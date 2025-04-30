# Image Compression Script

This script compresses images within a specified folder, allowing you to reduce their file sizes and optionally resize them. It can also convert images to a different format if desired.

## Features
- Compresses images to reduce file size while maintaining quality.
- Supports resizing images to a maximum width and/or height.
- Converts images to different formats (e.g., JPEG, PNG).
- Maintains the directory structure when saving compressed images.

## Requirements
- Python 3.x
- `PIL` (Pillow library)

## Installation

Ensure you have Python 3.x installed. You can install the required Python library using pip:

```bash
pip install pillow
```

## Usage

Run the script from the command line with the following options:

```bash
python compress_images.py -src <source_folder> -dst <destination_folder> [options]
```

### Arguments

- **`-src`, `--source`** (required): Path to the source folder containing images to compress.
- **`-dst`, `--destination`** (required): Path to the destination folder where compressed images will be saved.
- **`-q`, `--quality`** (optional): Quality of the output images (default is `85`). Accepts values from `1` to `95`.
- **`-maxw`, `--maxwidth`** (optional): Maximum width of the output images. Images will be resized proportionally.
- **`-maxh`, `--maxheight`** (optional): Maximum height of the output images. Images will be resized proportionally.
- **`-f`, `--format`** (optional): Output image format (e.g., `JPEG`, `PNG`). Defaults to the original format if not specified.

### Example Commands

1. **Compress images and save to a new folder with default settings:**
   ```bash
   python compress_images.py -src images/ -dst compressed_images/
   ```

2. **Compress images with custom quality:**
   ```bash
   python compress_images.py -src images/ -dst compressed_images/ -q 70
   ```

3. **Resize images with a maximum width and height:**
   ```bash
   python compress_images.py -src images/ -dst compressed_images/ -maxw 800 -maxh 600
   ```

4. **Convert images to a different format (e.g., PNG):**
   ```bash
   python compress_images.py -src images/ -dst compressed_images/ -f PNG
   ```

## Output

- The script will create the destination folder if it does not exist.
- It maintains the directory structure of the source folder.
- Outputs processed image details, including original and compressed sizes.
- Displays a summary of total space saved at the end of the operation.

### Example Output

```
Processed 'images/photo1.jpg' -> 'compressed_images/photo1.jpg' | Original Size: 1.50 MB | Compressed Size: 1.20 MB
Processed 'images/subfolder/photo2.png' -> 'compressed_images/subfolder/photo2.png' | Original Size: 2.00 MB | Compressed Size: 1.60 MB
Total Original Size: 3.50 MB
Total Compressed Size: 2.80 MB
Size reduced by 20.00%
```

## Error Handling

- Skips non-image files and logs a message: `Skipping non-image file: <file_path>`.
- Ensures the output format is valid; defaults to `JPEG` if an unsupported format is provided.

## License

This script is provided "as is" without warranty of any kind.
```
