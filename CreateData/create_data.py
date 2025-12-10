import sys
import os
import random
import string
import csv
import zipfile
import tempfile

# Import optional dependencies only when needed
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Pt
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

def generate_random_text(size):
    """Generates a block of random text of a given size."""
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + ' ', k=size))

def create_minimal_pdf(file_path, size_bytes):
    """
    Creates a minimal PDF file that passes magic number check but is smaller than normal PDF minimum.
    This creates an INVALID/CORRUPTED PDF that only has the header - useful for testing validation.
    """
    target_size = size_bytes
    
    if target_size < 5:
        print(f"Error: Cannot create PDF smaller than 5 bytes (minimum for '%PDF-' header)")
        sys.exit(1)
    
    print(f"Creating minimal PDF '{file_path}' of {size_bytes} bytes.")
    print("WARNING: This will be a CORRUPTED/INVALID PDF that only passes magic number check!")
    
    # PDF magic number header
    pdf_header = b'%PDF-1.4\n'
    
    with open(file_path, 'wb') as f:
        if target_size <= len(pdf_header):
            # Write only partial header to reach exact size
            f.write(pdf_header[:target_size])
        else:
            # Write full header + padding to reach target size
            f.write(pdf_header)
            remaining = target_size - len(pdf_header)
            # Add random comment lines (comments in PDF start with %)
            padding = b'%' + os.urandom(remaining - 1)
            f.write(padding)
    
    actual_size = os.path.getsize(file_path)
    print(f"Successfully created '{file_path}'.")
    print(f"File size: {actual_size} bytes")
    print(f"Magic number: {open(file_path, 'rb').read(5)}")
    print(f"This file passes magic number check but is NOT a valid PDF!")

def create_minimal_xlsx(file_path, size_bytes):
    """
    Creates a minimal Excel file that passes magic number check but is smaller than normal XLSX minimum.
    This creates an INVALID/CORRUPTED XLSX - useful for testing validation.
    """
    target_size = size_bytes
    
    if target_size < 4:
        print(f"Error: Cannot create XLSX smaller than 4 bytes (minimum for ZIP magic number)")
        sys.exit(1)
    
    print(f"Creating minimal XLSX '{file_path}' of {size_bytes} bytes.")
    print("WARNING: This will be a CORRUPTED/INVALID XLSX that only passes magic number check!")
    
    # XLSX files are ZIP archives, so they start with ZIP magic number
    zip_header = b'PK\x03\x04'
    
    with open(file_path, 'wb') as f:
        if target_size <= len(zip_header):
            f.write(zip_header[:target_size])
        else:
            f.write(zip_header)
            remaining = target_size - len(zip_header)
            # Add random padding
            f.write(os.urandom(remaining))
    
    actual_size = os.path.getsize(file_path)
    print(f"Successfully created '{file_path}'.")
    print(f"File size: {actual_size} bytes")
    print(f"Magic number: {open(file_path, 'rb').read(4)}")
    print(f"This file passes magic number check but is NOT a valid XLSX!")

def create_minimal_docx(file_path, size_bytes):
    """
    Creates a minimal Word file that passes magic number check but is smaller than normal DOCX minimum.
    This creates an INVALID/CORRUPTED DOCX - useful for testing validation.
    """
    target_size = size_bytes
    
    if target_size < 4:
        print(f"Error: Cannot create DOCX smaller than 4 bytes (minimum for ZIP magic number)")
        sys.exit(1)
    
    print(f"Creating minimal DOCX '{file_path}' of {size_bytes} bytes.")
    print("WARNING: This will be a CORRUPTED/INVALID DOCX that only passes magic number check!")
    
    # DOCX files are ZIP archives, so they start with ZIP magic number
    zip_header = b'PK\x03\x04'
    
    with open(file_path, 'wb') as f:
        if target_size <= len(zip_header):
            f.write(zip_header[:target_size])
        else:
            f.write(zip_header)
            remaining = target_size - len(zip_header)
            # Add random padding
            f.write(os.urandom(remaining))
    
    actual_size = os.path.getsize(file_path)
    print(f"Successfully created '{file_path}'.")
    print(f"File size: {actual_size} bytes")
    print(f"Magic number: {open(file_path, 'rb').read(4)}")
    print(f"This file passes magic number check but is NOT a valid DOCX!")

def create_pdf(file_path, size_mb):
    """
    Creates a PDF file of a specific size in MB using an iterative approach.
    """
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab is required for PDF generation. Install with: pip install reportlab")
        sys.exit(1)
    
    target_size_bytes = size_mb * 1024 * 1024
    tolerance_bytes = 400 * 1024  # 400 KB
    max_iterations = 15

    print(f"Attempting to create '{file_path}' of size {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")

    # Start with an estimate. PDF overhead is significant, so content is a fraction of file size.
    # Let's assume content is about 85% of the file size. This is a heuristic.
    estimated_chars = int(target_size_bytes * 0.85)
    
    for i in range(max_iterations):
        print(f"Iteration {i+1}/{max_iterations}, using {estimated_chars:,.0f} characters.")
        
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        text = generate_random_text(estimated_chars)
        
        chars_per_line = 100
        lines = [text[i:i+chars_per_line] for i in range(0, len(text), chars_per_line)]

        y_position = height - 40
        for line in lines:
            c.drawString(40, y_position, line)
            y_position -= 12
            if y_position < 40:
                c.showPage()
                y_position = height - 40
                
        c.save()

        current_size_bytes = os.path.getsize(file_path)
        size_diff = current_size_bytes - target_size_bytes

        print(f"  -> Current size: {current_size_bytes / (1024*1024):.2f} MB, Difference: {size_diff / 1024:,.2f} KB")

        if abs(size_diff) <= tolerance_bytes:
            break # Success

        # Adjust for next iteration
        # If we have a file, we can make a better guess about the ratio
        if current_size_bytes > 0:
            # Proportional adjustment
            estimated_chars = int((estimated_chars / current_size_bytes) * target_size_bytes)
        else: # Should not happen after first iteration
            estimated_chars = int(estimated_chars * 0.9) # Reduce if file is empty

    # Final check after loop
    current_size_bytes = os.path.getsize(file_path)
    size_diff = current_size_bytes - target_size_bytes

    if abs(size_diff) > tolerance_bytes:
        print(f"Error: Could not generate file within tolerance after {max_iterations} iterations.")
        print(f"Final file size deviation ({current_size_bytes / 1024:,.0f} KB) is more than the tolerance ({tolerance_bytes / 1024:,.0f} KB).")
        os.remove(file_path)
        sys.exit(1)
    
    print(f"\nSuccessfully created '{file_path}'.")
    print(f"Final size: {current_size_bytes / (1024*1024):.2f} MB ({current_size_bytes:,.0f} bytes).")
    print(f"Target size:  {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    print(f"Difference:   {size_diff / 1024:,.2f} KB.")


def create_csv(file_path, size_mb):
    """
    Creates a CSV file of a specific size in MB.
    """
    target_size_bytes = size_mb * 1024 * 1024
    tolerance_bytes = 100 * 1024  # 100 KB
    
    print(f"Attempting to create '{file_path}' of size {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['ID', 'Name', 'Email', 'Address', 'Phone', 'Data'])
        
        row_count = 0
        while True:
            current_size = os.path.getsize(file_path)
            if current_size >= target_size_bytes - tolerance_bytes:
                break
            
            # Generate random row data
            row = [
                row_count,
                ''.join(random.choices(string.ascii_letters, k=20)),
                f"user{row_count}@example.com",
                ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=50)),
                ''.join(random.choices(string.digits, k=10)),
                ''.join(random.choices(string.ascii_letters + string.digits, k=100))
            ]
            writer.writerow(row)
            row_count += 1
            
            # Check every 100 rows
            if row_count % 100 == 0:
                csvfile.flush()
    
    current_size_bytes = os.path.getsize(file_path)
    size_diff = current_size_bytes - target_size_bytes
    
    print(f"\nSuccessfully created '{file_path}'.")
    print(f"Final size: {current_size_bytes / (1024*1024):.2f} MB ({current_size_bytes:,.0f} bytes).")
    print(f"Target size:  {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    print(f"Difference:   {size_diff / 1024:,.2f} KB.")


def create_excel(file_path, size_mb):
    """
    Creates an Excel (.xlsx) file of a specific size in MB using an iterative approach.
    """
    if not OPENPYXL_AVAILABLE:
        print("Error: openpyxl is required for Excel generation. Install with: pip install openpyxl")
        sys.exit(1)
    
    target_size_bytes = size_mb * 1024 * 1024
    tolerance_bytes = 400 * 1024  # 400 KB
    max_iterations = 15
    
    print(f"Attempting to create '{file_path}' of size {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    
    # Start with an estimate
    estimated_rows = int(target_size_bytes / 200)  # Rough estimate
    
    for i in range(max_iterations):
        print(f"Iteration {i+1}/{max_iterations}, using {estimated_rows:,.0f} rows.")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Data"
        
        # Write header
        ws.append(['ID', 'Name', 'Email', 'Address', 'Phone', 'Data', 'Notes', 'Status'])
        
        # Write data rows
        for row_num in range(estimated_rows):
            ws.append([
                row_num,
                ''.join(random.choices(string.ascii_letters, k=20)),
                f"user{row_num}@example.com",
                ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=50)),
                ''.join(random.choices(string.digits, k=10)),
                ''.join(random.choices(string.ascii_letters + string.digits, k=100)),
                ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=80)),
                random.choice(['Active', 'Inactive', 'Pending', 'Completed'])
            ])
        
        wb.save(file_path)
        
        current_size_bytes = os.path.getsize(file_path)
        size_diff = current_size_bytes - target_size_bytes
        
        print(f"  -> Current size: {current_size_bytes / (1024*1024):.2f} MB, Difference: {size_diff / 1024:,.2f} KB")
        
        if abs(size_diff) <= tolerance_bytes:
            break
        
        # Adjust for next iteration
        if current_size_bytes > 0:
            estimated_rows = int((estimated_rows / current_size_bytes) * target_size_bytes)
        else:
            estimated_rows = int(estimated_rows * 0.9)
    
    current_size_bytes = os.path.getsize(file_path)
    size_diff = current_size_bytes - target_size_bytes
    
    if abs(size_diff) > tolerance_bytes:
        print(f"Warning: File size deviation ({current_size_bytes / 1024:,.0f} KB) exceeds tolerance ({tolerance_bytes / 1024:,.0f} KB).")
    
    print(f"\nSuccessfully created '{file_path}'.")
    print(f"Final size: {current_size_bytes / (1024*1024):.2f} MB ({current_size_bytes:,.0f} bytes).")
    print(f"Target size:  {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    print(f"Difference:   {size_diff / 1024:,.2f} KB.")


def create_docx(file_path, size_mb):
    """
    Creates a Word (.docx) file of a specific size in MB using an iterative approach.
    """
    if not PYTHON_DOCX_AVAILABLE:
        print("Error: python-docx is required for Word document generation. Install with: pip install python-docx")
        sys.exit(1)
    
    target_size_bytes = size_mb * 1024 * 1024
    tolerance_bytes = 400 * 1024  # 400 KB
    max_iterations = 15
    
    print(f"Attempting to create '{file_path}' of size {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    
    # Start with an estimate
    estimated_chars = int(target_size_bytes * 0.70)  # Heuristic
    
    for i in range(max_iterations):
        print(f"Iteration {i+1}/{max_iterations}, using {estimated_chars:,.0f} characters.")
        
        doc = Document()
        
        # Add title
        doc.add_heading('Test Document', 0)
        
        # Generate random text
        text = generate_random_text(estimated_chars)
        
        # Split into paragraphs (roughly 500 chars each)
        paragraph_size = 500
        paragraphs = [text[i:i+paragraph_size] for i in range(0, len(text), paragraph_size)]
        
        for para_text in paragraphs:
            p = doc.add_paragraph(para_text)
            p.style.font.size = Pt(11)
        
        doc.save(file_path)
        
        current_size_bytes = os.path.getsize(file_path)
        size_diff = current_size_bytes - target_size_bytes
        
        print(f"  -> Current size: {current_size_bytes / (1024*1024):.2f} MB, Difference: {size_diff / 1024:,.2f} KB")
        
        if abs(size_diff) <= tolerance_bytes:
            break
        
        # Adjust for next iteration
        if current_size_bytes > 0:
            estimated_chars = int((estimated_chars / current_size_bytes) * target_size_bytes)
        else:
            estimated_chars = int(estimated_chars * 0.9)
    
    current_size_bytes = os.path.getsize(file_path)
    size_diff = current_size_bytes - target_size_bytes
    
    if abs(size_diff) > tolerance_bytes:
        print(f"Warning: File size deviation ({current_size_bytes / 1024:,.0f} KB) exceeds tolerance ({tolerance_bytes / 1024:,.0f} KB).")
    
    print(f"\nSuccessfully created '{file_path}'.")
    print(f"Final size: {current_size_bytes / (1024*1024):.2f} MB ({current_size_bytes:,.0f} bytes).")
    print(f"Target size:  {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    print(f"Difference:   {size_diff / 1024:,.2f} KB.")


def create_zip(file_path, num_files, size_mb):
    """
    Creates a ZIP file containing a specified number of text files with a target final size in MB.
    """
    target_size_bytes = size_mb * 1024 * 1024
    tolerance_bytes = 100 * 1024  # 100 KB
    max_iterations = 15
    
    print(f"Attempting to create '{file_path}' with {num_files} files of size {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    
    # Start with an estimate - text compresses roughly 3:1, but this varies
    estimated_chars_per_file = int((target_size_bytes * 2.5) / num_files)
    
    for iteration in range(max_iterations):
        print(f"Iteration {iteration+1}/{max_iterations}, using {estimated_chars_per_file:,.0f} characters per file.")
        
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create text files
            for i in range(num_files):
                temp_file = os.path.join(temp_dir, f"file_{i+1:04d}.txt")
                with open(temp_file, 'w') as f:
                    text = generate_random_text(estimated_chars_per_file)
                    f.write(text)
            
            # Create zip file
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i in range(num_files):
                    temp_file = os.path.join(temp_dir, f"file_{i+1:04d}.txt")
                    zipf.write(temp_file, f"file_{i+1:04d}.txt")
        
        current_size_bytes = os.path.getsize(file_path)
        size_diff = current_size_bytes - target_size_bytes
        
        print(f"  -> Current size: {current_size_bytes / (1024*1024):.2f} MB, Difference: {size_diff / 1024:,.2f} KB")
        
        if abs(size_diff) <= tolerance_bytes:
            break
        
        # Adjust for next iteration
        if current_size_bytes > 0:
            estimated_chars_per_file = int((estimated_chars_per_file / current_size_bytes) * target_size_bytes)
        else:
            estimated_chars_per_file = int(estimated_chars_per_file * 0.9)
    
    current_size_bytes = os.path.getsize(file_path)
    size_diff = current_size_bytes - target_size_bytes
    
    if abs(size_diff) > tolerance_bytes:
        print(f"Warning: File size deviation ({current_size_bytes / 1024:,.0f} KB) exceeds tolerance ({tolerance_bytes / 1024:,.0f} KB).")
    
    print(f"\nSuccessfully created '{file_path}' containing {num_files} files.")
    print(f"Final size: {current_size_bytes / (1024*1024):.2f} MB ({current_size_bytes:,.0f} bytes).")
    print(f"Target size:  {size_mb:.2f} MB ({target_size_bytes:,.0f} bytes).")
    print(f"Difference:   {size_diff / 1024:,.2f} KB.")


def main():
    """Main function to handle command-line arguments."""
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    if len(sys.argv) < 3:
        print("Usage: python create_data.py <file_extension> <size_in_mb> [num_files]")
        print("Supported extensions: pdf, csv, xlsx, docx, zip")
        print("\nFor minimal/corrupted files (magic number only):")
        print("  python create_data.py <file_extension>-minimal <size_in_bytes>")
        print("  Example: python create_data.py pdf-minimal 500  (creates 500 byte corrupted PDF)")
        print("\nFor zip files:")
        print("  python create_data.py zip <size_in_mb> <num_files>")
        print("  Example: python create_data.py zip 10 100  (creates 10MB zip with 100 files)")
        sys.exit(1)

    ext = sys.argv[1].lower()
    
    # Handle minimal/corrupted files (for testing magic number vs size validation)
    if ext.endswith('-minimal'):
        base_ext = ext.replace('-minimal', '')
        if base_ext not in ['pdf', 'xlsx', 'docx']:
            print(f"Error: Minimal format only supported for pdf, xlsx, docx")
            sys.exit(1)
        
        try:
            size_bytes = int(sys.argv[2])
            if size_bytes <= 0:
                raise ValueError("Size must be positive.")
        except ValueError as e:
            print(f"Error: Invalid size '{sys.argv[2]}'. Please provide a positive integer (bytes). Details: {e}")
            sys.exit(1)
        
        file_name = os.path.join(output_dir, f"test_data_minimal_{size_bytes}bytes.{base_ext}")
        
        if base_ext == 'pdf':
            create_minimal_pdf(file_name, size_bytes)
        elif base_ext == 'xlsx':
            create_minimal_xlsx(file_name, size_bytes)
        elif base_ext == 'docx':
            create_minimal_docx(file_name, size_bytes)
        return
    
    # Handle zip format specially (requires num_files parameter)
    if ext == 'zip':
        if len(sys.argv) != 4:
            print("Error: ZIP format requires 3 arguments: zip <size_in_mb> <num_files>")
            print("Example: python create_data.py zip 10 100")
            sys.exit(1)
        
        try:
            size_mb = float(sys.argv[2])
            if size_mb <= 0:
                raise ValueError("Size must be positive.")
            num_files = int(sys.argv[3])
            if num_files <= 0:
                raise ValueError("Number of files must be positive.")
        except ValueError as e:
            print(f"Error: Invalid arguments. Details: {e}")
            sys.exit(1)
        
        file_name = os.path.join(output_dir, f"test_data_{size_mb}MB_{num_files}files.zip")
        create_zip(file_name, num_files, size_mb)
        return
    
    # Handle other formats
    if len(sys.argv) < 3:
        print("Usage: python create_data.py <file_extension> <size_in_mb>")
        print("Supported extensions: pdf, csv, xlsx, docx, zip")
        sys.exit(1)
    
    try:
        size_mb = float(sys.argv[2])
        if size_mb <= 0:
            raise ValueError("Size must be positive.")
    except ValueError as e:
        print(f"Error: Invalid size '{sys.argv[2]}'. Please provide a positive number. Details: {e}")
        sys.exit(1)

    file_name = os.path.join(output_dir, f"test_data_{size_mb}MB.{ext}")

    if ext == 'pdf':
        create_pdf(file_name, size_mb)
    elif ext == 'csv':
        create_csv(file_name, size_mb)
    elif ext in ['xlsx', 'excel']:
        if ext == 'excel':
            file_name = os.path.join(output_dir, f"test_data_{size_mb}MB.xlsx")
        create_excel(file_name, size_mb)
    elif ext in ['docx', 'doc']:
        if ext == 'doc':
            file_name = os.path.join(output_dir, f"test_data_{size_mb}MB.docx")
        create_docx(file_name, size_mb)
    else:
        print(f"Error: Unsupported file extension '{ext}'.")
        print("Supported extensions: pdf, csv, xlsx (or excel), docx (or doc), zip")
        print("For minimal/corrupted files: pdf-minimal, xlsx-minimal, docx-minimal")
        sys.exit(1)

if __name__ == "__main__":
    # Before running, make sure you have the required packages installed:
    # pip install reportlab openpyxl python-docx
    #
    # Usage:
    #   Valid files:    python create_data.py pdf 5
    #   Minimal files:  python create_data.py pdf-minimal 100
    #   ZIP archives:   python create_data.py zip 10 100
    main()
