# Variable Cleaner

A Python utility for cleaning up and standardizing variables in the format `${variable_name}` across your project files.

## Features

- Scans files for variables in the format `${variable_name} value`
- Identifies variables that only occur once in the codebase (candidates for removal)
- Finds variables that occur multiple times but are not standardized to uppercase
- Interactive prompts for confirming removal or replacement actions
- Color-coded output for better readability

## Requirements

- Python 3.9 or higher
- Required packages: colorama, argparse

## Installation

```bash
pip install colorama
```

## Usage

```bash
python clean_variables.py <file_with_variables> <base_directory>
```
```bash
python clean_variables.py /Users/jelle/Documents/DICTU/repos/kwm/kwm-art/tests/Serie/objects/kwm_Algemeen.robot /Users/jelle/Documents/DICTU/repos/kwm/kwm-art
```

### Arguments

- `<file_with_variables>`: Path to the file containing variables in the format `${variable_name} value`
- `<base_directory>`: Base directory to search for variable occurrences in the project

### Example

```bash
python clean_variables.py ./config/variables.txt ./src
```

## How It Works

1. The script scans the specified file for variables in the format `${variable_name} value`
2. For each variable, it searches the base directory for occurrences
3. If a variable is found only once, it suggests removal (with confirmation)
4. If a variable is found multiple times and is not in uppercase, it suggests standardizing to uppercase (with confirmation)
5. You can either accept the suggested actions by pressing Enter or skip them

## Note

The script will show you where each variable is found before suggesting any changes. All changes require explicit confirmation before being applied.