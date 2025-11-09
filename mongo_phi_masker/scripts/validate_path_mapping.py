#!/usr/bin/env python3
"""
Validate PATH_MAPPING against actual collection configuration files.

This script identifies:
1. Orphaned PATH_MAPPING entries (collections in PATH_MAPPING without config files)
2. Missing PATH_MAPPING entries (collections with config files but no PATH_MAPPING)
3. Case sensitivity issues across platforms

Usage:
    python scripts/validate_path_mapping.py
    python scripts/validate_path_mapping.py --fix  # Remove orphaned entries
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.collection_rule_mapping import PATH_MAPPING


def get_collections_with_configs():
    """Get list of collections that have config files."""
    config_dir = PROJECT_ROOT / "config" / "config_rules"
    config_files = list(config_dir.glob("config_*.json"))

    # Extract collection names from config file names
    collections = []
    for config_file in config_files:
        # config_Patients.json -> Patients
        collection_name = config_file.stem.replace("config_", "")
        collections.append(collection_name)

    return sorted(collections)


def validate_path_mapping():
    """Validate PATH_MAPPING against config files."""
    print("=" * 70)
    print("PATH_MAPPING Validation Report")
    print("=" * 70)
    print()

    # Get collections
    collections_with_configs = set(get_collections_with_configs())
    path_mapping_collections = set(PATH_MAPPING.keys())

    # Find orphaned entries
    orphaned = path_mapping_collections - collections_with_configs

    # Find missing entries
    missing = collections_with_configs - path_mapping_collections

    # Report results
    print(f"Collections with config files: {len(collections_with_configs)}")
    print(f"Collections in PATH_MAPPING:   {len(path_mapping_collections)}")
    print()

    if orphaned:
        print(f"❌ Orphaned PATH_MAPPING entries ({len(orphaned)}):")
        print("   (Collections in PATH_MAPPING without config files)")
        print()
        for collection in sorted(orphaned):
            print(f"   - {collection}")
        print()
    else:
        print("✅ No orphaned PATH_MAPPING entries found")
        print()

    if missing:
        print(f"⚠️  Missing PATH_MAPPING entries ({len(missing)}):")
        print("   (Collections with config files but no PATH_MAPPING)")
        print()
        for collection in sorted(missing):
            print(f"   - {collection}")
        print()
    else:
        print("✅ All collections with config files have PATH_MAPPING entries")
        print()

    # Case sensitivity check
    print("Case Sensitivity Check:")
    lower_to_original = {}
    case_conflicts = []

    for collection in path_mapping_collections | collections_with_configs:
        lower = collection.lower()
        if lower in lower_to_original:
            case_conflicts.append((lower_to_original[lower], collection))
        else:
            lower_to_original[lower] = collection

    if case_conflicts:
        print(f"❌ Case conflicts found ({len(case_conflicts)}):")
        for orig, conflict in case_conflicts:
            print(f"   - {orig} vs {conflict}")
        print()
    else:
        print("✅ No case sensitivity issues found")
        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    if orphaned or missing or case_conflicts:
        print("❌ Validation FAILED")
        print()
        if orphaned:
            print(f"   - {len(orphaned)} orphaned PATH_MAPPING entries")
        if missing:
            print(f"   - {len(missing)} missing PATH_MAPPING entries")
        if case_conflicts:
            print(f"   - {len(case_conflicts)} case sensitivity conflicts")
        return False
    else:
        print("✅ Validation PASSED")
        print("   All PATH_MAPPING entries are valid and in sync with config files")
        return True


def generate_pruned_path_mapping():
    """Generate PATH_MAPPING with orphaned entries removed."""
    collections_with_configs = set(get_collections_with_configs())

    pruned = {
        collection: mapping for collection, mapping in PATH_MAPPING.items() if collection in collections_with_configs
    }

    return pruned


def fix_path_mapping():
    """Remove orphaned PATH_MAPPING entries."""
    print("=" * 70)
    print("Fixing PATH_MAPPING")
    print("=" * 70)
    print()

    collections_with_configs = set(get_collections_with_configs())
    path_mapping_collections = set(PATH_MAPPING.keys())
    orphaned = path_mapping_collections - collections_with_configs

    if not orphaned:
        print("✅ No orphaned entries to remove")
        return

    print(f"Removing {len(orphaned)} orphaned entries...")
    print()

    # Read the file
    mapping_file = PROJECT_ROOT / "config" / "collection_rule_mapping.py"
    content = mapping_file.read_text()

    # Find PATH_MAPPING section
    start_marker = "PATH_MAPPING = {"
    start_idx = content.find(start_marker)

    if start_idx == -1:
        print("❌ ERROR: Could not find PATH_MAPPING in file")
        return

    # Find the closing brace
    brace_count = 0
    end_idx = start_idx + len(start_marker)

    for i in range(start_idx + len(start_marker), len(content)):
        if content[i] == "{":
            brace_count += 1
        elif content[i] == "}":
            if brace_count == 0:
                end_idx = i + 1
                break
            brace_count -= 1

    # Generate new PATH_MAPPING
    pruned = generate_pruned_path_mapping()

    # Format the new PATH_MAPPING
    new_mapping_lines = ["PATH_MAPPING = {"]

    for i, (collection, mapping) in enumerate(sorted(pruned.items())):
        # Add collection comment
        new_mapping_lines.append(f"    # {collection} collection")
        new_mapping_lines.append(f'    "{collection}": {{')

        # Add field mappings
        for field, path in sorted(mapping.items()):
            new_mapping_lines.append(f'        "{field}": "{path}",')

        # Close collection
        if i < len(pruned) - 1:
            new_mapping_lines.append("    },")
        else:
            new_mapping_lines.append("    }")

    new_mapping_lines.append("}")

    new_mapping_str = "\n".join(new_mapping_lines)

    # Replace in content
    new_content = content[:start_idx] + new_mapping_str + content[end_idx:]

    # Write back
    mapping_file.write_text(new_content)

    print(f"✅ Removed {len(orphaned)} orphaned entries from PATH_MAPPING")
    print()
    print("Removed collections:")
    for collection in sorted(orphaned):
        print(f"   - {collection}")
    print()
    print(f"Updated: {mapping_file}")


def main():
    parser = argparse.ArgumentParser(description="Validate PATH_MAPPING against collection config files")
    parser.add_argument("--fix", action="store_true", help="Remove orphaned PATH_MAPPING entries")

    args = parser.parse_args()

    if args.fix:
        fix_path_mapping()
        print()
        print("Re-validating after fix...")
        print()
        validate_path_mapping()
    else:
        success = validate_path_mapping()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
