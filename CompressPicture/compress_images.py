import os
import argparse
from PIL import Image

def parse_args():
    parser = argparse.ArgumentParser(description="Compress and convert images.")
    parser.add_argument('-src', '--source', required=True, help="Source folder or image path")
    parser.add_argument('-dst', '--destination', required=True, help="Destination folder or image path")
    parser.add_argument('-q', '--quality', type=int, default=95, help="Quality of output images (1-95)")
    parser.add_argument('-maxw', '--maxwidth', type=int, help="Maximum width of output images")
    parser.add_argument('-maxh', '--maxheight', type=int, help="Maximum height of output images")
    parser.add_argument('-f', '--format', default=None, help="Output image format (JPEG, PNG)")
    return parser.parse_args()

def compress_image(input_path, output_path, quality, max_width=None, max_height=None, output_format=None):
    try:
        # Open the image
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if saving as JPEG
            if output_format and output_format.upper() == 'JPEG' and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize if needed
            if max_width or max_height:
                current_width, current_height = img.size
                new_width = min(max_width, current_width) if max_width else current_width
                new_height = min(max_height, current_height) if max_height else current_height
                
                # Calculate new dimensions maintaining aspect ratio
                ratio = min(new_width/current_width, new_height/current_height)
                new_size = (int(current_width * ratio), int(current_height * ratio))
                
                if new_size != img.size:
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Determine output format
            format_to_save = (output_format or img.format or 'JPEG').upper()
            
            # Prepare save parameters
            save_kwargs = {}
            if format_to_save == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif format_to_save == 'PNG':
                save_kwargs['optimize'] = True
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the compressed image
            img.save(output_path, format_to_save, **save_kwargs)
            
            # Print compression results
            original_size = os.path.getsize(input_path) / 1024  # KB
            compressed_size = os.path.getsize(output_path) / 1024  # KB
            print(f"Processed: {input_path}")
            print(f"Original: {original_size:.1f}KB → Compressed: {compressed_size:.1f}KB")
            print(f"Reduction: {(1 - compressed_size/original_size) * 100:.1f}%")
            
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

def process_images(source, destination, quality, max_width, max_height, output_format):
    # If source is a file, process single image
    if os.path.isfile(source):
        # Determine output path for single file
        if os.path.isdir(destination):
            # If destination is a directory, use original filename
            filename = os.path.basename(source)
            if output_format:
                filename = os.path.splitext(filename)[0] + '.' + output_format.lower()
            destination = os.path.join(destination, filename)
        compress_image(source, destination, quality, max_width, max_height, output_format)
        return

    # Process directory
    total_original = 0
    total_compressed = 0
    
    for root, _, files in os.walk(source):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                input_path = os.path.join(root, file)
                
                # Maintain directory structure in output
                rel_path = os.path.relpath(root, source)
                
                # Determine output filename
                if output_format:
                    file = os.path.splitext(file)[0] + '.' + output_format.lower()
                    
                output_path = os.path.join(destination, rel_path, file)
                
                # Process the image
                compress_image(input_path, output_path, quality, max_width, max_height, output_format)
                
                total_original += os.path.getsize(input_path)
                total_compressed += os.path.getsize(output_path)
    
    if total_original > 0:
        print("\nOverall Results:")
        print(f"Total Original: {total_original / (1024*1024):.2f}MB")
        print(f"Total Compressed: {total_compressed / (1024*1024):.2f}MB")
        print(f"Total Reduction: {(1 - total_compressed/total_original) * 100:.1f}%")

if __name__ == "__main__":
    args = parse_args()
    process_images(
        args.source,
        args.destination,
        args.quality,
        args.maxwidth,
        args.maxheight,
        args.format
    )