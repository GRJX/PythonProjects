import os
import shutil
import sys

def merge_directories(source_dir, dest_dir):
    """
    Merges source directory into destination directory.
    Asks user for confirmation when duplicate filenames are found.
    
    Args:
        source_dir (str): Path to source directory
        dest_dir (str): Path to destination directory
    """
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist")
        return
    
    if not os.path.exists(dest_dir):
        print(f"Creating destination directory: {dest_dir}")
        os.makedirs(dest_dir)
    
    for root, dirs, files in os.walk(source_dir):
        # Calculate relative path from source
        rel_path = os.path.relpath(root, source_dir)
        
        # Create corresponding directory structure in destination
        if rel_path != '.':
            dest_subdir = os.path.join(dest_dir, rel_path)
        else:
            dest_subdir = dest_dir
            
        if not os.path.exists(dest_subdir):
            os.makedirs(dest_subdir)
            print(f"Created directory: {dest_subdir}")
        
        # Process files
        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_subdir, file)
            
            if os.path.exists(dest_file):
                print(f"\nFile already exists: {dest_file}")
                print(f"Source: {source_file}")
                print(f"Destination: {dest_file}")
                
                while True:
                    choice = input("Replace file? (y/n/s/q): ").lower().strip()
                    if choice == 'y':
                        shutil.copy2(source_file, dest_file)
                        print(f"Replaced: {dest_file}")
                        break
                    elif choice == 'n':
                        print(f"Skipped: {dest_file}")
                        break
                    elif choice == 's':
                        # Skip this file
                        print(f"Skipped: {dest_file}")
                        break
                    elif choice == 'q':
                        print("Merge operation cancelled")
                        return
                    else:
                        print("Please enter 'y' (yes), 'n' (no), 's' (skip), or 'q' (quit)")
            else:
                shutil.copy2(source_file, dest_file)
                print(f"Copied: {source_file} -> {dest_file}")

def main():
    # Hardcoded parameters - edit these values directly
    source_directory = "source"  # Default source directory
    destination_directory = "destination"  # Default destination directory
    
    # Override with command line arguments if provided
    if len(sys.argv) >= 3:
        source_directory = sys.argv[1]
        destination_directory = sys.argv[2]
    elif len(sys.argv) == 2:
        source_directory = sys.argv[1]
        print(f"Using default destination: {destination_directory}")
    
    print(f"Merging '{source_directory}' into '{destination_directory}'")
    print("=" * 50)
    
    merge_directories(source_directory, destination_directory)
    
    print("\nMerge operation completed!")

if __name__ == "__main__":
    main()
