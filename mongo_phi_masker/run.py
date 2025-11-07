#!/usr/bin/env python3
"""
MongoDB PHI Masker - Main entry point

This is a wrapper around masking.py for backward compatibility.
All functionality is provided by masking.py.

Usage:
    python run.py [masking.py arguments]
    python run.py info  # Show tool information

Examples:
    python run.py --help
    python run.py info
    python run.py --config config.json --src-env LOCL --collection Patients
"""

if __name__ == "__main__":
    import sys

    # Handle 'info' subcommand for backward compatibility with CI smoke tests
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        print("MongoDB PHI Masker")
        print("=" * 50)
        print("Production-ready HIPAA-compliant PHI/PII masking tool")
        print("")
        print("Features:")
        print("  • 9 production-ready collections")
        print("  • Automated orchestration with validation")
        print("  • Windows Task Scheduler support")
        print("  • Email notifications")
        print("  • Comprehensive logging")
        print("")
        print("For help: python run.py --help")
        sys.exit(0)

    # Import and execute masking.py's main function
    from masking import main

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
