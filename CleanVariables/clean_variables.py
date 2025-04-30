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


def find_variable_occurrences(variable_name, base_dir):
    """
    Find all occurrences of a variable in the specified directory (including subdirectories).
    Only checks .robot and .resource files.
    Returns a list of (file_path, line_number, line_content) tuples.
    """
    occurrences = []
    # Using re.NOFLAG to ensure case sensitivity (default behavior)
    pattern = re.compile(r'\$\{' + re.escape(variable_name) + r'\}')
    
    # Walk through all directories recursively
    try:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(('.robot', '.resource')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line_num, line in enumerate(lines, 1):
                                if pattern.search(line):
                                    occurrences.append((file_path, line_num, line.strip()))
                    except Exception as e:
                        print(f"{Fore.YELLOW}Warning: Could not read file {file_path}: {e}")
    except Exception as e:
        print(f"{Fore.RED}Error accessing directory {base_dir}: {e}")
    
    return occurrences


def extract_variables_from_file(file_path):
    """
    Extract all variables in the format ${variable_name} from a file.
    Returns a dictionary with variable names as keys and their values as values.
    """
    variables = {}
    pattern = re.compile(r'\$\{([^}]+)\}\s*(.*)')
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                match = pattern.search(line.strip())
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    variables[var_name] = var_value
    except Exception as e:
        print(f"{Fore.RED}Error reading file {file_path}: {e}")
        return {}
    
    return variables


def remove_variable_from_file(file_path, variable_name, value=None):
    """
    Remove a line containing the specified variable from a file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        pattern = re.compile(r'\$\{' + re.escape(variable_name) + r'\}')
        filtered_lines = [line for line in lines if not pattern.search(line)]
        
        if len(filtered_lines) < len(lines):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            print(f"{Fore.GREEN}Variable {variable_name} successfully removed from {file_path}")
        else:
            print(f"{Fore.YELLOW}No occurrences of variable {variable_name} found in {file_path}")
            
    except Exception as e:
        print(f"{Fore.RED}Error modifying file {file_path}: {e}")


def replace_variable_in_file(file_path, old_var, new_var, line_num=None):
    """
    Replace all occurrences of ${old_var} with ${new_var} in a file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        new_content = content.replace(f"${{{old_var}}}", f"${{{new_var}}}")
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"{Fore.GREEN}Variable ${{{old_var}}} successfully replaced with ${{{new_var}}} in {file_path}")
        else:
            print(f"{Fore.YELLOW}No occurrences of variable ${{{old_var}}} found in {file_path}")
            
    except Exception as e:
        print(f"{Fore.RED}Error modifying file {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Clean unused variables from files and standardize variable naming")
    parser.add_argument("base_dir", help="Base directory to search for variable occurrences")
    parser.add_argument("file", help="Path to the file containing variables in ${variable_name} format")
    args = parser.parse_args()

    # Check if the file exists
    if not os.path.isfile(args.file):
        print(f"{Fore.RED}Error: File {args.file} does not exist")
        return 1

    # Check if the base directory exists
    if not os.path.isdir(args.base_dir):
        print(f"{Fore.RED}Error: Directory {args.base_dir} does not exist")
        return 1

    # Extract variables from the file
    variables = extract_variables_from_file(args.file)
    if not variables:
        print(f"{Fore.YELLOW}No variables found in {args.file}")
        return 0

    print(f"{Fore.CYAN}Found {len(variables)} variables in {args.file}")
    
    for var_name, var_value in variables.items():
        print(f"\n{Fore.CYAN}Processing variable: {Fore.WHITE}${{{var_name}}} {var_value}")
        
        # Find all occurrences of the variable
        occurrences = find_variable_occurrences(var_name, args.base_dir)
        
        # Show occurrences
        print(f"Found {len(occurrences)} occurrences:")
        for i, (file_path, line_num, line) in enumerate(occurrences, 1):
            rel_path = os.path.relpath(file_path, start=args.base_dir)
            print(f"{i}. {rel_path}:{line_num}: {line}")
        
        if len(occurrences) == 1:
            # If only found once, prompt to remove
            confirm = input(f"\n{Fore.YELLOW}This variable is used only once. Remove it? (Enter to confirm, any other key to skip): ")
            if confirm == "":
                file_to_modify = occurrences[0][0]
                remove_variable_from_file(file_to_modify, var_name)
        
        elif len(occurrences) > 1 and not var_name.isupper():
            # If found multiple times and not in uppercase, prompt for replacement
            print(f"\n{Fore.YELLOW}This variable is used multiple times and is not in uppercase.")
            suggested_name = var_name.upper()
            new_name = input(f"Enter new name for the variable (default: {suggested_name}): ").strip()
            
            if not new_name:
                new_name = suggested_name
            
            if new_name != var_name:
                confirm = input(f"Replace all occurrences of ${{{var_name}}} with ${{{new_name}}}? (Enter to confirm, any other key to skip): ")
                if confirm == "":
                    for file_path, line_num, _ in occurrences:
                        replace_variable_in_file(file_path, var_name, new_name, line_num)
    
    print(f"\n{Fore.GREEN}Variable processing completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())