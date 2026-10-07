#!/usr/bin/env python3
"""
Doorzoekt ALLE groepen (incl. subgroepen) en ALLE projecten op een GitLab-instantie
en bekijkt per project alleen de CI-configuratiefile (.gitlab-ci.yml, of het
afwijkende pad dat in de projectinstellingen staat) op een zoektekst.

Gebruik:
    export GITLAB_URL="https://gitlab.jouwbedrijf.nl"
    export GITLAB_PAT="glpat-xxxxxxxx"      # scope: read_api (en read_repository)
    python3 zoek_gitlab_ci.py
    python3 zoek_gitlab_ci.py --zoek "gitlab-ci-templates" --output resultaat.csv

Vereist: pip install requests
"""

import argparse
import csv
import os
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ZOEKTEKST_DEFAULT = "gitlab-ci-templates"
STANDAARD_CI_PAD = ".gitlab-ci.yml"


class GitLab:
    def __init__(self, url, token, verify_ssl=True):
        self.api = url.rstrip("/") + "/api/v4"
        self.sessie = requests.Session()
        self.sessie.headers.update({"PRIVATE-TOKEN": token})
        self.sessie.verify = verify_ssl

    def get(self, pad, params=None, raw=False):
        """GET met retry bij rate limiting (429) en tijdelijke serverfouten."""
        url = pad if pad.startswith("http") else self.api + pad
        for poging in range(6):
            r = self.sessie.get(url, params=params, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                wacht = int(r.headers.get("Retry-After", 2 ** poging))
                time.sleep(wacht)
                continue
            return r
        return r

    def paginate(self, pad, params=None):
        """Loopt alle pagina's af via de Link-header."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        url, eerste = pad, True
        while url:
            r = self.get(url, params=params if eerste else None)
            eerste = False
            if r.status_code != 200:
                print(f"[WAARSCHUWING] {url} gaf status {r.status_code}", file=sys.stderr)
                return
            yield from r.json()
            url = r.links.get("next", {}).get("url")


def verzamel_projecten(gl):
    """Alle projecten uit alle groepen + alle overige zichtbare projecten (bv. persoonlijke)."""
    projecten = {}

    print("Groepen ophalen...", file=sys.stderr)
    groepen = list(gl.paginate("/groups", {"all_available": "true"}))
    print(f"  {len(groepen)} groepen gevonden", file=sys.stderr)

    for i, groep in enumerate(groepen, 1):
        print(f"  [{i}/{len(groepen)}] projecten in groep {groep['full_path']}", file=sys.stderr)
        for p in gl.paginate(f"/groups/{groep['id']}/projects",
                             {"include_subgroups": "false", "with_shared": "false"}):
            projecten[p["id"]] = p

    # Vangnet: ook projecten die niet in een groep zitten (persoonlijke namespaces)
    print("Overige zichtbare projecten ophalen...", file=sys.stderr)
    for p in gl.paginate("/projects", {"order_by": "id", "sort": "asc"}):
        projecten.setdefault(p["id"], p)

    print(f"Totaal {len(projecten)} unieke projecten", file=sys.stderr)
    return list(projecten.values())


def ci_pad_voor(project):
    """Bepaalt welk CI-bestand we moeten lezen. Negeert externe paden (bv. file@groep/project)."""
    pad = (project.get("ci_config_path") or "").strip()
    if not pad or "@" in pad or pad.startswith("http"):
        return STANDAARD_CI_PAD
    return pad


def controleer_project(gl, project, zoektekst):
    naam = project["path_with_namespace"]
    branch = project.get("default_branch")
    if not branch or project.get("empty_repo"):
        return None
    if project.get("repository_access_level") == "disabled":
        return None

    ci_pad = ci_pad_voor(project)
    bestand = urllib.parse.quote(ci_pad, safe="")
    r = gl.get(f"/projects/{project['id']}/repository/files/{bestand}/raw",
               params={"ref": branch})
    if r.status_code != 200:
        return None  # geen CI-file of geen toegang

    regels = [
        (nr, regel.strip())
        for nr, regel in enumerate(r.text.splitlines(), 1)
        if zoektekst in regel
    ]
    if not regels:
        return None
    return {
        "project": naam,
        "branch": branch,
        "bestand": ci_pad,
        "regels": regels,
        "url": f"{project['web_url']}/-/blob/{branch}/{ci_pad}",
    }


def main():
    parser = argparse.ArgumentParser(description="Zoek tekst in de CI-file van alle GitLab-projecten")
    parser.add_argument("--zoek", default=ZOEKTEKST_DEFAULT, help="Tekst om naar te zoeken")
    parser.add_argument("--output", default="gitlab_ci_resultaat.csv", help="CSV-uitvoerbestand")
    parser.add_argument("--threads", type=int, default=8, help="Aantal parallelle requests")
    parser.add_argument("--no-verify-ssl", action="store_true", help="SSL-certificaat niet controleren")
    args = parser.parse_args()

    url = os.environ.get("GITLAB_URL")
    token = os.environ.get("GITLAB_PAT")
    if not url or not token:
        sys.exit("Zet eerst de omgevingsvariabelen GITLAB_URL en GITLAB_PAT.")

    gl = GitLab(url, token, verify_ssl=not args.no_verify_ssl)
    projecten = verzamel_projecten(gl)

    print(f"\nCI-files doorzoeken op '{args.zoek}'...", file=sys.stderr)
    treffers, klaar = [], 0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = {pool.submit(controleer_project, gl, p, args.zoek): p for p in projecten}
        for f in as_completed(futures):
            klaar += 1
            try:
                res = f.result()
            except Exception as e:
                print(f"[FOUT] {futures[f]['path_with_namespace']}: {e}", file=sys.stderr)
                continue
            if res:
                treffers.append(res)
                print(f"  GEVONDEN: {res['project']} ({res['bestand']})")
            if klaar % 100 == 0:
                print(f"  ...{klaar}/{len(projecten)} projecten gecontroleerd", file=sys.stderr)

    treffers.sort(key=lambda t: t["project"])
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["project", "branch", "bestand", "regelnummer", "regel", "url"])
        for t in treffers:
            for nr, regel in t["regels"]:
                w.writerow([t["project"], t["branch"], t["bestand"], nr, regel, t["url"]])

    print(f"\nKlaar: {len(treffers)} van {len(projecten)} projecten bevatten '{args.zoek}'.")
    print(f"Resultaat opgeslagen in {args.output}")


if __name__ == "__main__":
    main()