#!/usr/bin/env python3
"""
Fetch files from a Docker container on a remote SSH host to a local directory.

Usage:
    python fetch_docker_files.py \\
        --host <ssh-host> \\
        --container <container> \\
        --path /data/exports \\
        --output-dir ./local_files

Environment variables (alternative to CLI flags):
    FETCH_SSH_HOST      SSH host alias from ~/.ssh/config
    FETCH_CONTAINER     Docker container name/ID
    FETCH_PATH          Path inside the container

CLI flags take precedence over environment variables.

Options:
    --host HOST         SSH host alias or user@host
    --container NAME    Docker container name/ID
    --path PATH         Path inside the container to copy
    --output-dir DIR    Local destination directory (default: ./comparison)
    --keep-remote-tmp   Do not clean up the temp dir on the remote host
"""

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------

def _run(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  [cmd] {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _ssh(host: str, command: str, check: bool = True) -> subprocess.CompletedProcess:
    return _run(["ssh", host, command], check=check)


# ---------------------------------------------------------------------------
# Fetch logic
# ---------------------------------------------------------------------------

def fetch_from_container(
    ssh_host: str,
    container: str,
    container_path: str,
    local_dest: Path,
    keep_remote_tmp: bool = False,
) -> None:
    """
    Copy a file or directory from a remote Docker container to a local directory.

    Steps:
      1. ssh <host>  →  docker cp <container>:<path> /tmp/<uuid>/
      2. scp -r <host>:/tmp/<uuid>/ <local_dest>/
      3. ssh <host>  →  rm -rf /tmp/<uuid>/   (unless --keep-remote-tmp)
    """
    remote_tmp = f"/tmp/fetch_{uuid.uuid4().hex}"

    print(f"\n→ Fetching  {container}:{container_path}  from {ssh_host}", file=sys.stderr)

    try:
        _ssh(ssh_host,
             f"mkdir -p {remote_tmp} && docker cp {container}:{container_path} {remote_tmp}/")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"docker cp failed on {ssh_host} for container '{container}', "
            f"path '{container_path}':\n{e.stderr}"
        ) from e

    local_dest.mkdir(parents=True, exist_ok=True)
    try:
        _run(["scp", "-r", f"{ssh_host}:{remote_tmp}/.", str(local_dest)])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"scp failed:\n{e.stderr}") from e
    finally:
        if not keep_remote_tmp:
            _ssh(ssh_host, f"rm -rf {remote_tmp}", check=False)
        else:
            print(f"  Remote temp kept at: {remote_tmp}", file=sys.stderr)

    print(f"  ✓ Saved to {local_dest}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch files from a Docker container on a remote SSH host.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--host",
                        default=os.environ.get("FETCH_SSH_HOST"),
                        help="SSH host alias or user@host (env: FETCH_SSH_HOST)")
    parser.add_argument("--container",
                        default=os.environ.get("FETCH_CONTAINER"),
                        help="Docker container name/ID (env: FETCH_CONTAINER)")
    parser.add_argument("--path",
                        default=os.environ.get("FETCH_PATH"),
                        help="Path inside the container (env: FETCH_PATH)")
    parser.add_argument("--output-dir", "-d", default="./comparison",
                        help="Local destination directory (default: ./comparison)")
    parser.add_argument("--keep-remote-tmp", action="store_true",
                        help="Do not delete the temp dir on the remote host after copying")

    args = parser.parse_args()

    missing = [name for name, val in [
        ("--host", args.host),
        ("--container", args.container),
        ("--path", args.path),
    ] if not val]

    if missing:
        print(
            "Error: the following arguments are required:\n"
            + "\n".join(f"  {m}" for m in missing),
            file=sys.stderr,
        )
        sys.exit(1)

    local_dest = Path(args.output_dir)

    print(f"\nSSH host:   {args.host}", file=sys.stderr)
    print(f"Container:  {args.container}", file=sys.stderr)
    print(f"Path:       {args.path}", file=sys.stderr)
    print(f"Output dir: {local_dest.resolve()}\n", file=sys.stderr)

    try:
        fetch_from_container(
            args.host, args.container, args.path,
            local_dest, args.keep_remote_tmp,
        )
    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
