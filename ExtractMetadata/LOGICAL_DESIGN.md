# Logical Design: Robust Media Metadata Processor

This document outlines the logical design for a script to process Google Photos Takeout archives. The architecture prioritizes correctness, completeness, and detailed reporting to ensure every media file is accounted for and processed reliably.

## 1. Guiding Principles

- **Correctness over Speed**: The design favors accurate metadata matching and verifiable file operations over raw performance. Every step is designed to be deliberate and auditable.
- **Completeness**: No media file from the source directory will be left behind. All files are either processed and moved based on metadata or are moved to a dedicated "unmatched" folder for manual review.
- **Idempotency**: Running the script multiple times on the same input and output directories will not cause errors or duplicate files. The script will intelligently skip files that are already correctly processed and in place.
- **Clear Reporting**: At the end of each run, the script must provide comprehensive statistics on successes and failures, and generate a log file to enable targeted re-processing of any failed items.
- **Two-Source Workflow**: Support for processing metadata from one source while finding media files in another source, enabling flexible multi-archive processing.

## 2. Command-Line Interface

The script is controlled via command-line arguments using the `argparse` library.

- `input_directory`: (Required) The source directory containing the Google Photos Takeout files.
- `output_directory`: (Required) The destination directory where processed files will be moved.
- `--skipped`: (Optional) Path to a `skipped_files_...json` log from a previous run. When provided, the script will only attempt to process the JSON files listed in this log, looking for their corresponding media files in the current input directory.
- `--rm`: (Optional) If specified, the script will remove original source files after successful processing. In skipped mode, only removes JSON files from the skipped log and matched media files from the current input directory.

## 3. Core Architecture and Execution Flow

The script operates in four distinct phases to ensure a methodical and verifiable process.

### Phase 1: Initialization and Indexing

1.  **Argument Parsing**: The script starts by parsing and validating the command-line arguments.
2.  **Directory Setup**: It verifies that the `input_directory` exists and creates the `output_directory` if it does not already exist.
3.  **File Indexing**: The script performs a single, comprehensive walk of the `input_directory` to build two in-memory indexes:
    - `media_file_index`: A dictionary mapping every non-JSON filename to its full absolute path. This represents the complete set of media files to be processed.
    - `json_file_index`: A dictionary mapping every `.json` filename to its full absolute path.
4.  **Run Mode Determination**:
    - **Standard Run**: If the `--skipped` flag is not used, the set of JSON files to process is the entire `json_file_index`.
    - **Skipped Run**: If the `--skipped` flag is used, the script reads the specified log file and attempts to locate the original JSON files from the skipped log. Only JSON files that exist and can be found are processed, looking for their media files in the current input directory.

### Phase 2: Two-Phase Metadata-Driven Processing

This phase uses a sophisticated two-phase approach to ensure optimal matching and prevent conflicts where multiple JSON files might match the same media file.

#### Phase 2a: Exact Filename Matching

1.  **Exact Match Discovery**: The script first iterates through all target JSON files to identify exact filename matches.
2.  **Metadata Extraction**: For each JSON file, it extracts the `title` and `photoTakenTime` values.
3.  **Exact Matching Logic**:
    - The base name is extracted from the `title` by removing any file extension.
    - The script searches for media files where the filename (without extension) exactly matches the title base name (case-insensitive).
    - All exact matches are collected and marked for processing.
4.  **Processing Exact Matches**: All exact matches are processed immediately, and the matched media files are added to an exclusion set for the pattern matching phase.

#### Phase 2b: Pattern Matching for Remaining Files

1.  **Pattern Generation**: For JSON files that didn't find exact matches, a regex pattern is generated:
    - The base name is extracted from the `title` and truncated to 46 characters.
    - A regular expression is constructed to match from the start of the filename (e.g., `^IMG_1234.*`).
2.  **Pattern Matching**: The script searches the `media_file_index` using the regex pattern, excluding files already matched in Phase 2a.
3.  **Processing Pattern Matches**: Matched files are processed using the same logic as exact matches.

#### Common Processing Logic for Both Phases

For each matched media file:

- It is added to an `accounted_for_media` set to track it for the reconciliation phase.
- The destination path is determined, preserving the relative folder structure from the source.
- **Idempotency Check**: The script checks if a file with the same name and correct modification time already exists at the destination. If so, it is skipped.
- **Collision Handling**: If a file with the same name exists at the destination but has a different timestamp, a numeric suffix (e.g., `_1`, `_2`) is appended to the new file's name before copying.
- The file is copied to the destination, and its modification time is set using the `photoTakenTime` from the JSON data.
- The result (success or failure) is logged for the final report.

#### Cleanup Logic

**Standard Mode**: If the `--rm` flag is active and all media files associated with the current JSON were processed without error, both the original source media files and the source JSON file are removed.

**Skipped Mode**: If the `--rm` flag is active:

- Media files from the current input directory (source 2) are removed after successful processing.
- JSON files are only removed if they exist in the original skipped log paths (source 1).

### Phase 3: Reconciliation of Unmatched Media

This phase fulfills the "completeness" principle by ensuring that media files without any corresponding JSON metadata are not left behind.

**Note**: This phase is **skipped entirely** when running in skipped mode, as the purpose is to find matches for specific JSON files rather than to handle all media files.

1.  **Identify Unmatched Files**: The script compares the initial `media_file_index` against the `accounted_for_media` set. Any file in the index but not in the set is considered unmatched.
2.  **Move Unmatched Files**:
    - A dedicated subdirectory is created: `output_directory/unmatched/`.
    - Each unmatched media file is moved from its source location to the `unmatched` directory. Its original modification time is preserved.

### Phase 4: Finalization and Reporting

1.  **Generate Statistics**: The script compiles the logs from the previous phases to calculate final statistics.

#### Standard Mode Statistics:

- Total JSON files processed.
- Number of JSON files that successfully matched at least one media file.
- Number of JSON files that failed (e.g., missing metadata, no matches found).
- Total media files found in the source directory.
- Number of media files successfully copied and timestamped.
- Number of media files moved to the `unmatched` directory.
- Total number of individual file copy or timestamp errors.
- Completeness verification showing all files accounted for.

#### Skipped Mode Statistics:

- Number of JSON files from the skipped log.
- Number of JSON files found and processed in current run.
- Number of media files matched and copied.
- Success/failure status for the skipped file processing.

2.  **Display Summary**: A structured summary of these statistics is printed to the console, giving the user a clear overview of the run's outcome.
3.  **Create Skipped Log**: If any failures were recorded (for a JSON file or an individual media file), their details are written to a new, timestamped `skipped_files_...json` log file in the `output_directory`. This file can be used for a subsequent run with the `--skipped` flag to retry only the failed items.

## 4. Two-Source Workflow

The skipped mode enables a powerful two-source workflow:

1. **First Run (Source 1)**: Process a Google Photos Takeout archive in standard mode. Some JSON files may fail to find matching media files, generating a skipped files log.

2. **Second Run (Source 2)**: Use the `--skipped` flag with a different input directory containing additional media files. The script will:
   - Load the JSON file paths from the skipped log
   - Look for those specific JSON files in their original locations
   - Search for matching media files in the new input directory (Source 2)
   - Only process the specific JSON-media pairs that can be matched
   - Skip the unmatched media reconciliation phase entirely

This workflow is particularly useful when Google Photos archives are split across multiple takeout files or when media files and metadata become separated across different directory structures.
