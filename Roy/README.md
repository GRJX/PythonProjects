# Photo Organizer

A Python script to organize photos into year-based folders, rename them based on geolocation, and crop them to a 1:1 ratio while preserving faces.

## Features

- **Year-based organization**: Photos are sorted into folders by the year they were taken (from EXIF data)
- **Geolocation-based naming**: Files are renamed to `<country>_<city>_<number>.ext` format using GPS coordinates from EXIF data
- **Smart 1:1 cropping**: Images are cropped to a square ratio while trying to preserve detected faces
- **Face detection**: Uses OpenCV's Haar Cascade classifier to detect faces and center the crop around them
- **Multiple format support**: JPG, JPEG, PNG, HEIC, HEIF, TIFF, TIF, BMP, WEBP

## Requirements

Install the required Python packages:

```bash
`pip install -r requirements.txt
```

Or manually:

```bash
pip install Pillow exifread opencv-python reverse_geocoder reportlab
```

## Scripts

### 1. organize_photos.py - Photo Organizer

Organizes photos into year folders, renames based on geolocation, and crops to 1:1.

**Usage:**

```bash
python organize_photos.py <input_directory> <output_directory>
python organize_photos.py ./input_photos ./output_photos --size 709
```

### 2. create_photo_pdf.py - PDF Generator

Creates a printable PDF with images in a 2x3 grid (6x6 cm images, 7x7 cm spacing).

**Usage:**

```bash
python create_photo_pdf.py <input_directory> <output_pdf>
python create_photo_pdf.py ./organized_photos/2024 ./photo_album.pdf
```

**Output:**

- Page 1: 2x3 grid of images
- Page 2: 2x3 grid of info blocks (YYYY-MM and Country, City)
- Repeats for all images...

The info page is mirrored for double-sided printing alignment.

## Workflow

1. Run `organize_photos.py` to organize and crop your photos
2. Run `create_photo_pdf.py` on the organized photos to create a printable PDF

```bash
# Step 1: Organize photos
python organize_photos.py ~/Pictures/vacation ~/Pictures/organized --size 709

# Step 2: Create PDF from a year folder
python create_photo_pdf.py ~/Pictures/organized/2024 ~/Documents/photos_2024.pdf
```

## Output Structure (after organize_photos.py)

```
output_photos/
├── 2023/
│   ├── NL_Amsterdam_0001.jpg
│   ├── NL_Amsterdam_0002.jpg
│   └── FR_Paris_0001.jpg
├── 2024/
│   └── US_New_York_0001.jpg
└── Unknown_Year/
    └── Unknown_Unknown_0001.jpg
```

## How organize_photos.py Works

1. **Scans input directory** for supported image formats
2. **Extracts EXIF data** to get:
   - Date taken (for year organization)
   - GPS coordinates (for location naming)
3. **Reverse geocodes** GPS coordinates to get country and city names
4. **Detects faces** in each image using OpenCV
5. **Smart crops** to 1:1 ratio:
   - If faces are detected, centers the crop on the faces
   - If no faces, uses center crop
   - Maintains 1:1 ratio as the priority (some faces may be cropped if necessary)
6. **Saves** the processed images with the new naming convention

## Notes

- Images without GPS data will be named `Unknown_Unknown_<number>.ext`
- Images without EXIF date will use the file modification date
- The 1:1 ratio is prioritized over keeping all faces in the frame
- Original images are not modified; new files are created in the output directory

## Calculating Size for Print

For 6 cm × 6 cm prints:

- At 100 DPI: 236 × 236 pixels (`--size 236`)
- At 150 DPI: 354 × 354 pixels (`--size 354`)
- At 300 DPI: 709 × 709 pixels (`--size 709`)
