# DockerCompare

Regression diff tool for `.docx`, `.xlsx`, `.csv`, and `.zip` files.
Two scripts work together: one fetches files from a remote Docker container, the other compares them.

---

## Scripts

| Script | Purpose |
|---|---|
| `fetch_docker_files.py` | Copy files from a Docker container on a remote host to a local directory |
| `file_regression_comp.py` | Compare two local directories and write a single diff file |

---

## Typical workflow

### 1. Fetch files from the remote Docker container

```bash
python fetch_docker_files.py \
    --host my-server \
    --container my-app \
    --path /data/exports \
    --output-dir ./local_files
```

### 2. Generate a diff file

```bash
python file_regression_comp.py ./local_files/old ./local_files/new -o diff.txt
```

This produces a single `diff.txt` with all added, removed, and changed files in unified diff format, plus a summary at the end.

---

## fetch_docker_files.py

### Options

| Flag | Env variable | Description |
|---|---|---|
| `--host` | `FETCH_SSH_HOST` | SSH host alias or `user@host` |
| `--container` | `FETCH_CONTAINER` | Docker container name/ID |
| `--path` | `FETCH_PATH` | Path inside the container to copy |
| `--output-dir` | — | Local destination directory (default: `./comparison`) |
| `--keep-remote-tmp` | — | Keep the remote temp directory after copying |

CLI flags take precedence over environment variables.

### Using environment variables

```bash
export FETCH_SSH_HOST=my-server
export FETCH_CONTAINER=my-app
export FETCH_PATH=/data/exports

python fetch_docker_files.py --output-dir ./local_files
```

---

## file_regression_comp.py

### Options

| Flag | Description |
|---|---|
| `--output FILE` / `-o` | Output diff file (default: `diff.txt`) |
| `--ext EXT` | Only include files with this extension (repeatable) |

### Examples

Only CSV and XLSX files:
```bash
python file_regression_comp.py ./old ./new --ext .csv --ext .xlsx
```

---

## Requirements

- Python 3.10+
- SSH access to the remote host with `docker cp` permissions
- `openpyxl` (optional, for better XLSX support): `pip install openpyxl`
- `pandoc` (optional, for better DOCX support)
