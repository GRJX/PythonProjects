# Install

The script requires Python 3 and the installation of Pillow and pillow_heif libraries. First, make sure Python 3 is installed on your system. Then install the required Python packages using `pip`:

```sh
pip install Pillow pillow_heif
```

# Usage

To convert HEIC files to either PNG or JPG format, use the following command in the terminal:

```sh
python heic_converter.py [-f FILE | -d DIRECTORY] FORMAT [-compress]
```

Arguments:
- `-f, --file`: The path to a single `.HEIC` file to convert.
- `-d, --directory`: The path to a directory containing `.HEIC` files to convert.
- `FORMAT`: The desired output format (`png` or `jpg`).
- `-compress` (optional): Compress the output image if possible (applies only to png).

# Examples

Converting a single HEIC image to PNG format without compression:

```sh
python heic_converter.py -f example.HEIC png
```

Batch converting all HEIC images in a directory to JPG format with compression:

```sh
python heic_converter.py -d /path/to/directory jpg -compress
```

Converting a single HEIC image to PNG format with compression enabled:

```sh
python heic_converter.py -f /path/to/photo.HEIC png -compress
```