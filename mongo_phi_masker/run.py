#!/usr/bin/env python3
"""
MongoDB PHI Masker - Main entry point

This is a wrapper around masking.py for backward compatibility.
All functionality is provided by masking.py.

Usage:
    python run.py [masking.py arguments]

Examples:
    python run.py --help
    python run.py --config config.json --src-env LOCL --collection Patients
"""

if __name__ == "__main__":
    # Import and execute masking.py's main function
    from masking import main
    import sys

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
