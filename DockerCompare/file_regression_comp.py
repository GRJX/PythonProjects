#!/usr/bin/env python3
"""
File regression comparison script.
Extracts all file contents from two local directories into a single unified diff file.

To copy files from a remote Docker container to local before running this script:

    # 1. Copy from container to the remote host's filesystem:
    ssh <ssh-host> "docker cp <container>:<container-path> /tmp/export/"

    # 2. Copy from remote host to your local machine:
    scp -r <ssh-host>:/tmp/export/ ./old/

    # 3. Clean up remote temp files:
    ssh <ssh-host> "rm -rf /tmp/export/"

    # Then run:
    python file_regression_comp.py ./old ./new

Usage:
    python file_regression_comp.py <old_dir> <new_dir> [options]

Options:
    --output FILE       Output diff file (default: diff.txt)
    --ext EXT           Only include files with this extension (can repeat)
                        e.g. --ext .docx --ext .csv
"""

import argparse
import csv
import sys
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Text extractors
# ---------------------------------------------------------------------------

def extract_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                import subprocess
                result = subprocess.run(
                    ["pandoc", "--to", "plain", str(path)],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            if "word/document.xml" not in zf.namelist():
                return "<no word/document.xml found>"
            return _xml_to_text(zf.read("word/document.xml"))
    except Exception as e:
        return f"<error reading docx: {e}>"


def _xml_to_text(xml_bytes: bytes) -> str:
    import re
    text = xml_bytes.decode("utf-8", errors="replace")
    paras = re.split(r'</w:p>', text)
    lines = []
    for para in paras:
        tokens = re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', para, re.DOTALL)
        line = "".join(tokens).strip()
        if line:
            lines.append(line)
    if lines:
        return "\n".join(lines)
    parts = re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', text, re.DOTALL)
    return "".join(parts)


def extract_xlsx(path: Path) -> str:
    try:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            out = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                out.append(f"=== Sheet: {sheet_name} ===")
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c) if c is not None else "" for c in row]
                    out.append("\t".join(cells))
            return "\n".join(out)
        except ImportError:
            pass

        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            shared = _xlsx_shared_strings(zf)
            out = []
            sheet_files = sorted(n for n in names if n.startswith("xl/worksheets/sheet"))
            for sf in sheet_files:
                out.append(f"=== {sf} ===")
                out.extend(_xlsx_parse_sheet(zf.read(sf), shared))
            return "\n".join(out)
    except Exception as e:
        return f"<error reading xlsx: {e}>"


def _xlsx_shared_strings(zf):
    import re
    try:
        xml = zf.read("xl/sharedStrings.xml").decode("utf-8", errors="replace")
        return re.findall(r'<t(?:\s[^>]*)?>(.*?)</t>', xml, re.DOTALL)
    except KeyError:
        return []


def _xlsx_parse_sheet(xml_bytes, shared):
    import re
    xml = xml_bytes.decode("utf-8", errors="replace")
    rows = re.split(r'<row\b', xml)[1:]
    result = []
    for row in rows:
        cells = re.findall(r'<c\b([^>]*)>(.*?)</c>', row, re.DOTALL)
        values = []
        for attrs, content in cells:
            t_match = re.search(r't="(\w)"', attrs)
            v_match = re.search(r'<v>(.*?)</v>', content, re.DOTALL)
            if v_match:
                v = v_match.group(1)
                if t_match and t_match.group(1) == "s":
                    idx = int(v)
                    v = shared[idx] if idx < len(shared) else v
                values.append(v)
            else:
                values.append("")
        if values:
            result.append("\t".join(values))
    return result


def extract_csv(path: Path) -> str:
    try:
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            return "\n".join("\t".join(row) for row in reader)
    except Exception as e:
        return f"<error reading csv: {e}>"


def extract_zip(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            lines = [f"=== ZIP contents of {path.name} ==="]
            for info in sorted(zf.infolist(), key=lambda x: x.filename):
                lines.append(f"{info.filename}\t{info.file_size} bytes")
            return "\n".join(lines)
    except Exception as e:
        return f"<error reading zip: {e}>"


EXTRACTORS = {
    ".docx": extract_docx,
    ".xlsx": extract_xlsx,
    ".csv":  extract_csv,
    ".zip":  extract_zip,
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

import re as _re
_RANDOM_TOKEN = _re.compile(r'_[A-Za-z]{4}_')


def _normalize(name: str) -> str:
    """Strip _xxxx_ random tokens from a filename stem for matching purposes."""
    stem = Path(name).stem
    suffix = Path(name).suffix
    parent = str(Path(name).parent)
    clean_stem = _RANDOM_TOKEN.sub("_", stem).strip("_")
    clean = clean_stem + suffix
    return clean if parent == "." else f"{parent}/{clean}"


def collect_files(root: Path, extensions: set) -> dict:
    """Return {relative_path_str: absolute_path} for all matching files."""
    result = {}
    if root.is_file():
        if root.suffix.lower() in extensions:
            result[root.name] = root
    else:
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in extensions:
                result[str(p.relative_to(root))] = p
    return result


def _match_files(old_files: dict, new_files: dict) -> list[tuple]:
    """
    Pair up files from old and new by normalized name.
    Returns list of (display_key, old_path_or_None, new_path_or_None).
    """
    old_norm = {_normalize(k): (k, v) for k, v in old_files.items()}
    new_norm = {_normalize(k): (k, v) for k, v in new_files.items()}

    all_norm_keys = sorted(set(old_norm) | set(new_norm))
    pairs = []
    for norm_key in all_norm_keys:
        old_entry = old_norm.get(norm_key)
        new_entry = new_norm.get(norm_key)
        # Use the new filename as display key if available, else old
        display = new_entry[0] if new_entry else old_entry[0]
        pairs.append((display, old_entry[1] if old_entry else None,
                      new_entry[1] if new_entry else None))
    return pairs


def write_diff(old_root: Path, new_root: Path, extensions: set, out_path: Path) -> None:
    import difflib

    old_files = collect_files(old_root, extensions)
    new_files = collect_files(new_root, extensions)
    pairs = _match_files(old_files, new_files)

    changed = identical = added = removed = 0

    with open(out_path, "w", encoding="utf-8") as f:
        for key, old_path, new_path in pairs:
            ext = Path(key).suffix.lower()
            extractor = EXTRACTORS.get(ext)
            if extractor is None:
                continue

            old_text = extractor(old_path) if old_path else ""
            new_text = extractor(new_path) if new_path else ""

            if old_path and not new_path:
                status = "REMOVED"
                removed += 1
            elif not old_path and new_path:
                status = "ADDED"
                added += 1
            elif old_text == new_text:
                identical += 1
                continue
            else:
                status = "CHANGED"
                changed += 1

            f.write(f"{'='*72}\n")
            f.write(f"{status}: {key}\n")
            f.write(f"{'='*72}\n")

            diff = difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"old/{old_path.name if old_path else key}",
                tofile=f"new/{new_path.name if new_path else key}",
                lineterm="",
            )
            f.write("\n".join(diff))
            f.write("\n\n")

        f.write(f"{'='*72}\n")
        f.write("SUMMARY\n")
        f.write(f"{'='*72}\n")
        f.write(f"  Added:     {added}\n")
        f.write(f"  Removed:   {removed}\n")
        f.write(f"  Changed:   {changed}\n")
        f.write(f"  Identical: {identical}\n")

    print(f"  ✓ diff written to {out_path}  "
          f"(+{added} added, -{removed} removed, ~{changed} changed, ={identical} identical)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Diff docx/xlsx/csv/zip files from two directories into a single diff file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("old", help="Path to the OLD (baseline) local directory")
    parser.add_argument("new", help="Path to the NEW (candidate) local directory")
    parser.add_argument("--output", "-o", default="diff.txt",
                        help="Output diff file (default: diff.txt)")
    parser.add_argument("--ext", action="append", dest="exts",
                        help="File extensions to include (default: all supported)")

    args = parser.parse_args()

    extensions = set(args.exts) if args.exts else set(EXTRACTORS.keys())
    extensions = {e if e.startswith(".") else f".{e}" for e in extensions}

    old_root = Path(args.old)
    new_root = Path(args.new)
    for p, label in [(old_root, "old"), (new_root, "new")]:
        if not p.exists():
            print(f"Error: {label} path does not exist: {p}", file=sys.stderr)
            sys.exit(1)

    write_diff(old_root, new_root, extensions, Path(args.output))


if __name__ == "__main__":
    main()
