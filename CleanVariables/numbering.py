import os
import re
import argparse
from typing import List, Tuple, Optional

def find_robot_files(directory: str = ".") -> List[str]:
    """Find all .robot files in the given directory."""
    robot_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.robot'):
                robot_files.append(os.path.join(root, file))
    return robot_files

def parse_test_cases(file_path: str) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    """
    Parse a robot file and extract test cases.
    Returns: (file_lines, test_cases)
    test_cases: [(line_number, original_line, test_case_name)]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    test_cases = []
    in_test_cases_section = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check for section headers
        if line_stripped.startswith('***') and line_stripped.endswith('***'):
            if 'Test Cases' in line_stripped:
                in_test_cases_section = True
            else:
                in_test_cases_section = False
            continue
        
        # If we're in test cases section and line starts at beginning (no indentation)
        if in_test_cases_section and line and not line[0].isspace() and line_stripped:
            # Extract test case name (remove existing numbering if present)
            match = re.match(r'^(\[TC\d+\])?\s*(.+)', line_stripped)
            if match:
                test_case_name = match.group(2).strip()
                test_cases.append((i, line.rstrip('\n'), test_case_name))
    
    return lines, test_cases

def generate_new_numbering(test_cases: List[Tuple[int, str, str]]) -> List[Tuple[int, str, str, str]]:
    """
    Generate new numbering for test cases.
    Returns: [(line_number, original_line, test_case_name, new_line)]
    """
    numbered_cases = []
    
    for idx, (line_num, original_line, test_case_name) in enumerate(test_cases, 1):
        new_number = f"[TC{idx:03d}]"
        new_line = f"{new_number} {test_case_name}"
        numbered_cases.append((line_num, original_line, test_case_name, new_line))
    
    return numbered_cases

def show_changes_and_get_approval(file_path: str, changes: List[Tuple[int, str, str, str]], dry_run: bool = False) -> List[Tuple[int, str]]:
    """
    Show proposed changes and get user approval.
    Returns: [(line_number, approved_new_line)]
    """
    print(f"\n{'='*60}")
    print(f"File: {file_path}")
    if dry_run:
        print("(DRY RUN - No changes will be applied)")
    print(f"{'='*60}")
    
    approved_changes = []
    
    for line_num, original_line, test_case_name, new_line in changes:
        print(f"\nLine {line_num + 1}:")
        print(f"  Original: {original_line}")
        print(f"  Proposed: {new_line}")
        
        if dry_run:
            print("  [DRY RUN] Change would be applied")
            approved_changes.append((line_num, new_line))
        else:
            while True:
                choice = input("  Action: (a)ccept, (s)kip, (e)dit manually, (q)uit: ").lower().strip()
                
                if choice == 'a':
                    approved_changes.append((line_num, new_line))
                    break
                elif choice == 's':
                    print("  Skipped.")
                    break
                elif choice == 'e':
                    manual_edit = input("  Enter new line: ").strip()
                    approved_changes.append((line_num, manual_edit))
                    break
                elif choice == 'q':
                    return approved_changes
                else:
                    print("  Invalid choice. Please enter 'a', 's', 'e', or 'q'.")
    
    return approved_changes

def apply_changes(file_path: str, lines: List[str], approved_changes: List[Tuple[int, str]], dry_run: bool = False) -> None:
    """Apply approved changes to the file."""
    if not approved_changes:
        print(f"No changes to apply for {file_path}")
        return
    
    if dry_run:
        print(f"[DRY RUN] Would apply {len(approved_changes)} changes to {file_path}")
        return
    
    # Apply changes
    for line_num, new_line in approved_changes:
        lines[line_num] = new_line + '\n'
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Applied {len(approved_changes)} changes to {file_path}")

def main():
    """Main function to process robot files."""
    parser = argparse.ArgumentParser(description="Robot Framework Test Case Renumbering Tool")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show proposed changes without modifying files")
    parser.add_argument("--dir", "-d", default=".", 
                       help="Directory to search for .robot files (default: current directory)")
    args = parser.parse_args()
    
    print("Robot Framework Test Case Renumbering Tool")
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
    print("==========================================")
    
    # Find robot files
    robot_files = find_robot_files(args.dir)
    if not robot_files:
        print(f"No .robot files found in directory: {args.dir}")
        return
    
    print(f"Found {len(robot_files)} .robot file(s) in {args.dir}:")
    for file in robot_files:
        print(f"  - {file}")
    
    # Process each file
    for file_path in robot_files:
        try:
            lines, test_cases = parse_test_cases(file_path)
            
            if not test_cases:
                print(f"\nNo test cases found in {file_path}")
                continue
            
            # Generate new numbering (each file starts at 1)
            changes = generate_new_numbering(test_cases)
            
            # Filter out cases that don't need changes
            actual_changes = []
            for line_num, original_line, test_case_name, new_line in changes:
                if original_line.strip() != new_line:
                    actual_changes.append((line_num, original_line, test_case_name, new_line))
            
            if not actual_changes:
                print(f"\nNo changes needed for {file_path}")
                continue
            
            # Show changes and get approval
            approved_changes = show_changes_and_get_approval(file_path, actual_changes, args.dry_run)
            
            # Apply approved changes
            apply_changes(file_path, lines, approved_changes, args.dry_run)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
