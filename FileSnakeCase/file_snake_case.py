#!/usr/bin/env python3
"""
Robot Framework File Snake Case Converter

Dit script scant een directory voor .robot en .resource bestanden, converteert de bestandsnamen
naar snake_case, en werkt automatisch alle referenties bij in andere bestanden.

Author: GitHub Copilot
Date: 2025-01-27
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def to_snake_case(name: str) -> str:
    """
    Converteer een string naar snake_case.
    
    Args:
        name: De originele string
        
    Returns:
        De string in snake_case formaat
    """
    # Vervang spaties en andere tekens door underscores
    name = re.sub(r'[-\s]+', '_', name)
    
    # Voeg underscores toe voor camelCase conversie
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    
    # Converteer naar lowercase
    name = name.lower()
    
    # Verwijder dubbele underscores
    name = re.sub(r'_+', '_', name)
    
    # Verwijder leading/trailing underscores
    name = name.strip('_')
    
    return name


def find_robot_files(directory: Path) -> List[Path]:
    """
    Zoek alle .robot en .resource bestanden in een directory en subdirectories.
    
    Args:
        directory: De directory om te scannen
        
    Returns:
        Lijst van gevonden bestanden
    """
    robot_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.robot', '.resource')):
                robot_files.append(Path(root) / file)
    
    return robot_files


def build_file_index(files: List[Path]) -> Dict[str, Path]:
    """
    Bouw een index van bestandsnamen naar hun volledige paden.
    
    Args:
        files: Lijst van bestandspaden
        
    Returns:
        Dictionary met bestandsnaam als key en pad als value
    """
    file_index = {}
    
    for file_path in files:
        filename = file_path.name
        if filename in file_index:
            print(f"⚠️  WAARSCHUWING: Dubbele bestandsnaam gevonden: {filename}")
            print(f"   Bestaand: {file_index[filename]}")
            print(f"   Nieuw: {file_path}")
        file_index[filename] = file_path
    
    return file_index


def get_snake_case_suggestions(files: List[Path]) -> List[Tuple[Path, str, str]]:
    """
    Genereer snake_case suggesties voor bestanden die niet al in snake_case zijn.
    
    Args:
        files: Lijst van bestandspaden
        
    Returns:
        Lijst van tuples (pad, huidige_naam, snake_case_naam)
    """
    suggestions = []
    
    for file_path in files:
        current_name = file_path.stem  # Naam zonder extensie
        extension = file_path.suffix
        snake_case_name = to_snake_case(current_name)
        
        # Alleen voorstellen als de naam daadwerkelijk verandert
        if current_name != snake_case_name:
            full_snake_name = f"{snake_case_name}{extension}"
            suggestions.append((file_path, file_path.name, full_snake_name))
    
    return suggestions


def find_references_in_file(file_path: Path, target_filename: str) -> List[Tuple[int, str]]:
    """
    Zoek referenties naar een bestandsnaam in een bestand.
    
    Args:
        file_path: Het bestand om te doorzoeken
        target_filename: De bestandsnaam om te zoeken
        
    Returns:
        Lijst van tuples (regel_nummer, regel_inhoud) waar referenties gevonden zijn
    """
    references = []
    target_stem = Path(target_filename).stem  # Naam zonder extensie
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Zoek naar verschillende soorten referenties
                patterns = [
                    rf'\b{re.escape(target_filename)}\b',  # Volledige bestandsnaam
                    rf'\b{re.escape(target_stem)}\b',      # Naam zonder extensie
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        references.append((line_num, line.strip()))
                        break  # Voorkom dubbele matches op dezelfde regel
                        
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"⚠️  Kan bestand niet lezen: {file_path} - {e}")
    
    return references


def find_all_references(all_files: List[Path], target_filename: str) -> Dict[Path, List[Tuple[int, str]]]:
    """
    Zoek alle referenties naar een bestandsnaam in alle bestanden.
    
    Args:
        all_files: Alle bestanden om te doorzoeken
        target_filename: De bestandsnaam om te zoeken
        
    Returns:
        Dictionary met bestandspad als key en lijst van referenties als value
    """
    all_references = {}
    
    for file_path in all_files:
        references = find_references_in_file(file_path, target_filename)
        if references:
            all_references[file_path] = references
    
    return all_references


def update_references_in_file(file_path: Path, old_filename: str, new_filename: str) -> int:
    """
    Update referenties in een bestand van oude naar nieuwe bestandsnaam.
    
    Args:
        file_path: Het bestand om te updaten
        old_filename: De oude bestandsnaam
        new_filename: De nieuwe bestandsnaam
        
    Returns:
        Aantal gemaakte wijzigingen
    """
    old_stem = Path(old_filename).stem
    new_stem = Path(new_filename).stem
    changes_made = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Vervang volledige bestandsnamen
        content = re.sub(
            rf'\b{re.escape(old_filename)}\b',
            new_filename,
            content,
            flags=re.IGNORECASE
        )
        
        # Vervang bestandsnamen zonder extensie
        content = re.sub(
            rf'\b{re.escape(old_stem)}\b',
            new_stem,
            content,
            flags=re.IGNORECASE
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Tel het aantal wijzigingen
            changes_made = len(re.findall(rf'\b{re.escape(new_filename)}\b', content, re.IGNORECASE))
            changes_made += len(re.findall(rf'\b{re.escape(new_stem)}\b', content, re.IGNORECASE))
    
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"⚠️  Kan bestand niet updaten: {file_path} - {e}")
    
    return changes_made


def confirm_change(current_name: str, suggested_name: str) -> Tuple[bool, str]:
    """
    Vraag gebruiker om bevestiging voor een bestandsnaamwijziging.
    
    Args:
        current_name: Huidige bestandsnaam
        suggested_name: Voorgestelde nieuwe naam
        
    Returns:
        Tuple van (goedgekeurd, definitieve_naam)
    """
    print(f"\n📁 Bestand gevonden: {current_name}")
    print(f"🔄 Snake case voorstel: {suggested_name}")
    
    while True:
        choice = input("Goedkeuren? (j/n/c voor custom naam/q voor quit): ").lower().strip()
        
        if choice in ['j', 'ja', 'y', 'yes']:
            return True, suggested_name
        elif choice in ['n', 'nee', 'no']:
            return False, current_name
        elif choice == 'c':
            custom_name = input("Voer custom naam in: ").strip()
            if custom_name:
                print(f"🔄 Custom naam: {custom_name}")
                confirm_custom = input("Deze custom naam gebruiken? (j/n): ").lower().strip()
                if confirm_custom in ['j', 'ja', 'y', 'yes']:
                    return True, custom_name
            continue
        elif choice == 'q':
            print("🛑 Script gestopt door gebruiker")
            exit(0)
        else:
            print("❌ Ongeldige keuze. Gebruik j/n/c/q")


def process_file_rename(file_path: Path, new_name: str, all_files: List[Path]) -> Tuple[bool, Path]:
    """
    Verwerk de hernoaming van een bestand en update alle referenties.
    
    Args:
        file_path: Het huidige bestandspad
        new_name: De nieuwe bestandsnaam
        all_files: Alle bestanden voor referentie updates
        
    Returns:
        Tuple van (succes, nieuw_bestandspad)
    """
    old_name = file_path.name
    new_path = file_path.parent / new_name
    
    # Controleer of doelbestand al bestaat
    if new_path.exists() and new_path != file_path:
        print(f"❌ Fout: Doelbestand bestaat al: {new_path}")
        return False, file_path
    
    # Skip als geen wijziging nodig
    if old_name == new_name:
        print(f"ℹ️  Geen wijziging nodig voor: {old_name}")
        return True, file_path
    
    try:
        # Zoek eerst alle referenties
        print(f"🔍 Zoeken naar referenties voor: {old_name}")
        references = find_all_references(all_files, old_name)
        
        if references:
            print(f"📋 Gevonden referenties in {len(references)} bestanden:")
            for ref_file, ref_lines in references.items():
                print(f"   📄 {ref_file.name}: {len(ref_lines)} referenties")
                for line_num, line_content in ref_lines[:3]:  # Toon max 3 voorbeelden
                    print(f"      Regel {line_num}: {line_content[:80]}")
                if len(ref_lines) > 3:
                    print(f"      ... en {len(ref_lines) - 3} meer")
        
        # Hernoem het bestand
        print(f"📝 Hernoemen: {old_name} → {new_name}")
        file_path.rename(new_path)
        
        # Update alle referenties
        total_changes = 0
        for ref_file in references:
            changes = update_references_in_file(ref_file, old_name, new_name)
            if changes > 0:
                print(f"   ✅ {ref_file.name}: {changes} referenties bijgewerkt")
                total_changes += changes
        
        if total_changes > 0:
            print(f"✅ Totaal {total_changes} referenties bijgewerkt in {len(references)} bestanden")
        else:
            print("ℹ️  Geen referenties gevonden om bij te werken")
        
        return True, new_path
        
    except OSError as e:
        print(f"❌ Fout bij hernoemen van {old_name}: {e}")
        return False, file_path


def rebuild_file_lists(scan_dir: Path) -> Tuple[List[Path], Dict[str, Path]]:
    """
    Bouw de bestandslijst en index opnieuw op na wijzigingen.
    
    Args:
        scan_dir: De directory om opnieuw te scannen
        
    Returns:
        Tuple van (robot_files, file_index)
    """
    print("🔄 Bestandslijst opnieuw opbouwen...")
    robot_files = find_robot_files(scan_dir)
    file_index = build_file_index(robot_files)
    return robot_files, file_index


def main():
    """Hoofdfunctie van het script."""
    parser = argparse.ArgumentParser(
        description="Converteer Robot Framework bestanden naar snake_case en update referenties",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  %(prog)s /path/to/robot/project
  %(prog)s . --dry-run
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory om te scannen voor .robot en .resource bestanden'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Toon alleen wat er zou gebeuren zonder daadwerkelijke wijzigingen'
    )
    
    args = parser.parse_args()
    
    # Valideer directory
    scan_dir = Path(args.directory).resolve()
    if not scan_dir.exists():
        print(f"❌ Directory bestaat niet: {scan_dir}")
        return
    
    if not scan_dir.is_dir():
        print(f"❌ Pad is geen directory: {scan_dir}")
        return
    
    print(f"🔍 Scannen van directory: {scan_dir}")
    
    # Zoek alle Robot Framework bestanden
    robot_files, file_index = rebuild_file_lists(scan_dir)
    
    if not robot_files:
        print("ℹ️  Geen .robot of .resource bestanden gevonden")
        return
    
    print(f"📁 Gevonden {len(robot_files)} Robot Framework bestanden")
    
    # Genereer snake_case suggesties
    suggestions = get_snake_case_suggestions(robot_files)
    
    if not suggestions:
        print("✅ Alle bestanden zijn al in snake_case formaat!")
        return
    
    print(f"\n🔄 {len(suggestions)} bestanden kunnen worden geconverteerd naar snake_case:")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODUS - Geen wijzigingen worden uitgevoerd\n")
        for file_path, current_name, suggested_name in suggestions:
            print(f"📁 {current_name} → {suggested_name}")
        return
    
    # Verwerk elk voorstel
    successful_renames = 0
    total_suggestions = len(suggestions)
    processed_files = set()  # Houd bij welke bestanden al verwerkt zijn
    
    # Blijf processen totdat alle suggesties zijn afgehandeld
    while suggestions:
        current_suggestion = suggestions.pop(0)  # Neem het eerste voorstel
        file_path, current_name, suggested_name = current_suggestion
        
        # Skip als dit bestand al verwerkt is (kan gebeuren na herbouw)
        if str(file_path) in processed_files:
            continue
            
        approved, final_name = confirm_change(current_name, suggested_name)
        
        if approved:
            success, new_file_path = process_file_rename(file_path, final_name, robot_files)
            if success:
                successful_renames += 1
                processed_files.add(str(file_path))  # Markeer originele pad als verwerkt
                processed_files.add(str(new_file_path))  # Markeer nieuwe pad als verwerkt
                print(f"✅ Succesvol verwerkt: {current_name} → {final_name}")
                
                # Bouw bestandslijsten opnieuw op na succesvolle wijziging
                robot_files, file_index = rebuild_file_lists(scan_dir)
                
                # Genereer nieuwe suggesties voor eventuele resterende bestanden
                remaining_suggestions = get_snake_case_suggestions(robot_files)
                
                # Filter out already processed files from new suggestions
                filtered_suggestions = []
                for suggestion in remaining_suggestions:
                    suggestion_file_path, _, _ = suggestion
                    if str(suggestion_file_path) not in processed_files:
                        filtered_suggestions.append(suggestion)
                
                # Update suggestions list
                suggestions = filtered_suggestions
                
                if suggestions:
                    print(f"🔄 Nog {len(suggestions)} bestanden te verwerken na herbouw...")
                
            else:
                print(f"❌ Fout bij verwerken: {current_name}")
        else:
            processed_files.add(str(file_path))  # Markeer als overgeslagen
            print(f"⏭️  Overgeslagen: {current_name}")
    
    print(f"\n🎉 Voltooid! {successful_renames} van {total_suggestions} bestanden succesvol verwerkt")


if __name__ == "__main__":
    main()
