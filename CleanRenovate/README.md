# Nexus Repository Cleaner

This script automates the process of cleaning up old Docker image tags from a Nexus repository. It uses Playwright to interact with the Nexus web UI.

## Prerequisites

*   Python 3.7+
*   Pip (Python package installer)
*   Access to a Nexus repository (dictus)

## Setup

1.  **Clone the repository:**

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```

4.  **Configure credentials:**
    Replace the `.env.local` to `.env` file in the project root directory and add your Nexus credentials:
    ```properties
    USERNAME=your_nexus_username
    PASSWORD=your_nexus_password
    BASE_URL=https://nexus.dictus.iesprd.ictu-sr.nl/
    ```
    Replace `your_nexus_username` and `your_nexus_password` with your actual credentials.

## Usage

Run the script from the command line:

```bash
python clean_renovate.py
```

The script will:
1.  Log in to the Nexus repository specified in the script.
2.  Navigate to the specified Docker repositories (e.g., `kwm/db`, `kwm/kwm-portal`, etc.).
3.  Extract all tags, excluding those specified (e.g., `latest`, `Parent Directory`).
4.  For each extracted tag, search for associated components in Nexus.
5.  Attempt to delete each found component associated with the tag.

## Configuration

*   **Nexus URL:** The base URL for the Nexus instance is hardcoded in the script (`https://nexus.dictus.iesprd.ictu-sr.nl/`). Modify this in `clean_renovate.py` if your instance is different.
*   **Repositories to Scan:** The list of repositories to fetch tags from is defined in the `if __name__ == "__main__":` block. Modify the list passed to `nexus.extract_tags([...])`.
*   **Excluded Tags:** Tags to ignore during extraction are defined in the `excluded_tags` parameter when calling `nexus.extract_tags`.
*   **Headless Mode:** By default, the script runs with the browser visible (`headless=False`). Change this to `headless=True` in the `Nexus()` instantiation for background execution.
*   **Selectors:** The script relies on specific CSS/XPath selectors to interact with the Nexus UI. These might change with Nexus updates and may need adjustment in the `Nexus` class methods.
