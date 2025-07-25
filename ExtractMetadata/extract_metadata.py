#!/usr/bin/env python3
"""
Robust Media Metadata Processor

A comprehensive script to process Google Photos Takeout archives with metadata-driven
file organization. Prioritizes correctness, completeness, and detailed reporting.

Author: GitHub Copilot
Date: 2025-07-25
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Any


class MediaMetadataProcessor:
    """
    Main processor class for handling Google Photos Takeout metadata extraction
    and file organization.
    """
    
    def __init__(self, input_dir: str, output_dir: str, skipped_file: Optional[str] = None, 
                 remove_originals: bool = False):
        """
        Initialize the processor with configuration parameters.
        
        Args:
            input_dir: Source directory containing Google Photos Takeout files
            output_dir: Destination directory for processed files
            skipped_file: Optional path to previous skipped files log
            remove_originals: Whether to remove original files after processing
        """
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.skipped_file = Path(skipped_file).resolve() if skipped_file else None
        self.remove_originals = remove_originals
        
        # Create output directory early to enable logging
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging immediately
        self._setup_logging()
        
        # File indexes built during initialization
        self.media_file_index: Dict[str, Path] = {}
        self.json_file_index: Dict[str, Path] = {}
        
        # Tracking sets for reconciliation
        self.accounted_for_media: Set[str] = set()
        
        # Processing results
        self.processing_results = {
            'json_processed': 0,
            'json_successful': 0,
            'json_failed': 0,
            'media_total': 0,
            'media_processed': 0,
            'media_unmatched': 0,
            'copy_errors': 0,
            'failed_items': [],
            'files_copied': 0  # Track actual file copies, not processing attempts
        }
    
    def _setup_logging(self) -> None:
        """Configure logging for the processor."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    self.output_dir / f"metadata_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_directories(self) -> None:
        """Validate input directory exists and create output directory if needed."""
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {self.input_dir}")
        
        if not self.input_dir.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {self.input_dir}")
        
        self.logger.info(f"Output directory ready: {self.output_dir}")
    
    def build_file_indexes(self) -> None:
        """
        Build comprehensive indexes of all media and JSON files in the input directory.
        This creates a complete inventory for processing and reconciliation.
        """
        self.logger.info("Building file indexes...")
        
        for root, dirs, files in os.walk(self.input_dir):
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                filename = file_path.name
                
                if filename.lower().endswith('.json'):
                    self.json_file_index[filename] = file_path
                else:
                    # All non-JSON files are considered potential media files
                    self.media_file_index[filename] = file_path
        
        self.processing_results['media_total'] = len(self.media_file_index)
        
        self.logger.info(f"Found {len(self.json_file_index)} JSON files")
        self.logger.info(f"Found {len(self.media_file_index)} media files")
    
    def determine_processing_targets(self) -> List[Path]:
        """
        Determine which JSON files should be processed based on run mode.
        
        Returns:
            List of JSON file paths to process
        """
        if self.skipped_file and self.skipped_file.exists():
            self.logger.info(f"Running in skipped mode with file: {self.skipped_file}")
            return self._load_skipped_files()
        else:
            self.logger.info("Running in standard mode - processing all JSON files")
            return list(self.json_file_index.values())
    
    def _load_skipped_files(self) -> List[Path]:
        """Load JSON files from a previous skipped files log."""
        try:
            with open(self.skipped_file, 'r') as f:
                skipped_data = json.load(f)
            
            json_files = []
            skipped_json_paths = []
            
            for item in skipped_data.get('failed_items', []):
                if item.get('type') == 'json' and item.get('file'):
                    original_json_path = Path(item['file'])
                    skipped_json_paths.append(original_json_path)
                    
                    # Check if this exact JSON file exists in our current input directory
                    if original_json_path.exists() and original_json_path.is_file():
                        json_files.append(original_json_path)
                        self.logger.debug(f"Found skipped JSON file: {original_json_path}")
                    else:
                        self.logger.warning(f"Skipped JSON file not found: {original_json_path}")
            
            # Store the original skipped JSON paths for cleanup later
            self.skipped_json_paths = skipped_json_paths
            
            self.logger.info(f"Loaded {len(json_files)} JSON files from skipped log (out of {len(skipped_json_paths)} total)")
            return json_files
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            self.logger.error(f"Error loading skipped file: {e}")
            return []
    
    def extract_metadata(self, json_path: Path) -> Optional[Tuple[str, str]]:
        """
        Extract title and photoTakenTime from a JSON metadata file.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            Tuple of (title, photo_taken_time) or None if extraction fails
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            title = metadata.get('title')
            photo_taken_time = metadata.get('photoTakenTime', {}).get('timestamp')
            
            if not title or not photo_taken_time:
                return None
            
            return title, photo_taken_time
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.error(f"Error extracting metadata from {json_path}: {e}")
            return None
    
    def generate_file_pattern(self, title: str) -> str:
        """
        Generate a regex pattern to match related media files.
        
        Args:
            title: The title from JSON metadata
            
        Returns:
            Regex pattern string
        """
        # Remove file extension and truncate to 46 characters
        base_name = Path(title).stem[:46]
        
        # Escape special regex characters and create pattern
        escaped_base = re.escape(base_name)
        pattern = f"^{escaped_base}.*"
        
        return pattern
    
    def find_exact_matching_media_files(self, title: str) -> List[str]:
        """
        Find media files that exactly match the title (ignoring extension).
        
        Args:
            title: The title from JSON metadata
            
        Returns:
            List of exactly matching filenames
        """
        # Get the base name without extension from the title
        title_base = Path(title).stem
        
        matching_files = []
        for filename in self.media_file_index:
            # Check if the filename (without extension) exactly matches the title base
            filename_base = Path(filename).stem
            if filename_base.lower() == title_base.lower():
                matching_files.append(filename)
        
        return matching_files

    def find_pattern_matching_media_files(self, title: str, excluded_files: Set[str]) -> List[str]:
        """
        Find media files matching the regex pattern, excluding already matched files.
        
        Args:
            title: The title from JSON metadata
            excluded_files: Set of filenames to exclude from matching
            
        Returns:
            List of pattern-matching filenames
        """
        pattern = self.generate_file_pattern(title)
        regex = re.compile(pattern, re.IGNORECASE)
        matching_files = []
        
        for filename in self.media_file_index:
            if filename not in excluded_files and regex.match(filename):
                matching_files.append(filename)
        
        return matching_files

    def calculate_destination_path(self, source_path: Path, filename: str) -> Path:
        """
        Calculate the destination path preserving relative folder structure.
        
        Args:
            source_path: Original file path
            filename: Target filename (may be modified for collisions)
            
        Returns:
            Destination path
        """
        # Get relative path from input directory
        relative_path = source_path.relative_to(self.input_dir)
        
        # Replace the filename while preserving directory structure
        destination = self.output_dir / relative_path.parent / filename
        
        return destination
    
    def handle_filename_collision(self, destination: Path) -> Path:
        """
        Handle filename collisions by appending numeric suffixes.
        
        Args:
            destination: Intended destination path
            
        Returns:
            Available destination path
        """
        if not destination.exists():
            return destination
        
        # Extract name and extension
        name = destination.stem
        extension = destination.suffix
        parent = destination.parent
        
        counter = 1
        while True:
            new_name = f"{name}_{counter}{extension}"
            new_destination = parent / new_name
            
            if not new_destination.exists():
                return new_destination
            
            counter += 1
    
    def copy_and_timestamp_file(self, source: Path, destination: Path, timestamp: str) -> bool:
        """
        Copy file and set its modification time based on metadata timestamp.
        
        Args:
            source: Source file path
            destination: Destination file path
            timestamp: Unix timestamp string from metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source, destination)
            
            # Set modification time from metadata
            mtime = int(timestamp)
            os.utime(destination, (mtime, mtime))
            
            return True
            
        except (OSError, ValueError, OverflowError) as e:
            self.logger.error(f"Error copying {source} to {destination}: {e}")
            return False
    
    def check_file_already_processed(self, destination: Path, timestamp: str) -> bool:
        """
        Check if a file is already correctly processed at the destination.
        
        Args:
            destination: Destination file path
            timestamp: Expected timestamp
            
        Returns:
            True if file exists with correct timestamp
        """
        if not destination.exists():
            return False
        
        try:
            expected_mtime = int(timestamp)
            actual_mtime = int(destination.stat().st_mtime)
            
            return abs(actual_mtime - expected_mtime) < 2  # 2-second tolerance
            
        except (ValueError, OSError):
            return False
    
    def process_json_file(self, json_path: Path) -> bool:
        """
        Process a single JSON file and its associated media files.
        
        Args:
            json_path: Path to the JSON metadata file
            
        Returns:
            True if processing was successful, False otherwise
        """
        self.processing_results['json_processed'] += 1
        
        # Extract metadata
        metadata = self.extract_metadata(json_path)
        if not metadata:
            self.processing_results['json_failed'] += 1
            self.processing_results['failed_items'].append({
                'type': 'json',
                'file': str(json_path),
                'reason': 'Failed to extract metadata'
            })
            return False
        
        title, timestamp = metadata
        
        # Generate pattern and find matching files
        exact_matches = self.find_exact_matching_media_files(title)
        if exact_matches:
            self.logger.info(f"Exact matches found for {title}: {exact_matches}")
            self._process_json_with_files(json_path, title, timestamp, exact_matches)
            return True
        else:
            self.logger.info(f"No exact matches for {title}, trying pattern matching")
            pattern_matches = self.find_pattern_matching_media_files(title, set())
            if pattern_matches:
                self.logger.info(f"Pattern matches found for {title}: {pattern_matches}")
                self._process_json_with_files(json_path, title, timestamp, pattern_matches)
                return True
            else:
                self.processing_results['json_failed'] += 1
                self.processing_results['failed_items'].append({
                    'type': 'json',
                    'file': str(json_path),
                    'reason': 'No matching media files found'
                })
                return False
    
    def _process_json_with_files(self, json_path: Path, title: str, timestamp: str, matching_files: List[str]) -> bool:
        """
        Process a JSON file with its associated media files.
        
        Args:
            json_path: Path to the JSON metadata file
            title: Title from metadata
            timestamp: Timestamp from metadata
            matching_files: List of matching media filenames
            
        Returns:
            True if processing was successful, False otherwise
        """
        self.processing_results['json_processed'] += 1
        
        # Process each matching media file
        all_successful = True
        processed_files = []
        files_copied_this_json = 0
        
        for filename in matching_files:
            source_path = self.media_file_index[filename]
            
            # Mark as accounted for
            self.accounted_for_media.add(filename)
            
            # Calculate destination
            destination = self.calculate_destination_path(source_path, filename)
            
            # Check if already processed
            if self.check_file_already_processed(destination, timestamp):
                self.logger.debug(f"Skipping already processed file: {filename}")
                processed_files.append(source_path)
                continue
            
            # Handle collisions
            if destination.exists():
                destination = self.handle_filename_collision(destination)
            
            # Copy and timestamp
            if self.copy_and_timestamp_file(source_path, destination, timestamp):
                files_copied_this_json += 1
                processed_files.append(source_path)
                self.logger.info(f"Processed: {filename} -> {destination.name}")
            else:
                all_successful = False
                self.processing_results['copy_errors'] += 1
                self.processing_results['failed_items'].append({
                    'type': 'media',
                    'file': str(source_path),
                    'reason': 'Copy operation failed'
                })
        
        # Update processing counts
        self.processing_results['media_processed'] += len(matching_files)
        self.processing_results['files_copied'] += files_copied_this_json
        
        # Clean up originals if requested and all successful
        if self.remove_originals and all_successful and processed_files:
            self._cleanup_originals(json_path, processed_files)
        
        if all_successful:
            self.processing_results['json_successful'] += 1
            return True
        else:
            self.processing_results['json_failed'] += 1
            return False
    
    def _cleanup_originals(self, json_path: Path, media_paths: List[Path]) -> None:
        """Remove original JSON and media files after successful processing."""
        try:
            # In skipped mode, only remove media files from current source
            # and JSON files from the skipped log
            if self.skipped_file and self.skipped_file.exists():
                # Remove media files from current source (source 2)
                for media_path in media_paths:
                    media_path.unlink()
                    self.logger.debug(f"Removed original media file: {media_path}")
                
                # Remove JSON file only if it's in the skipped log
                if hasattr(self, 'skipped_json_paths') and json_path in self.skipped_json_paths:
                    json_path.unlink()
                    self.logger.debug(f"Removed original JSON from skipped log: {json_path}")
            else:
                # Standard mode - remove both media and JSON files
                for media_path in media_paths:
                    media_path.unlink()
                    self.logger.debug(f"Removed original: {media_path}")
                
                json_path.unlink()
                self.logger.debug(f"Removed original: {json_path}")
            
        except OSError as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def reconcile_unmatched_media(self) -> None:
        """Move media files without corresponding JSON metadata to unmatched directory."""
        # Skip unmatched reconciliation when running in skipped mode
        if self.skipped_file and self.skipped_file.exists():
            self.logger.info("Skipping unmatched media reconciliation (running in skipped mode)")
            return
            
        unmatched_files = []
        
        for filename, file_path in self.media_file_index.items():
            if filename not in self.accounted_for_media:
                unmatched_files.append((filename, file_path))
        
        if not unmatched_files:
            self.logger.info("No unmatched media files found")
            return
        
        # Create unmatched directory
        unmatched_dir = self.output_dir / "unmatched"
        unmatched_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Moving {len(unmatched_files)} unmatched files to {unmatched_dir}")
        
        for filename, source_path in unmatched_files:
            try:
                destination = unmatched_dir / filename
                
                # Handle collisions in unmatched directory
                if destination.exists():
                    destination = self.handle_filename_collision(destination)
                
                shutil.copy2(source_path, destination)
                self.processing_results['media_unmatched'] += 1
                
                # Remove original if requested
                if self.remove_originals:
                    source_path.unlink()
                
            except OSError as e:
                self.logger.error(f"Error moving unmatched file {filename}: {e}")
                self.processing_results['copy_errors'] += 1
    
    def generate_statistics_report(self) -> None:
        """Generate and display comprehensive processing statistics."""
        stats = self.processing_results
        
        print("\n" + "="*60)
        print("MEDIA METADATA PROCESSOR - FINAL REPORT")
        print("="*60)
        print(f"Input Directory:  {self.input_dir}")
        print(f"Output Directory: {self.output_dir}")
        print(f"Remove Originals: {'Yes' if self.remove_originals else 'No'}")
        
        # Show mode-specific information
        if self.skipped_file and self.skipped_file.exists():
            print(f"Processing Mode:  SKIPPED (using {self.skipped_file.name})")
            skipped_json_count = len(getattr(self, 'skipped_json_paths', []))
            print(f"Skipped JSON files in log: {skipped_json_count}")
        else:
            print(f"Processing Mode:  STANDARD")
        
        print("-"*60)
        print("JSON PROCESSING:")
        print(f"  Total JSON files processed:     {stats['json_processed']}")
        print(f"  Successfully matched:           {stats['json_successful']}")
        print(f"  Failed to process:              {stats['json_failed']}")
        print("-"*60)
        print("MEDIA FILE PROCESSING:")
        print(f"  Total unique media files found: {stats['media_total']}")
        print(f"  Media file processing attempts: {stats['media_processed']}")
        print(f"  Actual files copied:            {stats['files_copied']}")
        
        # Only show unmatched in standard mode
        if not (self.skipped_file and self.skipped_file.exists()):
            print(f"  Unique files moved to unmatched: {stats['media_unmatched']}")
        
        print(f"  Copy/timestamp errors:          {stats['copy_errors']}")
        print("-"*60)
        
        # Completeness check varies by mode
        if self.skipped_file and self.skipped_file.exists():
            # In skipped mode, show how many from the skipped log were processed
            skipped_json_count = len(getattr(self, 'skipped_json_paths', []))
            unique_processed = len(self.accounted_for_media)
            
            print(f"SKIPPED MODE RESULTS:")
            print(f"  JSON files from skipped log:    {skipped_json_count}")
            print(f"  JSON files found and processed: {stats['json_processed']}")
            print(f"  Media files matched and copied: {stats['files_copied']}")
            print(f"  Unique media files processed:   {unique_processed}")
            
            if stats['json_successful'] == stats['json_processed']:
                print("  Status: ✅ ALL SKIPPED JSON FILES SUCCESSFULLY PROCESSED")
            else:
                failed = stats['json_processed'] - stats['json_successful']
                print(f"  Status: ⚠️  {failed} JSON FILES STILL FAILED")
        else:
            # Standard mode completeness check
            unique_processed = len(self.accounted_for_media)
            total_handled = unique_processed + stats['media_unmatched']
            print(f"COMPLETENESS CHECK:")
            print(f"  Unique files processed:         {unique_processed}")
            print(f"  Files moved to unmatched:       {stats['media_unmatched']}")
            print(f"  Total files accounted for:      {total_handled}/{stats['media_total']}")
            
            if total_handled == stats['media_total']:
                print("  Status: ✅ ALL FILES ACCOUNTED FOR")
            else:
                missing = stats['media_total'] - total_handled
                print(f"  Status: ⚠️  {missing} FILES UNACCOUNTED")
        
        print("="*60)
        
        # Additional debug information
        if stats['media_processed'] > len(self.accounted_for_media):
            duplicates = stats['media_processed'] - len(self.accounted_for_media)
            print(f"Note: {duplicates} duplicate file processing attempts detected")
            print("(Some files matched multiple JSON metadata files)")
    
    def save_skipped_files_log(self) -> None:
        """Save failed items to a JSON log file for potential reprocessing."""
        if not self.processing_results['failed_items']:
            self.logger.info("No failed items to log")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.output_dir / f"skipped_files_{timestamp}.json"
        
        log_data = {
            'generated_at': datetime.now().isoformat(),
            'total_failed_items': len(self.processing_results['failed_items']),
            'failed_items': self.processing_results['failed_items']
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"Skipped files log saved to: {log_file}")
            print(f"\nSkipped files log: {log_file}")
            
        except OSError as e:
            self.logger.error(f"Error saving skipped files log: {e}")
    
    def run(self) -> None:
        """Execute the complete metadata processing workflow."""
        try:
            self.logger.info("Starting Media Metadata Processor")
            
            # Phase 1: Initialization and Indexing
            self.validate_directories()
            self.build_file_indexes()
            json_files_to_process = self.determine_processing_targets()
            
            # Log the processing mode
            if self.skipped_file and self.skipped_file.exists():
                self.logger.info(f"Running in SKIPPED mode - processing {len(json_files_to_process)} failed JSON files")
                self.logger.info("Unmatched media reconciliation will be skipped")
            else:
                self.logger.info(f"Running in STANDARD mode - processing {len(json_files_to_process)} JSON files")
            
            # Phase 2: Two-Phase Metadata-Driven Processing
            self.logger.info("Starting Phase 1: Exact filename matching...")
            exact_matched_files = set()
            exact_match_results = []
            
            # Phase 2a: Exact matching pass
            for json_path in json_files_to_process:
                metadata = self.extract_metadata(json_path)
                if metadata:
                    title, timestamp = metadata
                    exact_matches = self.find_exact_matching_media_files(title)
                    if exact_matches:
                        exact_match_results.append((json_path, title, timestamp, exact_matches))
                        exact_matched_files.update(exact_matches)
                        self.logger.debug(f"Exact match: {json_path.name} -> {exact_matches}")
            
            self.logger.info(f"Phase 1 complete: {len(exact_matched_files)} files exactly matched")
            
            # Process exact matches
            for json_path, title, timestamp, matching_files in exact_match_results:
                self._process_json_with_files(json_path, title, timestamp, matching_files)
            
            self.logger.info("Starting Phase 2: Pattern matching for remaining files...")
            
            # Phase 2b: Pattern matching pass for remaining JSON files
            for json_path in json_files_to_process:
                # Skip if already processed in exact match phase
                if any(json_path == result[0] for result in exact_match_results):
                    continue
                    
                metadata = self.extract_metadata(json_path)
                if metadata:
                    title, timestamp = metadata
                    pattern_matches = self.find_pattern_matching_media_files(title, exact_matched_files)
                    if pattern_matches:
                        self.logger.debug(f"Pattern match: {json_path.name} -> {pattern_matches}")
                        self._process_json_with_files(json_path, title, timestamp, pattern_matches)
                    else:
                        # No matches found
                        self.processing_results['json_processed'] += 1
                        self.processing_results['json_failed'] += 1
                        self.processing_results['failed_items'].append({
                            'type': 'json',
                            'file': str(json_path),
                            'reason': 'No matching media files found'
                        })
                else:
                    # Failed to extract metadata
                    self.processing_results['json_processed'] += 1
                    self.processing_results['json_failed'] += 1
                    self.processing_results['failed_items'].append({
                        'type': 'json',
                        'file': str(json_path),
                        'reason': 'Failed to extract metadata'
                    })
            
            self.logger.info("Phase 2 complete: Pattern matching finished")
            
            # Phase 3: Reconciliation of Unmatched Media (skip in skipped mode)
            self.reconcile_unmatched_media()
            
            # Phase 4: Finalization and Reporting
            self.generate_statistics_report()
            self.save_skipped_files_log()
            
            self.logger.info("Processing completed successfully")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error during processing: {e}")
            else:
                print(f"Fatal error during processing: {e}")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Robust Media Metadata Processor for Google Photos Takeout archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/takeout /path/to/output
  %(prog)s /path/to/takeout /path/to/output --rm
  %(prog)s /path/to/takeout /path/to/output --skipped /path/to/skipped_files.json
        """
    )
    
    parser.add_argument(
        'input_directory',
        help='Source directory containing Google Photos Takeout files'
    )
    
    parser.add_argument(
        'output_directory', 
        help='Destination directory for processed files'
    )
    
    parser.add_argument(
        '--skipped',
        help='Path to a skipped_files_*.json log from a previous run'
    )
    
    parser.add_argument(
        '--rm',
        action='store_true',
        help='Remove original source files after successful processing'
    )
    
    args = parser.parse_args()
    
    # Create and run the processor
    processor = MediaMetadataProcessor(
        input_dir=args.input_directory,
        output_dir=args.output_directory,
        skipped_file=args.skipped,
        remove_originals=args.rm
    )
    
    processor.run()


if __name__ == "__main__":
    main()