# Create Data - Test File Generator

A Python utility to create test files of specific sizes for testing file upload validation, size restrictions, and file type handling.

## Overview

This tool generates test files with precise sizes in various formats including PDF, CSV, Excel (XLSX), and Word (DOCX). It's particularly useful for testing minimum/maximum file size restrictions in file upload components.

## Supported File Types

- **PDF** (`.pdf`) - Generates PDF files with random text content
- **CSV** (`.csv`) - Generates CSV files with random tabular data
- **Excel** (`.xlsx`) - Generates Excel workbooks with random data rows
- **Word** (`.docx`) - Generates Word documents with random text paragraphs

## Installation

Install the required dependencies:

```bash
pip install reportlab openpyxl python-docx
```

## Usage

### Basic Syntax

```bash
python create_data.py <file_extension> <size_in_mb>
```

### Parameters

- `<file_extension>`: The type of file to create (`pdf`, `csv`, `xlsx`, `docx`)
- `<size_in_mb>`: The target file size in megabytes (can be decimal values)

### Examples

#### Testing Minimum File Size Restrictions

Based on your Java code requirements, here are examples for testing files that are **too small**:

```bash
# PDF - minimum 100 bytes (create a file smaller than 100 bytes)
python create_data.py pdf 0.00005

# CSV - minimum 5 bytes (create a file smaller than 5 bytes)
python create_data.py csv 0.000001

# Excel - minimum 2000 bytes (create a file smaller than 2000 bytes)
python create_data.py xlsx 0.001

# Word - minimum 1024 bytes (create a file smaller than 1024 bytes)
python create_data.py docx 0.0005
```

#### Creating Standard Test Files

```bash
# Create a 5MB PDF file
python create_data.py pdf 5

# Create a 10MB CSV file
python create_data.py csv 10

# Create a 2MB Excel file
python create_data.py xlsx 2

# Create a 3MB Word document
python create_data.py docx 3
```

#### Creating Small Test Files

```bash
# Create a 50KB PDF
python create_data.py pdf 0.05

# Create a 100KB CSV
python create_data.py csv 0.1

# Create a 500KB Excel file
python create_data.py xlsx 0.5

# Create a 250KB Word document
python create_data.py docx 0.25
```

## Output

The script creates a file named `test_data_<size>MB.<extension>` in the current directory.

Example output filenames:

- `test_data_5MB.pdf`
- `test_data_0.00005MB.pdf`
- `test_data_10MB.csv`
- `test_data_2MB.xlsx`
- `test_data_3MB.docx`

## Testing File Upload Validation

### For Your Java Code

Based on your Java enum with minimum size requirements:

| File Type | Extension | Min Size (Bytes) | Test Command (Under Minimum)         |
| --------- | --------- | ---------------- | ------------------------------------ |
| PDF       | `.pdf`    | 100              | `python create_data.py pdf 0.00005`  |
| CSV       | `.csv`    | 5                | `python create_data.py csv 0.000001` |
| Excel     | `.xlsx`   | 2000             | `python create_data.py xlsx 0.001`   |
| Word      | `.docx`   | 1024             | `python create_data.py docx 0.0005`  |

### Conversion Reference

- 1 MB = 1,048,576 bytes
- 1 KB = 1,024 bytes
- To create a file of X bytes: `X / 1,048,576` MB

Examples:

- 100 bytes = 0.000095 MB ≈ `0.00005` MB
- 1024 bytes = 0.000977 MB ≈ `0.001` MB
- 2000 bytes = 0.001907 MB ≈ `0.002` MB

## How It Works

The script uses an iterative approach to achieve the target file size:

1. **PDF**: Uses ReportLab to generate pages with random text
2. **CSV**: Writes rows of random data until target size is reached
3. **Excel**: Creates workbooks with random data rows, adjusting row count iteratively
4. **Word**: Generates paragraphs of random text, adjusting content size iteratively

### Tolerance

- **PDF, Excel, Word**: ±400 KB tolerance (may iterate up to 15 times)
- **CSV**: ±100 KB tolerance (direct writing approach)

For very small files (< 1KB), the actual file size may vary slightly due to file format overhead.

## Notes

- The script will overwrite existing files with the same name
- Very small file sizes (< 0.001 MB) may have higher variance due to file format overhead
- Excel and Word files have significant format overhead, making very small files difficult to achieve precisely
- CSV files have minimal overhead and can achieve very precise small sizes

## Error Handling

The script will exit with an error if:

- Invalid file extension is provided
- Invalid size value is provided (negative or non-numeric)
- Target size cannot be achieved within tolerance after maximum iterations (PDF, Excel, Word only)

## License

This is a utility script for testing purposes.
