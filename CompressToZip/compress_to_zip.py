import os
import zipfile
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Zip files in a folder into multiple zip files based on a max size.")
    parser.add_argument('-src', '--source', required=True, help="Source folder path")
    parser.add_argument('-dist', '--destination', required=True, help="Destination folder path")
    parser.add_argument('-max', '--maxsize', type=int, default=20, help="Maximum zip file size in megabytes")
    
    return parser.parse_args()

def to_bytes(size_in_mb):
    return size_in_mb * 1024 * 1024

def initialize_new_zip(destination_folder, zip_number):
    zip_filename = os.path.join(destination_folder, f'compressed_{zip_number:03}.zip')
    print(f"Creating new zip file: {zip_filename}")
    return zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED), zip_filename

def finalize_zip(zip_file):
    zip_file.close()
    print(f"Finalized zip file: {zip_file.filename}")

def create_zip(source_folder, destination_folder, max_size_bytes):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f"Created destination folder: {destination_folder}")

    current_size, zip_number, current_zip_size, current_zip, zip_filename = 0, 1, 0, None, ''
    
    for root, _, files in os.walk(source_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_size = os.path.getsize(file_path)
            
            if current_zip is None or (current_zip_size + file_size) > max_size_bytes:
                if current_zip:
                    finalize_zip(current_zip)
                current_zip, zip_filename = initialize_new_zip(destination_folder, zip_number)
                current_zip_size = 0
                zip_number += 1
            
            relative_path = os.path.relpath(file_path, source_folder)
            current_zip.write(file_path, relative_path)
            current_zip_size += file_size
            current_size += file_size
            print(f"Added '{relative_path}' to {zip_filename}. Size: {file_size / (1024 * 1024):.2f} MB")

    if current_zip:
        finalize_zip(current_zip)
    
    total_compressed_size = current_size / (1024 * 1024)
    print(f"Compressed a total of {total_compressed_size:.2f} MB into {zip_number - 1} zip file(s).")

if __name__ == "__main__":
    args = parse_args()
    max_size_bytes = to_bytes(args.maxsize)
    create_zip(args.source, args.destination, max_size_bytes)
