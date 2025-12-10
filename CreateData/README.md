# Create Data - Test File Generator

A Python utility to create test files of specific sizes for testing file upload validation, size restrictions, and file type handling.

## Overview

This tool generates test files with precise sizes in various formats including PDF, CSV, Excel (XLSX), and Word (DOCX). It's particularly useful for testing minimum/maximum file size restrictions in file upload components.

## Supported File Types

### Valid Files

- **PDF** (`.pdf`) - Generates PDF files with random text content
- **CSV** (`.csv`) - Generates CSV files with random tabular data
- **Excel** (`.xlsx`) - Generates Excel workbooks with random data rows
- **Word** (`.docx`) - Generates Word documents with random text paragraphs
- **ZIP** (`.zip`) - Generates ZIP archives with multiple text files

### Minimal/Corrupted Files (For Testing)

- **PDF Minimal** (`pdf-minimal`) - Creates corrupted PDF with only magic number header
- **Excel Minimal** (`xlsx-minimal`) - Creates corrupted XLSX with only ZIP magic number
- **Word Minimal** (`docx-minimal`) - Creates corrupted DOCX with only ZIP magic number

These minimal files pass magic number checks but are NOT valid files - useful for testing validation logic.

## Installation

Install the required dependencies:

```bash
pip install reportlab openpyxl python-docx
```

## Usage

### Basic Syntax

**For valid files:**

```bash
python create_data.py <file_extension> <size_in_mb>
```

**For minimal/corrupted files (testing only):**

```bash
python create_data.py <file_extension>-minimal <size_in_bytes>
```

**For ZIP archives:**

```bash
python create_data.py zip <size_in_mb> <num_files>
```

### Parameters

- `<file_extension>`: The type of file to create (`pdf`, `csv`, `xlsx`, `docx`, `zip`)
- `<size_in_mb>`: The target file size in megabytes (can be decimal values)
- `<size_in_bytes>`: For minimal files, the exact size in bytes (integer)
- `<num_files>`: For ZIP archives, the number of text files to include

### Examples

#### Testing Minimum File Size Restrictions

**Using Minimal/Corrupted Files (Recommended for Size Testing):**

These files pass the magic number check but are corrupted/invalid - perfect for testing size validation:

```bash
# PDF - Create file that passes magic number but fails size check
python create_data.py pdf-minimal 500      # 500 byte corrupted PDF (has %PDF- header)
python create_data.py pdf-minimal 100      # 100 byte corrupted PDF
python create_data.py pdf-minimal 50       # 50 byte corrupted PDF

# Excel - Create file that passes magic number but fails size check
python create_data.py xlsx-minimal 1000    # 1KB corrupted XLSX (has PK ZIP header)
python create_data.py xlsx-minimal 500     # 500 byte corrupted XLSX

# Word - Create file that passes magic number but fails size check
python create_data.py docx-minimal 512     # 512 byte corrupted DOCX (has PK ZIP header)
python create_data.py docx-minimal 100     # 100 byte corrupted DOCX

# CSV - Can create genuinely small valid files
python create_data.py csv 0.000001         # Tiny valid CSV
```

**Creating Valid Small Files (when possible):**

```bash
# CSV - minimum 5 bytes (can create genuinely small valid files)
python create_data.py csv 0.000001

# Note: PDF, Excel, and Word cannot create valid files smaller than their format overhead
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

#### Creating ZIP Archives

```bash
# Create a 10MB ZIP containing 100 text files
python create_data.py zip 10 100

# Create a 5MB ZIP containing 50 text files
python create_data.py zip 5 50

# Create a 100MB ZIP containing 1000 text files
python create_data.py zip 100 1000
```

## Output

Files are created in the `output` directory with descriptive names:

**Valid files:**

- `test_data_5MB.pdf`
- `test_data_10MB.csv`
- `test_data_2MB.xlsx`
- `test_data_3MB.docx`

**Minimal/corrupted files:**

- `test_data_minimal_500bytes.pdf`
- `test_data_minimal_1000bytes.xlsx`
- `test_data_minimal_512bytes.docx`

**ZIP archives:**

- `test_data_10MB_100files.zip`

## Testing File Upload Validation

### For Your Java Code

Based on your Java enum with minimum size requirements:

| File Type | Min Size (Bytes) | Valid File Command                   | Minimal File Command (Magic ✓, Size ✗)    |
| --------- | ---------------- | ------------------------------------ | ----------------------------------------- |
| PDF       | 100              | `python create_data.py pdf 0.0012`   | `python create_data.py pdf-minimal 50`    |
| CSV       | 5                | `python create_data.py csv 0.000001` | N/A (can create tiny valid CSVs)          |
| Excel     | 2000             | `python create_data.py xlsx 0.004`   | `python create_data.py xlsx-minimal 1000` |
| Word      | 1024             | `python create_data.py docx 0.003`   | `python create_data.py docx-minimal 500`  |

**Key:**

- **Valid File Command**: Creates smallest possible valid/complete file
- **Minimal File Command**: Creates corrupted file with only magic number - passes format detection but fails size check
- ✓ = Passes check, ✗ = Fails check

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

## Important Notes on Minimum File Sizes

### Format Overhead Limitations

**PDF, Excel, and Word files have significant format overhead that prevents creating VALID files below certain sizes:**

- **PDF files**: Minimum valid size ~1200 bytes (header, metadata, structure)
- **Excel (.xlsx) files**: Minimum valid size ~4000 bytes (XML structure, compression)
- **Word (.docx) files**: Minimum valid size ~3000 bytes (XML structure, compression)
- **CSV files**: Can be as small as 1 byte (minimal overhead)

### Testing Strategy with Minimal Files

**NEW: Use the `-minimal` flag to create corrupted files for testing!**

When you need to test files that:

- ✓ Pass magic number/format detection (e.g., starts with `%PDF-` or `PK`)
- ✗ Fail size validation (smaller than your minimum requirement)

Use the minimal file generators:

```bash
# Create a 100-byte corrupted PDF (has %PDF- header but is invalid)
python create_data.py pdf-minimal 100

# Create a 1000-byte corrupted Excel (has PK ZIP header but is invalid)
python create_data.py xlsx-minimal 1000

# Create a 500-byte corrupted Word doc (has PK ZIP header but is invalid)
python create_data.py docx-minimal 500
```

**These files will:**

- Pass magic number checks (file type detection by header)
- Be detected as the correct file type by tools like `file` command
- Fail to open in actual applications (they're corrupted)
- Be exactly the size you specify
- Perfect for testing that your validation checks BOTH format AND size

**Example scenario:** Your Java code requires PDFs ≥ 100 bytes. The smallest VALID PDF is ~1200 bytes, so you can't test a "too small valid PDF". Instead, create a 50-byte minimal PDF that passes format detection but fails the size check.

### General Notes

- The script will overwrite existing files with the same name
- Very small file sizes (< 1KB) may have higher variance due to file format overhead
- CSV files have minimal overhead and can achieve very precise small sizes

## Error Handling

The script will exit with an error if:

- Invalid file extension is provided
- Invalid size value is provided (negative or non-numeric)
- Target size cannot be achieved within tolerance after maximum iterations (PDF, Excel, Word only)

## License

This is a utility script for testing purposes.
