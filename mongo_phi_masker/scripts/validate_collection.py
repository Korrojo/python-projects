#!/usr/bin/env python3
"""
Collection Configuration Validation Script

Validates that a collection has all required files before running orchestration.

Usage:
    python scripts/validate_collection.py --collection Patients
    python scripts/validate_collection.py --all
"""

import argparse
import json
import sys
from pathlib import Path


def validate_collection(collection_name: str, verbose: bool = True) -> bool:
    """
    Validate that a collection has all required configuration files.

    Returns:
        True if valid, False otherwise
    """
    issues = []
    warnings = []

    # Check 1: Config file exists
    config_file = Path(f"config/config_rules/config_{collection_name}.json")
    if not config_file.exists():
        issues.append(f"❌ Config file missing: {config_file}")
        return False  # Can't continue without config

    # Check 2: Config file is valid JSON
    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"❌ Config file has invalid JSON: {e}")
        return False

    # Check 3: Config has required fields
    required_fields = ["mongodb", "processing", "masking", "phi_collections"]
    for field in required_fields:
        if field not in config_data:
            issues.append(f"❌ Config missing required field: {field}")

    # Check 4: Rules file path is specified
    rules_path_str = config_data.get("masking", {}).get("rules_path", "")
    if not rules_path_str:
        issues.append("❌ No rules_path specified in config")
        return False

    # Check 5: Rules file exists
    rules_path = Path(rules_path_str)
    if not rules_path.exists():
        issues.append(f"❌ Rules file missing: {rules_path}")
    else:
        # Check 6: Rules file is valid JSON
        try:
            with open(rules_path, "r") as f:
                rules_data = json.load(f)

            # Check 7: Rules file has rules array
            if "rules" not in rules_data:
                issues.append("❌ Rules file missing 'rules' array")
            elif len(rules_data["rules"]) == 0:
                warnings.append("⚠️  Rules file has no masking rules defined")
        except json.JSONDecodeError as e:
            issues.append(f"❌ Rules file has invalid JSON: {e}")

    # Check 8: Collection name matches config
    phi_collections = config_data.get("phi_collections", [])
    if collection_name not in phi_collections:
        warnings.append(f"⚠️  Collection '{collection_name}' not in phi_collections array: {phi_collections}")

    # Print results
    if verbose:
        if issues:
            print(f"\n❌ {collection_name} - INVALID")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ {collection_name} - VALID")
            print(f"   Config: {config_file.name}")
            print(f"   Rules:  {rules_path.name}")

        if warnings:
            for warning in warnings:
                print(f"   {warning}")

    return len(issues) == 0


def validate_all_collections(verbose: bool = True) -> dict:
    """
    Validate all collections that have config files.

    Returns:
        Dict with 'valid' and 'invalid' collection lists
    """
    config_dir = Path("config/config_rules")

    valid = []
    invalid = []

    for config_file in sorted(config_dir.glob("config_*.json")):
        collection_name = config_file.stem.replace("config_", "")

        if validate_collection(collection_name, verbose=verbose):
            valid.append(collection_name)
        else:
            invalid.append(collection_name)

    return {"valid": valid, "invalid": invalid}


def main():
    parser = argparse.ArgumentParser(
        description="Validate collection configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--collection", help="Collection name to validate")
    group.add_argument("--all", action="store_true", help="Validate all collections")

    parser.add_argument("--quiet", action="store_true", help="Only show summary")

    args = parser.parse_args()

    if args.collection:
        # Validate single collection
        is_valid = validate_collection(args.collection, verbose=not args.quiet)

        if not args.quiet:
            print()

        sys.exit(0 if is_valid else 1)

    else:
        # Validate all collections
        results = validate_all_collections(verbose=not args.quiet)

        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"\n✅ Valid:   {len(results['valid'])} collections")
        print(f"❌ Invalid: {len(results['invalid'])} collections\n")

        if results["valid"]:
            print("Valid collections:")
            for name in results["valid"]:
                print(f"  • {name}")
            print()

        if results["invalid"]:
            print("Invalid collections:")
            for name in results["invalid"]:
                print(f"  • {name}")
            print()

        sys.exit(0 if len(results["invalid"]) == 0 else 1)


if __name__ == "__main__":
    main()
