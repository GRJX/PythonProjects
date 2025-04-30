#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "colorama",
#   "argparse"
# ]
# ///

import os
import re
import sys
import argparse
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init(autoreset=True)


def convert_to_snake_case(var_name):
    """
    Convert a variable name to snake_case.
    Handles CamelCase, PascalCase, and other common naming conventions.
    """
    # First replace existing underscores with spaces
    result = var_name.replace('_', ' ')
    
    # Add space before capital letters
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', result)
    
    # Add space after capital letters that are followed by lowercase letters
    result = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', result)
    
    # Split by spaces, filter empty strings, and join with underscores
    words = [word.strip().lower() for word in result.split() if word.strip()]
    return '_'.join(words)


def scan_for_uppercase_variables(base_dir, file_extensions=None):
    """
    Scan the entire directory for variables in the {variable_name} format
    that have any uppercase character, but are not completely uppercase.
    Returns a dictionary with variable names as keys
    and lists of (file_path, line_number, line_content) tuples as values.
    Also returns counters for skipped variables.
    """
    if file_extensions is None:
        file_extensions = ('.robot', '.resource')
    
    variables_found = {}
    skipped_lowercase = {}
    skipped_uppercase = {}
    
    # Walk through all directories recursively
    try:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line_num, line in enumerate(lines, 1):
                                # Find all {variable} patterns in the line
                                matches = re.finditer(r'\{([^{}]+)\}', line)
                                for match in matches:
                                    var_name = match.group(1)
                                    
                                    # Skip if already all lowercase (including digits and underscores)
                                    if var_name.lower() == var_name and not any(c.isupper() for c in var_name):
                                        if var_name not in skipped_lowercase:
                                            skipped_lowercase[var_name] = 0
                                        skipped_lowercase[var_name] += 1
                                        continue
                                    
                                    # Skip if all uppercase
                                    if var_name.upper() == var_name:
                                        if var_name not in skipped_uppercase:
                                            skipped_uppercase[var_name] = 0
                                        skipped_uppercase[var_name] += 1
                                        continue
                                    
                                    # Check if the variable has at least one uppercase character
                                    if any(c.isupper() for c in var_name):
                                        if var_name not in variables_found:
                                            variables_found[var_name] = []
                                        variables_found[var_name].append((file_path, line_num, line.strip()))
                    except Exception as e:
                        print(f"{Fore.YELLOW}Warning: Could not read file {file_path}: {e}")
    except Exception as e:
        print(f"{Fore.RED}Error accessing directory {base_dir}: {e}")
    
    return variables_found, skipped_lowercase, skipped_uppercase


def replace_variable_in_file(file_path, old_var, new_var, replace_all_in_file=True):
    """
    Replace occurrences of {old_var} with {new_var} in a file.
    Returns the number of replacements made.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Use direct string replacement for better accuracy
        old_pattern = f"{{{old_var}}}"
        new_pattern = f"{{{new_var}}}"
        
        # Count occurrences
        count = content.count(old_pattern)
        
        if count > 0:
            # Replace the pattern
            new_content = content.replace(old_pattern, new_pattern)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return count
        return 0
            
    except Exception as e:
        print(f"{Fore.RED}Error modifying file {file_path}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Find variables in {variable_name} format and convert them to lowercase snake_case"
    )
    parser.add_argument("base_dir", help="Base directory to scan for variable occurrences")
    parser.add_argument(
        "--extensions", 
        help="Comma-separated list of file extensions to scan (default: .robot,.resource,.py,.txt,.html,.js,.ts)",
        default=".robot,.resource,.py,.txt,.html,.js,.ts"
    )
    parser.add_argument(
        "--batch", 
        action="store_true", 
        help="Process all variables in batch mode without individual confirmation"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only show what would be changed without making actual changes"
    )
    args = parser.parse_args()

    # Check if the base directory exists
    if not os.path.isdir(args.base_dir):
        print(f"{Fore.RED}Error: Directory {args.base_dir} does not exist")
        return 1
    
    # Parse file extensions
    file_extensions = tuple(args.extensions.split(','))
    
    # Scan for variables with uppercase characters
    print(f"{Fore.CYAN}Scanning directory: {args.base_dir}")
    print(f"{Fore.CYAN}File extensions: {file_extensions}")
    print(f"{Fore.CYAN}Finding variables in {{variable}} format that contain uppercase characters")
    print(f"{Fore.CYAN}Skipping variables that are already in lowercase or completely in uppercase")
    
    variables_found, skipped_lowercase, skipped_uppercase = scan_for_uppercase_variables(args.base_dir, file_extensions)
    
    # Print statistics about skipped variables
    if skipped_lowercase:
        print(f"{Fore.GREEN}Skipped {len(skipped_lowercase)} variables that are already in lowercase:")
        for var_name, count in sorted(skipped_lowercase.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {Fore.GREEN}{{{var_name}}} - found {count} times")
        if len(skipped_lowercase) > 5:
            print(f"  {Fore.GREEN}... and {len(skipped_lowercase) - 5} more")
    
    if skipped_uppercase:
        print(f"{Fore.GREEN}Skipped {len(skipped_uppercase)} variables that are completely in uppercase:")
        for var_name, count in sorted(skipped_uppercase.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {Fore.GREEN}{{{var_name}}} - found {count} times")
        if len(skipped_uppercase) > 5:
            print(f"  {Fore.GREEN}... and {len(skipped_uppercase) - 5} more")
    
    if not variables_found:
        print(f"{Fore.GREEN}No variables with mixed case found that need conversion.")
        return 0
    
    print(f"{Fore.CYAN}Found {len(variables_found)} variables with mixed case that need conversion:")
    
    # Sort variables by name for consistent output
    sorted_vars = sorted(variables_found.items())
    
    # Process each variable
    for var_index, (var_name, occurrences) in enumerate(sorted_vars, 1):
        print(f"\n{Fore.CYAN}[{var_index}/{len(sorted_vars)}] Variable: {Fore.WHITE}{{{var_name}}}")
        print(f"Found in {len(occurrences)} places:")
        
        # Group occurrences by file for clearer output
        file_occurrences = {}
        for file_path, line_num, line in occurrences:
            rel_path = os.path.relpath(file_path, start=args.base_dir)
            if rel_path not in file_occurrences:
                file_occurrences[rel_path] = []
            file_occurrences[rel_path].append((line_num, line))
        
        # Display occurrences grouped by file
        for i, (rel_path, lines) in enumerate(file_occurrences.items(), 1):
            print(f"{Fore.CYAN}  File {i}: {Fore.WHITE}{rel_path}")
            for line_num, line in lines[:3]:  # Show only first 3 occurrences per file
                print(f"    Line {line_num}: {line}")
            if len(lines) > 3:
                print(f"    ... and {len(lines) - 3} more occurrences in this file")
        
        # Suggest lowercase snake_case version
        suggested_name = convert_to_snake_case(var_name)
        
        if args.batch:
            new_name = suggested_name
            should_replace = True
        else:
            print(f"\n{Fore.YELLOW}Suggested replacement: {{{suggested_name}}}")
            print(f"{Fore.CYAN}(Converted from '{var_name}' to lowercase snake_case)")
            new_name = input(f"Enter new name (default: {suggested_name}, 's' to skip, 'q' to quit): ").strip()
            
            if new_name.lower() == 'q':
                print(f"{Fore.CYAN}Exiting...")
                return 0
            
            if new_name.lower() == 's':
                print(f"{Fore.YELLOW}Skipping {var_name}...")
                continue
                
            if not new_name:
                new_name = suggested_name
            
            should_replace = new_name != var_name
            
            if should_replace and not args.dry_run:
                confirm = input(f"Replace all occurrences of {{{var_name}}} with {{{new_name}}}? (Enter to confirm, any other key to skip): ")
                should_replace = confirm == ""
        
        # Perform replacements if confirmed
        if should_replace:
            if args.dry_run:
                print(f"{Fore.GREEN}[DRY RUN] Would replace {{{var_name}}} with {{{new_name}}} in {len(file_occurrences)} files")
            else:
                total_replacements = 0
                files_changed = 0
                
                # Process each file individually
                for rel_path in file_occurrences.keys():
                    file_path = os.path.join(args.base_dir, rel_path)
                    
                    # Replace all occurrences in the file
                    replacements = replace_variable_in_file(file_path, var_name, new_name)
                    if replacements > 0:
                        total_replacements += replacements
                        files_changed += 1
                
                print(f"{Fore.GREEN}Successfully replaced {{{var_name}}} with {{{new_name}}} {total_replacements} times in {files_changed} files")
    
    print(f"\n{Fore.GREEN}Variable processing completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())