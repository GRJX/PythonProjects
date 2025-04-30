# Video Compression Utility

This utility compresses MP4 and other video files to a specific target file size using FFmpeg, while maintaining the best possible quality.

## Requirements

- Python 3.6 or higher
- FFmpeg (must be installed and available in your system PATH)

## Installation

1. Ensure Python 3.6+ is installed on your system
2. Install FFmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## Usage

```bash
python compress_video.py -i INPUT_FILE -o OUTPUT_FILE -s TARGET_SIZE_MB [options]
```

### Arguments

- `-i, --input`: Path to the input video file (required)
- `-o, --output`: Path for the compressed output video file (required)
- `-s, --size`: Target size in megabytes (MB) (required)
- `-q, --quality`: CRF value (0-51, lower is better quality, default: 23)
- `-p, --preset`: Compression preset (default: medium)
  - Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
- `--no-audio`: Remove audio from output video to save space

### Examples

Compress a video to 50MB with default settings:
```bash
python compress_video.py -i input.mp4 -o compressed.mp4 -s 50
```

Compress with better quality (lower CRF value):
```bash
python compress_video.py -i input.mp4 -o compressed.mp4 -s 20 -q 18
```

Compress quickly with a faster preset:
```bash
python compress_video.py -i input.mp4 -o compressed.mp4 -s 30 -p veryfast
```

Compress to a very small size without audio:
```bash
python compress_video.py -i input.mp4 -o compressed.mp4 -s 10 --no-audio
```

## How It Works

This script uses a two-pass encoding strategy to achieve the target file size:

1. Calculates the necessary video bitrate based on the target size and video duration
2. Performs a first encoding pass to analyze the video
3. Performs a second encoding pass to compress the video to the target bitrate
4. Includes constant rate factor (CRF) to maintain quality within bitrate constraints

## Troubleshooting

### Error: "FFmpeg is not installed or not in the system PATH"

If you encounter this error, follow these steps to resolve it:

1. **Verify FFmpeg installation**:
   Check if FFmpeg is installed by running:
   ```bash
   ffmpeg -version
   ```
   If you see version information, FFmpeg is installed but might not be in your PATH.

2. **Install FFmpeg if needed**:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. **Add FFmpeg to your PATH**:
   - **macOS/Linux**: Add to your shell profile (.bashrc, .zshrc, etc.):
     ```bash
     export PATH="$PATH:/path/to/ffmpeg"
     ```
   - **Windows**:
     - Right-click on "This PC" or "My Computer" and select "Properties"
     - Click "Advanced system settings"
     - Click "Environment Variables"
     - Under "System variables" find "Path" and click "Edit"
     - Add the path to the folder containing ffmpeg.exe
     - Click "OK" to save

4. **Specify full path to FFmpeg**:
   If you can't modify your PATH, you can edit the script to use the full path to FFmpeg:
   ```python
   # Replace 'ffmpeg' with the full path to your FFmpeg executable
   ffmpeg_path = '/full/path/to/ffmpeg'
   # Then use ffmpeg_path in subprocess calls instead of 'ffmpeg'
   ```

5. **Restart your terminal/command prompt** after making PATH changes.

## Notes

- Lower CRF values (like 18) provide better quality but may make it harder to hit the target size
- Slower presets provide better compression but take longer to process
- The actual output size might vary slightly from the target size
- For very small target sizes, video quality may be significantly reduced
