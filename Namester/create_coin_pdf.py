#!/usr/bin/env python3
"""
Coin PDF Generator

This script creates a PDF with circular coin images (3 cm diameter).
The front page contains the image as a circular coin, 
the back page contains info blocks with year/month and location.

Expected filename format: <country>_<city>_<YYYY>-<MM>_<number>.jpg

Requirements:
    pip install Pillow reportlab

Usage:
    python create_coin_pdf.py <input_image> <output_pdf>
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import re
import io

try:
    from PIL import Image, ImageDraw
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
COIN_DIAMETER = 3.5 * cm  # 3 cm diameter coins
GRID_SIZE = 4 * cm      # 4 cm grid cells (includes spacing)
GRID_COLS = 5
GRID_ROWS = 7
COINS_PER_PAGE = GRID_COLS * GRID_ROWS  # 35 coins per page

# Back page coin border (provides margin for alignment tolerance)
COIN_BORDER_WIDTH = 3 * cm / 10  # 1 mm border around each coin on back


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
    Calculate the position for a coin in the grid.
    Returns (x, y) coordinates for the center of the coin.
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
    
    # Calculate center position of the cell
    x = offset_x + col * GRID_SIZE + GRID_SIZE / 2
    # Y is from bottom, so we need to invert row order
    y = offset_y + (GRID_ROWS - 1 - row) * GRID_SIZE + GRID_SIZE / 2
    
    return (x, y)


def create_circular_image(img: Image.Image, size_px: int) -> tuple:
    """
    Create a circular version of the image.
    Returns a tuple of (RGBA image, edge_color_rgb).
    The edge_color_rgb is a tuple (r, g, b) normalized to 0-1 range.
    """
    # Resize image to target size
    img = img.resize((size_px, size_px), Image.LANCZOS)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Sample edge pixels before masking
    edge_color = sample_edge_color(img)
    
    # Create a circular mask
    mask = Image.new('L', (size_px, size_px), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size_px - 1, size_px - 1), fill=255)
    
    # Apply the mask
    result = Image.new('RGBA', (size_px, size_px), (255, 255, 255, 0))
    result.paste(img, (0, 0))
    result.putalpha(mask)
    
    return result, edge_color


def sample_edge_color(img: Image.Image) -> tuple:
    """
    Sample pixels around the edge of a circular region and return average color.
    Returns (r, g, b) normalized to 0-1 range for PDF drawing.
    """
    import math
    
    width, height = img.size
    center_x, center_y = width / 2, height / 2
    radius = min(width, height) / 2
    
    # Sample points around the circle edge
    num_samples = 36  # Sample every 10 degrees
    samples = []
    
    for i in range(num_samples):
        angle = 2 * math.pi * i / num_samples
        # Sample just inside the edge (at 95% radius)
        x = int(center_x + radius * 0.95 * math.cos(angle))
        y = int(center_y + radius * 0.95 * math.sin(angle))
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        
        pixel = img.getpixel((x, y))
        # Handle different color modes
        if isinstance(pixel, tuple):
            if len(pixel) >= 3:
                samples.append(pixel[:3])  # RGB or RGBA
        else:
            # Grayscale
            samples.append((pixel, pixel, pixel))
    
    # Calculate average color
    if samples:
        avg_r = sum(s[0] for s in samples) / len(samples)
        avg_g = sum(s[1] for s in samples) / len(samples)
        avg_b = sum(s[2] for s in samples) / len(samples)
        
        # Normalize to 0-1 range for PDF
        return (avg_r / 255.0, avg_g / 255.0, avg_b / 255.0)
    else:
        # Fallback to black
        return (0, 0, 0)


def draw_coin_page(c: canvas.Canvas, coins: list, page_width: float, page_height: float):
    """Draw a page with coins in a grid."""
    # Target size in pixels for 3cm at 300 DPI
    # 3cm * 300 DPI / 2.54 cm/inch ≈ 354 pixels
    TARGET_SIZE_PX = 354
    
    for i, coin_data in enumerate(coins):
        if i >= COINS_PER_PAGE:
            break
        
        center_x, center_y = calculate_grid_position(i, page_width, page_height)
        
        try:
            # Open image
            img = Image.open(coin_data['path'])
            
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
            
            # Crop to square (center crop)
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            
            # Create circular image and get edge color
            circular_img, edge_color = create_circular_image(img, TARGET_SIZE_PX)
            
            # Convert to PNG in memory (to preserve transparency)
            img_buffer = io.BytesIO()
            circular_img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            # Draw the coin image
            img_reader = ImageReader(img_buffer)
            # Position from bottom-left corner
            x = center_x - COIN_DIAMETER / 2
            y = center_y - COIN_DIAMETER / 2
            c.drawImage(img_reader, x, y, width=COIN_DIAMETER, height=COIN_DIAMETER, mask='auto')
            
        except Exception as e:
            print(f"Warning: Could not draw coin {coin_data['path']}: {e}")
            # Draw a placeholder circle
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.circle(center_x, center_y, COIN_DIAMETER / 2)


def draw_back_page_mirrored(c: canvas.Canvas, coins: list, page_width: float, page_height: float):
    """
    Draw a page with coin images mirrored horizontally for double-sided printing.
    When printed double-sided, the back will align with the front.
    """
    # Target size in pixels for 3cm at 300 DPI
    TARGET_SIZE_PX = 354
    
    for i, coin_data in enumerate(coins):
        if i >= COINS_PER_PAGE:
            break
        
        # Get normal position
        _, center_y = calculate_grid_position(i, page_width, page_height)
        
        # Mirror horizontally for back page (flip columns)
        col = i % GRID_COLS
        mirrored_col = GRID_COLS - 1 - col
        
        # Recalculate x position with mirrored column
        total_grid_width = GRID_COLS * GRID_SIZE
        offset_x = (page_width - total_grid_width) / 2
        center_x = offset_x + mirrored_col * GRID_SIZE + GRID_SIZE / 2
        
        try:
            # Open image
            img = Image.open(coin_data['path'])
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA', 'L'):
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
            
            # Crop to square (center crop)
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            
            # Create circular image and get edge color
            circular_img, edge_color = create_circular_image(img, TARGET_SIZE_PX)
            
            # Convert to PNG in memory (to preserve transparency)
            img_buffer = io.BytesIO()
            circular_img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            # Draw the coin image
            img_reader = ImageReader(img_buffer)
            x = center_x - COIN_DIAMETER / 2
            y = center_y - COIN_DIAMETER / 2
            c.drawImage(img_reader, x, y, width=COIN_DIAMETER, height=COIN_DIAMETER, mask='auto')
            
        except Exception as e:
            print(f"Warning: Could not draw coin {coin_data['path']}: {e}")
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.circle(center_x, center_y, COIN_DIAMETER / 2)


def create_pdf(image_path: str, output_path: str, count: int = 1):
    """Create the PDF with coin pages and info pages."""
    # Parse filename for info
    parsed = parse_filename(Path(image_path).name)
    
    # Create coin data for the specified count
    coins = []
    for _ in range(count):
        coins.append({
            'path': image_path,
            'filename': Path(image_path).name,
            'country': parsed['country'],
            'city': parsed['city'],
            'date': parsed['date']
        })
    
    # Get page size
    page_width, page_height = A4
    
    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Process coins in batches of COINS_PER_PAGE
    total_pages = (len(coins) + COINS_PER_PAGE - 1) // COINS_PER_PAGE
    
    print(f"Creating PDF with {len(coins)} coin(s) across {total_pages * 2} pages...")
    
    for page_num in range(total_pages):
        start_idx = page_num * COINS_PER_PAGE
        end_idx = min(start_idx + COINS_PER_PAGE, len(coins))
        page_coins = coins[start_idx:end_idx]
        
        print(f"  Processing page {page_num + 1}/{total_pages} ({len(page_coins)} coins)")
        
        # Draw coin page (front)
        draw_coin_page(c, page_coins, page_width, page_height)
        c.showPage()
        
        # Draw coin page (back) - mirror the positions for double-sided printing
        draw_back_page_mirrored(c, page_coins, page_width, page_height)
        c.showPage()
    
    # Save the PDF
    c.save()
    print(f"\nPDF created: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Create a PDF with circular coin images (3 cm diameter) for double-sided printing.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python create_coin_pdf.py photo.jpg coins.pdf
    python create_coin_pdf.py photo.jpg coins.pdf -n 10
    python create_coin_pdf.py Netherlands_Amsterdam_2024-01_0001.jpg coins.pdf

Input:
    - Single image file with filename like: NL_Amsterdam_2024-01_0001.jpg
    - Use -n/--count to specify how many coins to create
    
Output:
    - PDF with alternating pages:
      - Page 1: Grid of circular 3cm coins with the image
      - Page 2: Grid of info blocks (YYYY-MM and City) mirrored for double-sided printing
      - etc.
        """
    )
    
    parser.add_argument(
        'input_image',
        help='Input image file'
    )
    
    parser.add_argument(
        'output_pdf',
        help='Output PDF file path'
    )
    
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=1,
        help='Number of coins to create (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_image)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_image}' does not exist.")
        sys.exit(1)
    
    if input_path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"Error: Unsupported image format '{input_path.suffix}'.")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)
    
    print("="*50)
    print("Coin PDF Generator")
    print("="*50)
    print(f"Input image: {args.input_image}")
    print(f"Output PDF: {args.output_pdf}")
    print(f"Number of coins: {args.count}")
    print(f"Coin diameter: {COIN_DIAMETER/cm:.0f} cm")
    print(f"Grid layout: {GRID_COLS}x{GRID_ROWS} ({COINS_PER_PAGE} coins per page)")
    print("="*50)
    
    # Create PDF
    create_pdf(args.input_image, args.output_pdf, args.count)


if __name__ == "__main__":
    main()
