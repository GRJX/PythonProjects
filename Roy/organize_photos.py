#!/usr/bin/env python3
"""
Photo Organizer Script

This script organizes photos from an input directory into year-based folders,
renames them based on geolocation (country_city_number), and crops them to
a 1:1 ratio while preserving faces using facial recognition.

Requirements:
    pip install Pillow exifread geopy opencv-python reverse_geocoder pillow-heif

Usage:
    python organize_photos.py <input_directory> <output_directory>
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image, ExifTags
    import exifread
    import cv2
    import reverse_geocoder as rg
    import pycountry
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages:")
    print("pip install Pillow exifread opencv-python reverse_geocoder pillow-heif pycountry")
    sys.exit(1)

# Register HEIC/HEIF support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False
    print("Warning: pillow-heif not installed. HEIC/HEIF files will not be supported.")
    print("Install with: pip install pillow-heif")


# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif', '.bmp', '.webp'}

# Country name translations (English to Dutch)
COUNTRY_TRANSLATIONS = {
    'Afghanistan': 'Afghanistan',
    'Albania': 'Albanië',
    'Algeria': 'Algerije',
    'Andorra': 'Andorra',
    'Angola': 'Angola',
    'Argentina': 'Argentinië',
    'Armenia': 'Armenië',
    'Australia': 'Australië',
    'Austria': 'Oostenrijk',
    'Azerbaijan': 'Azerbeidzjan',
    'Bahamas': 'Bahama\'s',
    'Bahrain': 'Bahrein',
    'Bangladesh': 'Bangladesh',
    'Belarus': 'Wit-Rusland',
    'Belgium': 'België',
    'Belize': 'Belize',
    'Benin': 'Benin',
    'Bhutan': 'Bhutan',
    'Bolivia': 'Bolivia',
    'Bosnia and Herzegovina': 'Bosnië en Herzegovina',
    'Botswana': 'Botswana',
    'Brazil': 'Brazilië',
    'Brunei': 'Brunei',
    'Bulgaria': 'Bulgarije',
    'Cambodia': 'Cambodja',
    'Cameroon': 'Kameroen',
    'Canada': 'Canada',
    'Chile': 'Chili',
    'China': 'China',
    'Colombia': 'Colombia',
    'Costa Rica': 'Costa Rica',
    'Croatia': 'Kroatië',
    'Cuba': 'Cuba',
    'Cyprus': 'Cyprus',
    'Czech Republic': 'Tsjechië',
    'Czechia': 'Tsjechië',
    'Denmark': 'Denemarken',
    'Dominican Republic': 'Dominicaanse Republiek',
    'Ecuador': 'Ecuador',
    'Egypt': 'Egypte',
    'El Salvador': 'El Salvador',
    'Estonia': 'Estland',
    'Ethiopia': 'Ethiopië',
    'Fiji': 'Fiji',
    'Finland': 'Finland',
    'France': 'Frankrijk',
    'Georgia': 'Georgië',
    'Germany': 'Duitsland',
    'Ghana': 'Ghana',
    'Greece': 'Griekenland',
    'Guatemala': 'Guatemala',
    'Honduras': 'Honduras',
    'Hong Kong': 'Hongkong',
    'Hungary': 'Hongarije',
    'Iceland': 'IJsland',
    'India': 'India',
    'Indonesia': 'Indonesië',
    'Iran': 'Iran',
    'Iraq': 'Irak',
    'Ireland': 'Ierland',
    'Israel': 'Israël',
    'Italy': 'Italië',
    'Jamaica': 'Jamaica',
    'Japan': 'Japan',
    'Jordan': 'Jordanië',
    'Kazakhstan': 'Kazachstan',
    'Kenya': 'Kenia',
    'Kuwait': 'Koeweit',
    'Laos': 'Laos',
    'Latvia': 'Letland',
    'Lebanon': 'Libanon',
    'Libya': 'Libië',
    'Liechtenstein': 'Liechtenstein',
    'Lithuania': 'Litouwen',
    'Luxembourg': 'Luxemburg',
    'Macau': 'Macau',
    'Madagascar': 'Madagaskar',
    'Malaysia': 'Maleisië',
    'Maldives': 'Malediven',
    'Malta': 'Malta',
    'Mauritius': 'Mauritius',
    'Mexico': 'Mexico',
    'Moldova': 'Moldavië',
    'Monaco': 'Monaco',
    'Mongolia': 'Mongolië',
    'Montenegro': 'Montenegro',
    'Morocco': 'Marokko',
    'Mozambique': 'Mozambique',
    'Myanmar': 'Myanmar',
    'Namibia': 'Namibië',
    'Nepal': 'Nepal',
    'Netherlands': 'Nederland',
    'New Zealand': 'Nieuw-Zeeland',
    'Nicaragua': 'Nicaragua',
    'Nigeria': 'Nigeria',
    'North Korea': 'Noord-Korea',
    'North Macedonia': 'Noord-Macedonië',
    'Norway': 'Noorwegen',
    'Oman': 'Oman',
    'Pakistan': 'Pakistan',
    'Panama': 'Panama',
    'Paraguay': 'Paraguay',
    'Peru': 'Peru',
    'Philippines': 'Filipijnen',
    'Poland': 'Polen',
    'Portugal': 'Portugal',
    'Qatar': 'Qatar',
    'Romania': 'Roemenië',
    'Russia': 'Rusland',
    'Russian Federation': 'Rusland',
    'Rwanda': 'Rwanda',
    'San Marino': 'San Marino',
    'Saudi Arabia': 'Saoedi-Arabië',
    'Senegal': 'Senegal',
    'Serbia': 'Servië',
    'Singapore': 'Singapore',
    'Slovakia': 'Slowakije',
    'Slovenia': 'Slovenië',
    'South Africa': 'Zuid-Afrika',
    'South Korea': 'Zuid-Korea',
    'Spain': 'Spanje',
    'Sri Lanka': 'Sri Lanka',
    'Sudan': 'Soedan',
    'Sweden': 'Zweden',
    'Switzerland': 'Zwitserland',
    'Syria': 'Syrië',
    'Taiwan': 'Taiwan',
    'Tanzania': 'Tanzania',
    'Thailand': 'Thailand',
    'Tunisia': 'Tunesië',
    'Turkey': 'Turkije',
    'Türkiye': 'Turkije',
    'Uganda': 'Oeganda',
    'Ukraine': 'Oekraïne',
    'United Arab Emirates': 'Verenigde_Arabische_Emiraten',
    'United Kingdom': 'Verenigd_Koninkrijk',
    'United States': 'Verenigde_Staten',
    'United States of America': 'Verenigde_Staten',
    'Uruguay': 'Uruguay',
    'Uzbekistan': 'Oezbekistan',
    'Vatican City': 'Vaticaanstad',
    'Venezuela': 'Venezuela',
    'Vietnam': 'Vietnam',
    'Viet Nam': 'Vietnam',
    'Yemen': 'Jemen',
    'Zambia': 'Zambia',
    'Zimbabwe': 'Zimbabwe',
    'Unknown': 'Onbekend',
}


def translate_country(country: str) -> str:
    """Translate an English country name to Dutch."""
    return COUNTRY_TRANSLATIONS.get(country, country)


def get_exif_data(image_path: str) -> dict:
    """Extract EXIF data from an image file."""
    exif_data = {}
    
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            exif_data['tags'] = tags
    except Exception as e:
        print(f"Warning: Could not read EXIF from {image_path}: {e}")
    
    return exif_data


def get_gps_coordinates(exif_data: dict) -> tuple:
    """Extract GPS coordinates from EXIF data."""
    tags = exif_data.get('tags', {})
    
    def convert_to_degrees(value):
        """Convert GPS coordinates to degrees."""
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)
    
    try:
        lat_ref = tags.get('GPS GPSLatitudeRef')
        lat = tags.get('GPS GPSLatitude')
        lon_ref = tags.get('GPS GPSLongitudeRef')
        lon = tags.get('GPS GPSLongitude')
        
        if lat and lon and lat_ref and lon_ref:
            latitude = convert_to_degrees(lat)
            longitude = convert_to_degrees(lon)
            
            if str(lat_ref) == 'S':
                latitude = -latitude
            if str(lon_ref) == 'W':
                longitude = -longitude
            
            return (latitude, longitude)
    except Exception as e:
        print(f"Warning: Could not parse GPS coordinates: {e}")
    
    return None


def get_date_taken(exif_data: dict) -> datetime:
    """Extract the date when the photo was taken from EXIF data."""
    tags = exif_data.get('tags', {})
    
    date_tags = [
        'EXIF DateTimeOriginal',
        'EXIF DateTimeDigitized',
        'Image DateTime'
    ]
    
    for tag in date_tags:
        if tag in tags:
            try:
                date_str = str(tags[tag])
                # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                continue
    
    return None


def get_location_info(coordinates: tuple) -> dict:
    """Get country and city from GPS coordinates using reverse geocoding."""
    if coordinates is None:
        return {'country': 'Onbekend', 'city': 'Onbekend'}
    
    try:
        result = rg.search([coordinates])[0]
        country_code = result.get('cc', 'Unknown')  # Country code
        city = result.get('name', 'Unknown')
        
        # Convert country code to full country name
        country = 'Unknown'
        if country_code and country_code != 'Unknown':
            try:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                if country_obj:
                    country = country_obj.name
                else:
                    country = country_code
            except Exception:
                country = country_code
        
        # Translate country name to Dutch
        country = translate_country(country)
        
        # Clean up city name (remove special characters, replace spaces with underscores)
        city = ''.join(c if c.isalnum() or c == ' ' else '' for c in city)
        city = city.replace(' ', '_')
        
        return {'country': country, 'city': city}
    except Exception as e:
        print(f"Warning: Could not reverse geocode coordinates {coordinates}: {e}")
        return {'country': 'Onbekend', 'city': 'Onbekend'}


def detect_faces_with_rotation(image_path: str) -> tuple:
    """
    Detect faces at multiple rotations and return the best rotation angle.
    First applies EXIF orientation, then checks if additional rotation is needed.
    
    Returns:
        tuple: (faces_list, rotation_angle) where rotation_angle is 0, 90, 180, or 270
               The rotation_angle is the ADDITIONAL correction needed after EXIF orientation.
    """
    try:
        import tempfile
        from PIL import ImageOps
        
        # Load the pre-trained face detection model
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # First, open with PIL and apply EXIF orientation
        pil_img = Image.open(image_path)
        
        # Apply EXIF orientation using ImageOps (handles all orientation cases)
        try:
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception:
            pass
        
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Create temp file for OpenCV processing
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Check if it's a HEIC/HEIF file
        ext = Path(image_path).suffix.lower()
        if ext in {'.heic', '.heif'}:
            print(f"  Converting HEIC to temp file for face detection...")
        
        # Save as JPG (with EXIF orientation already applied)
        pil_img.save(temp_path, 'JPEG', quality=85)
        pil_img.close()
        
        # Read the temp file with OpenCV
        img = cv2.imread(temp_path)
        
        if img is None:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return ([], 0)
        
        # First try to detect faces at 0 degrees (after EXIF correction)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces_at_0 = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # If we find faces at 0 degrees, no additional rotation needed
        if len(faces_at_0) > 0:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return (list(faces_at_0), 0)
        
        # No faces found at 0 degrees, try other rotations
        # This handles cases where EXIF is missing or incorrect
        rotations = [90, 180, 270]
        best_faces = []
        best_rotation = 0
        best_face_count = 0
        best_total_area = 0
        
        for rotation in rotations:
            if rotation == 90:
                rotated_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                rotated_img = cv2.rotate(img, cv2.ROTATE_180)
            elif rotation == 270:
                rotated_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(rotated_img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Calculate total face area as a quality metric
                total_area = sum(w * h for (x, y, w, h) in faces)
                
                # Prefer orientation with more faces, or larger total face area
                if len(faces) > best_face_count or (len(faces) == best_face_count and total_area > best_total_area):
                    best_faces = list(faces)
                    best_rotation = rotation
                    best_face_count = len(faces)
                    best_total_area = total_area
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return (best_faces, best_rotation)
        
    except Exception as e:
        print(f"  Warning: Face detection with rotation failed: {e}")
        return ([], 0)


def detect_faces(image_path: str) -> list:
    """Detect faces in an image using OpenCV's Haar Cascade classifier."""
    try:
        import tempfile
        
        # Load the pre-trained face detection model
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Check if it's a HEIC/HEIF file - convert to temp JPG first
        ext = Path(image_path).suffix.lower()
        temp_file = None
        
        if ext in {'.heic', '.heif'}:
            try:
                # Convert HEIC to temporary JPG for OpenCV processing
                print(f"  Converting HEIC to temp file for face detection...")
                pil_img = Image.open(image_path)
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # Save as JPG
                pil_img.save(temp_path, 'JPEG', quality=85)
                pil_img.close()
                
                # Read the temp file with OpenCV
                img = cv2.imread(temp_path)
            except Exception as e:
                print(f"  Warning: Could not convert HEIC for face detection: {e}")
                if temp_file and os.path.exists(temp_path):
                    os.unlink(temp_path)
                return []
        else:
            # Read the image with OpenCV directly
            img = cv2.imread(image_path)
            temp_path = None
        
        if img is None:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            return []
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return list(faces)
    except Exception as e:
        print(f"  Warning: Face detection failed: {e}")
        return []
        return []


def calculate_face_bounding_box(faces: list, img_width: int, img_height: int) -> tuple:
    """Calculate the bounding box that contains all detected faces."""
    if not len(faces):
        return None
    
    min_x = min(face[0] for face in faces)
    min_y = min(face[1] for face in faces)
    max_x = max(face[0] + face[2] for face in faces)
    max_y = max(face[1] + face[3] for face in faces)
    
    return (min_x, min_y, max_x, max_y)


def smart_crop_to_square(image_path: str, output_path: str, target_size: int = None) -> bool:
    """
    Crop an image to 1:1 ratio while trying to preserve detected faces.
    Also rotates the image to keep faces upright based on face detection.
    
    The 1:1 ratio is prioritized over keeping all faces in frame.
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Preserve EXIF data
        exif_data = img.info.get('exif')
        
        # Handle EXIF orientation using ImageOps (handles all orientation cases consistently)
        from PIL import ImageOps
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        
        # Detect faces with rotation to find if additional rotation is needed
        # (handles cases where EXIF orientation is missing or incorrect)
        faces, rotation_needed = detect_faces_with_rotation(image_path)
        
        # Apply additional rotation correction if faces were detected at a different angle
        if rotation_needed != 0 and len(faces) > 0:
            print(f"  Rotating image {rotation_needed}° to correct face orientation")
            # PIL rotation is counter-clockwise, so we need to adjust
            if rotation_needed == 90:
                img = img.rotate(-90, expand=True)
            elif rotation_needed == 180:
                img = img.rotate(180, expand=True)
            elif rotation_needed == 270:
                img = img.rotate(90, expand=True)
        
        width, height = img.size
        
        # If already square, just save/resize
        if width == height:
            if target_size:
                img = img.resize((target_size, target_size), Image.LANCZOS)
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA', 'L'):
                img = img.convert('RGB')
            # Ensure output path has .jpg extension
            output_path_str = str(output_path)
            if not output_path_str.lower().endswith('.jpg'):
                base = os.path.splitext(output_path_str)[0]
                output_path = base + '.jpg'
            # Don't preserve EXIF orientation tag since we've already applied it
            img.save(output_path, format='JPEG', quality=95)
            return True
        
        # Determine the crop size (minimum of width/height for 1:1)
        crop_size = min(width, height)
        
        # If we rotated the image, we need to re-detect faces in the rotated image
        # The face coordinates from detect_faces_with_rotation are for the rotated version
        if len(faces) > 0:
            # Calculate face bounding box using the faces detected at the correct rotation
            face_bbox = calculate_face_bounding_box(faces, width, height)
            face_center_x = (face_bbox[0] + face_bbox[2]) // 2
            face_center_y = (face_bbox[1] + face_bbox[3]) // 2
            
            # Calculate crop position centered on faces
            if width > height:
                # Landscape: crop horizontally, center on face_center_x
                left = max(0, min(face_center_x - crop_size // 2, width - crop_size))
                top = 0
            else:
                # Portrait: crop vertically, center on face_center_y
                left = 0
                top = max(0, min(face_center_y - crop_size // 2, height - crop_size))
        else:
            # No faces detected, center crop
            if width > height:
                left = (width - crop_size) // 2
                top = 0
            else:
                left = 0
                top = (height - crop_size) // 2
        
        # Perform the crop
        right = left + crop_size
        bottom = top + crop_size
        
        img_cropped = img.crop((left, top, right, bottom))
        
        # Resize if target size specified
        if target_size:
            img_cropped = img_cropped.resize((target_size, target_size), Image.LANCZOS)
        
        # Convert to RGB if necessary (HEIC images may have different modes)
        if img_cropped.mode in ('RGBA', 'P', 'LA', 'L'):
            img_cropped = img_cropped.convert('RGB')
        
        # Always save as JPEG to avoid HEIC encoder issues
        # Ensure output path has .jpg extension
        output_path_str = str(output_path)
        if not output_path_str.lower().endswith('.jpg'):
            # Remove any extension and add .jpg
            base = os.path.splitext(output_path_str)[0]
            output_path = base + '.jpg'
        
        # Save the result (don't preserve EXIF orientation since we've already applied it)
        img_cropped.save(output_path, format='JPEG', quality=95)
        return True
        
    except Exception as e:
        print(f"Error cropping image {image_path}: {e}")
        return False


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use in filenames."""
    # Replace spaces with underscores and remove special characters
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
    # Remove consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    return sanitized.strip('_')


def process_images(input_dir: str, output_dir: str, target_size: int = None):
    """
    Process all images in the input directory.
    
    - Organize by year
    - Rename based on geolocation
    - Crop to 1:1 ratio preserving faces
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collect all image files
    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(input_path.rglob(f'*{ext}'))
        image_files.extend(input_path.rglob(f'*{ext.upper()}'))
    
    if not image_files:
        print("No image files found in the input directory.")
        return
    
    image_files = sorted(image_files)
    print(f"Found {len(image_files)} image(s) to process.")
    
    # PHASE 1: Extract all metadata first (before any HEIC processing)
    # This avoids conflicts between reverse_geocoder multiprocessing and pillow-heif
    print("\n--- Phase 1: Extracting metadata ---")
    image_metadata = []
    
    for image_file in image_files:
        print(f"  Reading metadata: {image_file.name}")
        
        # Extract EXIF data using exifread (doesn't require pillow-heif)
        exif_data = get_exif_data(str(image_file))
        
        # Get date taken
        date_taken = get_date_taken(exif_data)
        if date_taken:
            year = str(date_taken.year)
        else:
            # Fall back to file modification time
            try:
                mtime = os.path.getmtime(image_file)
                date_taken = datetime.fromtimestamp(mtime)
                year = str(date_taken.year)
            except:
                date_taken = None
                year = "Unknown_Year"
        
        # Get GPS coordinates and location
        coordinates = get_gps_coordinates(exif_data)
        location = get_location_info(coordinates)
        
        image_metadata.append({
            'file': image_file,
            'year': year,
            'date_taken': date_taken,
            'country': sanitize_filename(location['country']),
            'city': sanitize_filename(location['city']),
            'has_gps': coordinates is not None
        })
    
    # PHASE 2: Process images (now safe to use pillow-heif)
    print("\n--- Phase 2: Processing images ---")
    
    # Track counters for unique naming per location
    location_counters = defaultdict(int)
    
    # Process each image
    processed = 0
    skipped = 0
    
    for meta in image_metadata:
        image_file = meta['file']
        year = meta['year']
        country = meta['country']
        city = meta['city']
        date_taken = meta['date_taken']
        
        print(f"\nProcessing: {image_file.name}")
        print(f"  Location: {country}, {city}" if meta['has_gps'] else f"  No GPS data, using: {country}, {city}")
        
        # Create year folder
        year_folder = output_path / year
        year_folder.mkdir(exist_ok=True)
        
        # Generate date string for filename (YYYY-MM format)
        if date_taken:
            date_str = date_taken.strftime("%Y-%m")
        else:
            date_str = "Unknown"
        
        # Generate unique filename
        # Format: country_city_YYYY-MM_number.jpg
        location_key = f"{year}_{country}_{city}_{date_str}"
        location_counters[location_key] += 1
        counter = location_counters[location_key]
        
        # Format: country_city_YYYY-MM_number.jpg
        new_filename = f"{country}_{city}_{date_str}_{counter:04d}.jpg"
        output_file = year_folder / new_filename
        
        # Ensure unique filename (in case of conflicts)
        while output_file.exists():
            location_counters[location_key] += 1
            counter = location_counters[location_key]
            new_filename = f"{country}_{city}_{date_str}_{counter:04d}.jpg"
            output_file = year_folder / new_filename
        
        # Crop and save the image
        if smart_crop_to_square(str(image_file), str(output_file), target_size):
            print(f"  Saved as: {year}/{new_filename}")
            processed += 1
        else:
            # If cropping fails, try to just copy the file
            print(f"  Warning: Could not crop, copying original")
            try:
                shutil.copy2(image_file, output_file)
                processed += 1
            except Exception as e:
                print(f"  Error: Could not process image: {e}")
                skipped += 1
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"  Processed: {processed} images")
    print(f"  Skipped: {skipped} images")
    print(f"  Output directory: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Organize photos by year, rename based on geolocation, and crop to 1:1 ratio.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python organize_photos.py ./input_photos ./output_photos
    python organize_photos.py ./input_photos ./output_photos --size 600
    
Output Structure:
    output_photos/
    ├── 2023/
    │   ├── NL_Amsterdam_0001.jpg
    │   ├── NL_Amsterdam_0002.jpg
    │   └── FR_Paris_0001.jpg
    └── 2024/
        └── US_New_York_0001.jpg
        """
    )
    
    parser.add_argument(
        'input_dir',
        help='Input directory containing images'
    )
    
    parser.add_argument(
        'output_dir',
        help='Output directory for organized images'
    )
    
    parser.add_argument(
        '--size',
        type=int,
        default=None,
        help='Target size in pixels for the 1:1 crop (e.g., 600 for 600x600). If not specified, uses original dimensions.'
    )
    
    args = parser.parse_args()
    
    print("="*50)
    print("Photo Organizer")
    print("="*50)
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    if args.size:
        print(f"Target size: {args.size}x{args.size} pixels")
    print("="*50)
    
    process_images(args.input_dir, args.output_dir, args.size)


if __name__ == "__main__":
    main()
