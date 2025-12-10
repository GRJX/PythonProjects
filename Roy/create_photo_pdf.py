#!/usr/bin/env python3
"""
Photo PDF Generator

This script creates a PDF with images in a 2x3 grid layout.
Each image is 6x6 cm with a 7x7 cm grid spacing.
The back of each page contains info blocks with year/month and location.

Expected filename format: <country>_<city>_<YYYY>-<MM>_<number>.jpg

Requirements:
    pip install Pillow reportlab

Usage:
    python create_photo_pdf.py <input_directory> <output_pdf>
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import re
import io

try:
    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages:")
    print("pip install Pillow reportlab")
    sys.exit(1)


# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif', '.bmp', '.webp'}

# Layout constants
IMAGE_SIZE = 7 * cm  # 6 cm x 6 cm images
GRID_SIZE = 8 * cm   # 7 cm x 7 cm grid cells (includes spacing)
GRID_COLS = 2
GRID_ROWS = 3
IMAGES_PER_PAGE = GRID_COLS * GRID_ROWS  # 6 images per page


def parse_filename(filename: str) -> dict:
    """
    Parse the filename to extract country, city, and date.
    Expected format: <country>_<city>_<YYYY>-<MM>_<number>.jpg
    Examples:
        Netherlands_Rotterdam_2021-09_0001.jpg
        Italy_Moso_in_Passiria_2021-08_0001.jpg
    """
    # Remove extension
    name = Path(filename).stem
    
    # Pattern to match: anything_YYYY-MM_number at the end
    # This handles city names with underscores
    pattern = r'^(.+?)_(\d{4}-\d{2})_(\d+)$'
    match = re.match(pattern, name)
    
    if match:
        location_part = match.group(1)  # e.g., "Netherlands_Rotterdam" or "Italy_Moso_in_Passiria"
        date_str = match.group(2)       # e.g., "2021-09"
        
        # Split location into country and city
        parts = location_part.split('_')
        if len(parts) >= 2:
            country = parts[0]
            city = '_'.join(parts[1:])  # Handle city names with underscores
        else:
            country = location_part
            city = "Unknown"
        
        # Parse date
        try:
            date = datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            date = datetime.now()
    else:
        # Fallback for unexpected format
        country = "Onbekend"
        city = "Onbekend"
        date = datetime.now()
    
    # Convert underscores to spaces for display
    city = city.replace('_', ' ')
    country = country.replace('_', ' ')
    
    return {'country': country, 'city': city, 'date': date}


def calculate_grid_position(index: int, page_width: float, page_height: float) -> tuple:
    """
    Calculate the position for an image in the grid.
    Returns (x, y) coordinates for the bottom-left corner of the image.
    """
    # Calculate total grid dimensions
    total_grid_width = GRID_COLS * GRID_SIZE
    total_grid_height = GRID_ROWS * GRID_SIZE
    
    # Calculate offset to center the grid
    offset_x = (page_width - total_grid_width) / 2
    offset_y = (page_height - total_grid_height) / 2
    
    # Calculate row and column
    col = index % GRID_COLS
    row = index // GRID_COLS
    
    # Calculate position (center the 6cm image in the 7cm cell)
    cell_padding = (GRID_SIZE - IMAGE_SIZE) / 2
    
    x = offset_x + col * GRID_SIZE + cell_padding
    # Y is from bottom, so we need to invert row order
    y = offset_y + (GRID_ROWS - 1 - row) * GRID_SIZE + cell_padding
    
    return (x, y)


def draw_image_page(c: canvas.Canvas, images: list, page_width: float, page_height: float):
    """Draw a page with images in a 2x3 grid."""
    # Target size in pixels for 7cm at 300 DPI
    # 7cm * 300 DPI / 2.54 cm/inch ≈ 827 pixels
    TARGET_SIZE_PX = 827
    JPEG_QUALITY = 95
    
    for i, img_data in enumerate(images):
        if i >= IMAGES_PER_PAGE:
            break
        
        x, y = calculate_grid_position(i, page_width, page_height)
        
        try:
            # Open image (already cropped to 1:1 by organize_photos.py)
            img = Image.open(img_data['path'])
            
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'P', 'LA', 'L'):
                # Create white background for transparent images
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to target size for PDF
            img = img.resize((TARGET_SIZE_PX, TARGET_SIZE_PX), Image.LANCZOS)
            
            # Compress to JPEG in memory
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            img_buffer.seek(0)
            
            # Draw the image
            img_reader = ImageReader(img_buffer)
            c.drawImage(img_reader, x, y, width=IMAGE_SIZE, height=IMAGE_SIZE)
        except Exception as e:
            print(f"Warning: Could not draw image {img_data['path']}: {e}")
            # Draw a placeholder rectangle
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.rect(x, y, IMAGE_SIZE, IMAGE_SIZE)


def collect_images(input_dir: str) -> list:
    """Collect all images from the input directory."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
    
    images = []
    
    # Find all image files
    for file in sorted(input_path.iterdir()):
        if file.suffix.lower() in SUPPORTED_FORMATS:
            # Parse filename for location and date
            parsed = parse_filename(file.name)
            
            images.append({
                'path': str(file),
                'filename': file.name,
                'country': parsed['country'],
                'city': parsed['city'],
                'date': parsed['date']
            })
    
    return images


def create_pdf(images: list, output_path: str):
    """Create the PDF with image pages and info pages."""
    if not images:
        print("No images to process.")
        return
    
    # Get page size
    page_width, page_height = A4
    
    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Process images in batches of IMAGES_PER_PAGE
    total_pages = (len(images) + IMAGES_PER_PAGE - 1) // IMAGES_PER_PAGE
    
    print(f"Creating PDF with {len(images)} images across {total_pages * 2} pages...")
    
    for page_num in range(total_pages):
        start_idx = page_num * IMAGES_PER_PAGE
        end_idx = min(start_idx + IMAGES_PER_PAGE, len(images))
        page_images = images[start_idx:end_idx]
        
        print(f"  Processing page {page_num + 1}/{total_pages} ({len(page_images)} images)")
        
        # Draw image page (front)
        draw_image_page(c, page_images, page_width, page_height)
        c.showPage()
        
        # Draw info page (back) - mirror the positions for double-sided printing
        draw_info_page_mirrored(c, page_images, page_width, page_height)
        c.showPage()
    
    # Save the PDF
    c.save()
    print(f"\nPDF created: {output_path}")


def draw_info_page_mirrored(c: canvas.Canvas, images: list, page_width: float, page_height: float):
    """
    Draw a page with info blocks mirrored horizontally for double-sided printing.
    When printed double-sided, the info will align with the image on the front.
    """
    TEXT_PADDING = 1 * cm  # 1 cm padding from border
    
    for i, img_data in enumerate(images):
        if i >= IMAGES_PER_PAGE:
            break
        
        # Get normal position
        x, y = calculate_grid_position(i, page_width, page_height)
        
        # Mirror horizontally for back page (flip columns)
        col = i % GRID_COLS
        mirrored_col = GRID_COLS - 1 - col
        
        # Recalculate x position with mirrored column
        total_grid_width = GRID_COLS * GRID_SIZE
        offset_x = (page_width - total_grid_width) / 2
        cell_padding = (GRID_SIZE - IMAGE_SIZE) / 2
        x = offset_x + mirrored_col * GRID_SIZE + cell_padding
        
        # Get info
        date_str = img_data['date'].strftime("%Y-%m")
        location_str = f"{img_data['country']}, {img_data['city']}"
        
        # Calculate center of the cell
        center_x = x + IMAGE_SIZE / 2
        center_y = y + IMAGE_SIZE / 2
        
        # Calculate available width for text (IMAGE_SIZE minus 2x padding)
        available_width = IMAGE_SIZE - 2 * TEXT_PADDING
        
        # Draw border for the info block
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.rect(x, y, IMAGE_SIZE, IMAGE_SIZE)
        
        # Draw text centered
        c.setFillColorRGB(0, 0, 0)
        
        # Date on first line - larger font
        date_font_size = 24
        c.setFont("Helvetica-Bold", date_font_size)
        date_width = c.stringWidth(date_str, "Helvetica-Bold", date_font_size)
        c.drawString(center_x - date_width / 2, center_y + 15, date_str)
        
        # Location on second line - larger font, may need to scale down if too wide
        location_font_size = 18
        c.setFont("Helvetica", location_font_size)
        location_width = c.stringWidth(location_str, "Helvetica", location_font_size)
        
        # Scale down font if text is too wide for available space
        while location_width > available_width and location_font_size > 10:
            location_font_size -= 1
            c.setFont("Helvetica", location_font_size)
            location_width = c.stringWidth(location_str, "Helvetica", location_font_size)
        
        c.drawString(center_x - location_width / 2, center_y - 20, location_str)


def main():
    parser = argparse.ArgumentParser(
        description='Create a PDF with photos in a 2x3 grid layout with info pages.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python create_photo_pdf.py ./organized_photos/2024 ./photo_album.pdf
    python create_photo_pdf.py ~/Pictures/vacation ~/Documents/vacation.pdf

Input:
    - Directory containing images with filenames like: NL_Amsterdam_0001.jpg
    
Output:
    - PDF with alternating pages:
      - Page 1: 2x3 grid of 6x6 cm images
      - Page 2: 2x3 grid of info blocks (YYYY-MM and Country, City)
      - Page 3: Next 6 images...
      - etc.
        """
    )
    
    parser.add_argument(
        'input_dir',
        help='Input directory containing images'
    )
    
    parser.add_argument(
        'output_pdf',
        help='Output PDF file path'
    )
    
    args = parser.parse_args()
    
    print("="*50)
    print("Photo PDF Generator")
    print("="*50)
    print(f"Input directory: {args.input_dir}")
    print(f"Output PDF: {args.output_pdf}")
    print(f"Layout: {GRID_COLS}x{GRID_ROWS} grid, {IMAGE_SIZE/cm:.0f}x{IMAGE_SIZE/cm:.0f} cm images")
    print("="*50)
    
    # Collect images
    images = collect_images(args.input_dir)
    
    if not images:
        print("No supported images found in the input directory.")
        sys.exit(1)
    
    print(f"Found {len(images)} image(s)")
    
    # Create PDF
    create_pdf(images, args.output_pdf)


if __name__ == "__main__":
    main()
