#!/usr/bin/env python3
"""
Setup script for Patient Data Extraction project.

This script sets up the project environment by:
1. Checking common framework availability
2. Creating necessary directories
3. Setting up configuration files
4. Testing the setup
"""

import shutil
import sys
from pathlib import Path


def check_common_framework():
    """Check if the common framework is available."""
    framework_path = Path("../common_project")
    if not framework_path.exists():
        print("❌ Common framework not found at ../common_project")
        print("Please ensure the common_project directory exists")
        return False

    required_paths = [
        framework_path / "src",
        framework_path / "requirements.txt",
        framework_path / "README.md",
    ]

    for path in required_paths:
        if not path.exists():
            print(f"❌ Required framework file missing: {path}")
            return False

    print("✅ Common framework found and validated")
    return True


def create_directories():
    """Create necessary project directories."""
    directories = ["config", "src", "output", "logs", "temp"]

    print("Creating project directories...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}/")


def setup_configuration():
    """Set up configuration files."""
    print("Setting up configuration files...")

    # Create .env from example if it doesn't exist
    env_file = Path("config/.env")
    env_example = Path("config/.env.example")

    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print("  ✅ Created config/.env from template")
        print("  ⚠️  Please update config/.env with your database connection details")
    elif env_file.exists():
        print("  ✅ config/.env already exists")

    # Check extraction config
    extraction_config = Path("config/extraction_config.json")
    if extraction_config.exists():
        print("  ✅ config/extraction_config.json exists")
    else:
        print("  ❌ config/extraction_config.json missing")
        return False

    return True


def test_imports():
    """Test if we can import the common framework."""
    print("Testing framework imports...")

    try:
        # Add common framework to path
        framework_path = Path("../common_project/src").resolve()
        sys.path.insert(0, str(framework_path))

        # Test imports
        from config.config_manager import ConfigManager
        from database.connection import MongoDBConnection
        from extraction.data_extractor import DataExtractor
        from output.data_exporter import DataExporter
        from utils.logger import get_logger

        # Mark imports as used to satisfy linters
        _ = (MongoDBConnection, DataExtractor, DataExporter, ConfigManager, get_logger)

        print("  ✅ All framework imports successful")
        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def test_project_imports():
    """Test if we can import project modules."""
    print("Testing project imports...")

    try:
        # Add paths
        framework_path = Path("../common_project/src").resolve()
        project_path = Path("src").resolve()
        sys.path.insert(0, str(framework_path))
        sys.path.insert(0, str(project_path))

        # Test project import
        from patient_extractor import MultiDatabaseConfigManager, PatientDataExtractor

        # Mark imports as used to satisfy linters
        _ = (PatientDataExtractor, MultiDatabaseConfigManager)

        print("  ✅ Project imports successful")
        return True

    except ImportError as e:
        print(f"  ❌ Project import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def show_next_steps():
    """Show next steps to the user."""
    print("\n" + "=" * 60)
    print("SETUP COMPLETED!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Update config/.env with your MongoDB connection details:")
    print("   - DB1_MONGODB_URI (for PatientId extraction)")
    print("   - DB1_DATABASE_NAME")
    print("   - DB2_MONGODB_URI (for patient details)")
    print("   - DB2_DATABASE_NAME")
    print()
    print("2. Test your configuration:")
    print("   python run_extraction.py --test-connections")
    print()
    print("3. Run the extraction:")
    print("   python run_extraction.py")
    print("   OR")
    print("   run_extraction.bat")
    print()
    print("4. For Windows Task Scheduler:")
    print("   Use: run_extraction.bat")
    print()
    print("📁 Output files will be saved to:")
    print("   - output/mo_patient_ids.csv")
    print("   - output/patient_details.csv")
    print("   - logs/extraction.log")


def main():
    """Main setup function."""
    print("=" * 60)
    print("Patient Data Extraction - Project Setup")
    print("=" * 60)

    # Check common framework
    if not check_common_framework():
        return 1

    # Create directories
    create_directories()

    # Setup configuration
    if not setup_configuration():
        return 1

    # Test imports
    if not test_imports():
        return 1

    # Test project imports
    if not test_project_imports():
        return 1

    # Show next steps
    show_next_steps()

    return 0


if __name__ == "__main__":
    sys.exit(main())
