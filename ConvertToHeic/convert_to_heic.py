#!/usr/bin/env python3

import os
import argparse
from PIL import Image
from pillow_heif import register_heif_opener

SUPPORTED_FORMATS = {'png', 'jpg'}

def parse_args():
    parser = argparse.ArgumentParser(description="Batch convert HEIC images to PNG or JPG format.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help="File to convert")
    group.add_argument('-d', '--directory', type=str, help="Directory containing files to convert")
    parser.add_argument('format', choices=SUPPORTED_FORMATS, help="Output image format (png or jpg)")
    parser.add_argument('-compress', action='store_true', default=False, help="Compress output image if possible")

    return parser.parse_args()

def batch_convert_heic_to_other(file_or_dir, photo_format, compress):
    register_heif_opener()  # This must be done before opening any HEIC files
   
    if os.path.isfile(file_or_dir) and file_or_dir.endswith('.HEIC'):
        convert_file(file_or_dir, photo_format, compress)
    elif os.path.isdir(file_or_dir):
        for photo in os.listdir(file_or_dir):
            full_path = os.path.join(file_or_dir, photo)
            if os.path.isfile(full_path) and photo.endswith('.HEIC'):
                convert_file(full_path, photo_format, compress)
    else:
        print(f"{file_or_dir} is neither a file nor a directory or it does not exist.")

def convert_file(path, photo_format, compress):
    base_filename = os.path.splitext(path)[0]
    converted_photo = f"{base_filename}.{photo_format}"
    
    try:
        with Image.open(path) as img:
            if compress and photo_format == 'png':
                img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
                img.save(converted_photo, optimize=True)
            else:
                img.save(converted_photo)
            print(f"Successfully converted '{path}' to '{converted_photo}'")
    except Exception as e:
        print(f"Failed to convert {path}: {str(e)}")

if __name__ == "__main__":
    args = parse_args()
    path = args.file or args.directory
    batch_convert_heic_to_other(path, args.format, args.compress)
