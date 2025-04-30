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


def split_variable_name(var_name):
    """
    Split a variable name into words and join them with underscores.
    Handles camelCase, snake_case, and other common naming conventions.
    """
    # First replace underscores with spaces
    result = var_name.replace('_', ' ')
    
    # Add space before capital letters that are preceded by lowercase letters
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    
    # Split by spaces, filter empty strings, and join with underscores
    words = [word for word in result.split() if word]
    return '_'.join(words).upper()


def scan_for_lowercase_variables(base_dir, file_extensions=None):
    """
    Scan the entire directory for the first variable in the ${variable_name} format
    that appears after VAR and has at least one lowercase character.
    Returns a dictionary with variable names as keys
    and lists of (file_path, line_number, line_content) tuples as values.
    """
    if file_extensions is None:
        file_extensions = ('.robot', '.resource', '.py', '.txt')
    
    variables_found = {}
    
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
                                # Only process lines that start with VAR
                                stripped_line = line.strip()
                                if stripped_line.startswith('VAR'):
                                    # Find the first ${variable} pattern after VAR
                                    var_pattern = re.compile(r'VAR\s+.*?\$\{([^}]+)\}')
                                    match = var_pattern.search(stripped_line)
                                    if match:
                                        var_name = match.group(1)
                                        # Check if the variable has at least one lowercase character
                                        if var_name != var_name.upper() and var_name != var_name.lower():
                                            if var_name not in variables_found:
                                                variables_found[var_name] = []
                                            variables_found[var_name].append((file_path, line_num, stripped_line))
                    except Exception as e:
                        print(f"{Fore.YELLOW}Warning: Could not read file {file_path}: {e}")
    except Exception as e:
        print(f"{Fore.RED}Error accessing directory {base_dir}: {e}")
    
    return variables_found


def replace_variable_in_file(file_path, old_var, new_var, replace_all_in_file=False):
    """
    Replace occurrences of ${old_var} with ${new_var} in a file.
    If replace_all_in_file is True, replaces all occurrences in the file.
    If replace_all_in_file is False, only replaces the first occurrence after "VAR" in each line starting with VAR.
    Returns the number of replacements made.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Create a version of the content we can use for case-insensitive searches
        lowercase_content = content.lower()
        old_pattern_lower = f"${{{old_var.lower()}}}"
        new_pattern = f"${{{new_var}}}"
        
        replacements = 0
        new_content = content
        
        if not replace_all_in_file:
            # Only modify VAR lines - process line by line
            lines = content.split("\n")
            new_lines = []
            
            for line in lines:
                if line.strip().lower().startswith("var"):
                    # Find the position after VAR where the variable might be
                    var_pos = line.lower().find("var")
                    if var_pos >= 0:
                        # Look for the variable pattern in this line (case-insensitive)
                        var_part = line[var_pos:]
                        var_part_lower = var_part.lower()
                        var_match_pos = var_part_lower.find(old_pattern_lower)
                        
                        if var_match_pos >= 0:
                            # Found a match - replace this occurrence
                            # Get the actual variable as it appears in the text (preserving original case)
                            actual_var = var_part[var_match_pos:var_match_pos + len(old_pattern_lower)]
                            
                            # Replace only the first occurrence after VAR
                            prefix = line[:var_pos + var_match_pos]
                            suffix = var_part[var_match_pos + len(actual_var):]
                            new_line = prefix + new_pattern + suffix
                            new_lines.append(new_line)
                            replacements += 1
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if replacements > 0:
                new_content = "\n".join(new_lines)
        else:
            # Replace all instances of the variable in the entire file
            # First, find all the actual instances of the variable with their exact casing
            i = 0
            while i < len(lowercase_content):
                var_pos = lowercase_content.find(old_pattern_lower, i)
                if var_pos == -1:
                    break
                    
                # Get the actual variable as it appears in the text (preserving original case)
                actual_var = content[var_pos:var_pos + len(old_pattern_lower)]
                
                # Replace this specific instance with the new variable
                before = new_content[:var_pos]
                after = new_content[var_pos + len(actual_var):]
                new_content = before + new_pattern + after
                
                # Update the lowercase content to reflect this change
                lowercase_content = lowercase_content[:var_pos] + " " * len(new_pattern) + lowercase_content[var_pos + len(old_pattern_lower):]
                
                replacements += 1
                i = var_pos + len(new_pattern)
        
        if replacements > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return replacements
        return 0
            
    except Exception as e:
        print(f"{Fore.RED}Error modifying file {file_path}: {e}")
        return 0


def replace_all_occurrences_in_file(file_path, old_var, new_var):
    """
    Replace ALL occurrences of ${old_var} with ${new_var} in a file, not just in VAR lines.
    Returns the number of replacements made.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        pattern = re.compile(f'\\$\\{{{re.escape(old_var)}\\}}')
        matches = pattern.findall(content)
        num_replacements = len(matches)
        
        if num_replacements > 0:
            new_content = pattern.sub(f'$\{{{new_var}\}}', content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return num_replacements
        return 0
            
    except Exception as e:
        print(f"{Fore.RED}Error modifying file {file_path}: {e}")
        return 0


def scan_all_occurrences(base_dir, var_name, file_extensions=None):
    """
    Find all occurrences of ${var_name} in all files in the directory.
    Returns a dictionary with file paths as keys and lists of line numbers as values.
    """
    if file_extensions is None:
        file_extensions = ('.robot', '.resource', '.py', '.txt')
    
    occurrences = {}
    
    try:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line_num, line in enumerate(lines, 1):
                                pattern = re.compile(f'\\$\\{{{re.escape(var_name)}\\}}')
                                if pattern.search(line):
                                    if file_path not in occurrences:
                                        occurrences[file_path] = []
                                    occurrences[file_path].append(line_num)
                    except Exception as e:
                        print(f"{Fore.YELLOW}Warning: Could not read file {file_path}: {e}")
    except Exception as e:
        print(f"{Fore.RED}Error accessing directory {base_dir}: {e}")
    
    return occurrences


def main():
    parser = argparse.ArgumentParser(
        description="Find and replace variables in lines starting with VAR that have any lowercase characters"
    )
    parser.add_argument("base_dir", help="Base directory to scan for variable occurrences")
    parser.add_argument(
        "--extensions", 
        help="Comma-separated list of file extensions to scan (default: .robot,.resource,.py,.txt)",
        default=".robot,.resource,.py,.txt"
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
    parser.add_argument(
        "--replace-all-in-file", 
        action="store_true", 
        help="Replace all occurrences of a variable within the same file where it's found in a VAR line"
    )
    args = parser.parse_args()

    # Check if the base directory exists
    if not os.path.isdir(args.base_dir):
        print(f"{Fore.RED}Error: Directory {args.base_dir} does not exist")
        return 1
    
    # Parse file extensions
    file_extensions = tuple(args.extensions.split(','))
    
    # Scan for lowercase variables
    print(f"{Fore.CYAN}Scanning directory: {args.base_dir}")
    print(f"{Fore.CYAN}File extensions: {file_extensions}")
    print(f"{Fore.CYAN}Finding the FIRST variable after VAR in each line that has any lowercase characters")
    if args.replace_all_in_file:
        print(f"{Fore.CYAN}Will replace ALL occurrences of variables within the same files where they're found")
    
    variables_found = scan_for_lowercase_variables(args.base_dir, file_extensions)
    
    if not variables_found:
        print(f"{Fore.GREEN}No lowercase variables found.")
        return 0
    
    print(f"{Fore.CYAN}Found {len(variables_found)} lowercase variables:")
    
    # Sort variables by name for consistent output
    sorted_vars = sorted(variables_found.items())
    
    # Process each variable
    for var_index, (var_name, occurrences) in enumerate(sorted_vars, 1):
        print(f"\n{Fore.CYAN}[{var_index}/{len(sorted_vars)}] Variable: {Fore.WHITE}${{{var_name}}}")
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
        
        # Suggest uppercase version with word splitting
        suggested_name = split_variable_name(var_name)
        
        if args.batch:
            new_name = suggested_name
            should_replace = True
        else:
            print(f"\n{Fore.YELLOW}Suggested replacement: ${{{suggested_name}}}")
            print(f"{Fore.CYAN}(Converted from '{var_name}' with word splitting and uppercase)")
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
                confirm = input(f"Replace all occurrences of ${{{var_name}}} with ${{{new_name}}}? (Enter to confirm, any other key to skip): ")
                should_replace = confirm == ""
        
        # Perform replacements if confirmed
        if should_replace:
            if args.dry_run:
                print(f"{Fore.GREEN}[DRY RUN] Would replace ${{{var_name}}} with ${{{new_name}}} in VAR lines in {len(file_occurrences)} files")
                if args.replace_all_in_file:
                    print(f"{Fore.GREEN}[DRY RUN] Would also replace all occurrences of the variable within each file where it was found")
            else:
                total_replacements = 0
                files_changed = 0
                
                # Process each file individually
                for rel_path in file_occurrences.keys():
                    file_path = os.path.join(args.base_dir, rel_path)
                    
                    # Always process the file with replace_all_in_file set based on the args
                    replacements = replace_variable_in_file(file_path, var_name, new_name, args.replace_all_in_file)
                    if replacements > 0:
                        total_replacements += replacements
                        files_changed += 1
                
                if args.replace_all_in_file:
                    print(f"{Fore.GREEN}Successfully replaced ${{{var_name}}} with ${{{new_name}}} {total_replacements} times in {files_changed} files")
                else:
                    print(f"{Fore.GREEN}Successfully replaced ${{{var_name}}} with ${{{new_name}}} in VAR lines in {files_changed} files")
    
    print(f"\n{Fore.GREEN}Variable processing completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())