#!/usr/bin/env python3

import os
import argparse
import subprocess
import json
import math
from shutil import which


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Compress a video file to a target size in MB.")
    parser.add_argument('-i', '--input', required=True, help="Input video file path")
    parser.add_argument('-o', '--output', required=True, help="Output video file path")
    parser.add_argument('-s', '--size', type=float, required=True, help="Target size in MB")
    parser.add_argument('-q', '--quality', type=int, default=23, 
                        help="CRF value (0-51, lower is better quality, default: 23)")
    parser.add_argument('-p', '--preset', default='medium', choices=[
                        'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 
                        'medium', 'slow', 'slower', 'veryslow'], 
                        help="Compression preset (default: medium)")
    parser.add_argument('--no-audio', action='store_true', help="Remove audio from output")
    return parser.parse_args()


def get_video_info(input_path):
    """Get video information using ffprobe"""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        input_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to get video info: {result.stderr}")
    
    data = json.loads(result.stdout)
    return data


def calculate_bitrate(video_info, target_size_mb, no_audio=False):
    """Calculate the required video bitrate to achieve the target size"""
    # Extract duration from video info
    duration = float(video_info['format']['duration'])
    
    # Convert target size from MB to bits
    target_size_bits = target_size_mb * 8 * 1024 * 1024
    
    # Audio bitrate estimation (if we're keeping audio)
    audio_bitrate = 0
    if not no_audio:
        for stream in video_info['streams']:
            if stream['codec_type'] == 'audio' and 'bit_rate' in stream:
                audio_bitrate = int(stream['bit_rate'])
                break
        if audio_bitrate == 0:
            # Default assumption if we can't detect actual audio bitrate
            audio_bitrate = 128000
    
    # Calculate video bitrate needed
    audio_size = duration * audio_bitrate
    video_bitrate = (target_size_bits - audio_size) / duration
    
    # Ensure we don't go too low
    return max(video_bitrate, 100000)  # At least 100kbps


def compress_video(input_path, output_path, target_size_mb, quality=23, preset='medium', no_audio=False):
    """Compress the video to the target size using ffmpeg"""
    # Check if ffmpeg is installed
    if which('ffmpeg') is None:
        raise Exception("FFmpeg is not installed or not in the system PATH")
    
    # Get video information
    video_info = get_video_info(input_path)
    print(f"Input video duration: {float(video_info['format']['duration']):.2f} seconds")
    print(f"Input video size: {int(video_info['format']['size']) / (1024 * 1024):.2f} MB")
    
    # Calculate required bitrate
    bitrate = calculate_bitrate(video_info, target_size_mb, no_audio)
    bitrate_kbps = int(bitrate / 1000)
    print(f"Target video bitrate: {bitrate_kbps} kbps to achieve {target_size_mb} MB")
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',
        '-b:v', f'{bitrate_kbps}k',
        '-crf', str(quality),
        '-preset', preset,
        '-pass', '1',
        '-f', 'null'
    ]
    
    if not no_audio:
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
    else:
        cmd.extend(['-an'])
    
    cmd.append('/dev/null' if os.name != 'nt' else 'NUL')
    
    # Execute first pass
    print("Running first pass...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"First pass failed: {result.stderr}")
    
    # Second pass
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',
        '-b:v', f'{bitrate_kbps}k',
        '-crf', str(quality),
        '-preset', preset,
        '-pass', '2'
    ]
    
    if not no_audio:
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
    else:
        cmd.extend(['-an'])
    
    cmd.append(output_path)
    
    # Execute second pass
    print("Running second pass...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Second pass failed: {result.stderr}")
    
    # Verify output file size
    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Output video size: {output_size_mb:.2f} MB (Target: {target_size_mb} MB)")
    
    # Cleanup pass logfiles
    for f in os.listdir():
        if f.startswith('ffmpeg2pass'):
            os.remove(f)


def main():
    args = parse_args()
    
    try:
        print(f"Compressing video: {args.input}")
        print(f"Target size: {args.size} MB")
        compress_video(
            args.input,
            args.output,
            args.size,
            args.quality,
            args.preset,
            args.no_audio
        )
        print("Compression completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
