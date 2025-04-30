from PyPDF2 import PdfReader, PdfWriter
import os
from reportlab.pdfgen import canvas
from io import BytesIO


def compress_and_split_pdf(input_file, output_folder, max_size_mb=9):
    max_size_bytes = max_size_mb * 1024 * 1024

    # Read the PDF
    reader = PdfReader(input_file)
    writer = PdfWriter()

    # Step 1: Compress and check size
    for page in reader.pages:
        writer.add_page(page)

    temp_file = os.path.join(output_folder, "temp_compressed.pdf")
    with open(temp_file, "wb") as temp_pdf:
        writer.write(temp_pdf)

    if os.path.getsize(temp_file) <= max_size_bytes:
        os.rename(temp_file, os.path.join(output_folder, "compressed_output.pdf"))
        print(f"Compressed PDF saved as 'compressed_output.pdf' within the size limit.")
        return

    # Step 2: Split if still too large
    print("Compressed PDF exceeds size limit. Splitting into multiple files...")
    os.remove(temp_file)

    writer = PdfWriter()  # Reset writer for splitting
    part_number = 1
    current_size = 0

    for page_number, page in enumerate(reader.pages):
        writer.add_page(page)
        temp_file = BytesIO()
        writer.write(temp_file)

        current_size = temp_file.tell()
        if current_size > max_size_bytes or page_number == len(reader.pages) - 1:
            part_file_name = os.path.join(output_folder, f"output_part_{part_number}.pdf")
            with open(part_file_name, "wb") as part_file:
                writer.write(part_file)
            print(f"Part {part_number} saved as '{part_file_name}'.")

            part_number += 1
            writer = PdfWriter()

if __name__ == "__main__":
    input_pdf_path = "/Users/jelle/Downloads/De herkomst van je vermogen - Ondertekend.pdf"  # Replace with the input file path
    output_directory = "output"  # Replace with the desired output folder

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    compress_and_split_pdf(input_pdf_path, output_directory)
