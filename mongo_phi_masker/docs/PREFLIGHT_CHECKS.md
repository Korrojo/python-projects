# Pre-Flight Checks

The Pre-Flight Check system validates all configurations and dependencies before running the PHI masking pipeline. It
performs comprehensive validation across multiple categories to prevent runtime errors and ensure smooth execution.

## Features

- **Comprehensive Validation**: Checks configuration files, environment variables, database connectivity, file
  permissions, and Python environment
- **Detailed Error Reporting**: Clear error messages with specific recommendations for fixing issues
- **Automatic Fixing**: Optional `--fix` mode to automatically create missing directories
- **Severity Levels**: Distinguishes between errors (must fix) and warnings (should fix)
- **Verbose Mode**: Detailed output for debugging configuration issues
- **Exit Codes**: Returns appropriate exit codes for CI/CD integration

## Validation Categories

### 1. Python Environment

- **Python Version**: Validates Python >= 3.11
- **Virtual Environment**: Checks if virtual environment is active
- **Required Packages**: Verifies pymongo, python-dotenv, psutil are installed

### 2. Configuration Files

- **Config File Exists**: Checks `config/config_rules/config_{collection}.json` exists
- **Valid JSON**: Validates configuration file has valid JSON syntax
- **Required Sections**: Verifies mongodb, processing, masking sections are present
- **Masking Rules File**: Confirms referenced masking rules file exists

### 3. Environment Variables

- **Environment File**: Checks `.env` file exists
- **Required Variables**: Validates all required MongoDB connection variables are set
- **URI Construction**: Tests that MongoDB URIs can be constructed from variables

### 4. Collection Definition

- **Rule Mapping**: Verifies collection is defined in `COLLECTION_RULE_MAPPING`
- **PHI Fields**: Confirms PHI fields are defined for the collection

### 5. File System Permissions

- **Writable Directories**: Validates logs, reports, and checkpoints directories are writable
- **Auto-Create**: Can automatically create missing directories with `--fix` mode

### 6. Database Connectivity

- **Source Connection**: Tests connection to source MongoDB database
- **Source Collection**: Verifies source collection exists and document count
- **Destination Connection**: Tests connection to destination MongoDB database
- **Write Permissions**: Confirms write access to destination database

## Usage

### Basic Validation

Validate configuration for a specific collection:

```bash
python scripts/preflight_check.py --collection Container
```

### Verbose Output

Show all checks including passing ones:

```bash
python scripts/preflight_check.py --collection Patients --verbose
```

### Auto-Fix Mode

Automatically create missing directories:

```bash
python scripts/preflight_check.py --collection Tasks --fix
```

### Custom Environment File

Use a specific environment file:

```bash
python scripts/preflight_check.py --collection StaffAvailability --env .env.production
```

## Output

### Successful Validation

```
======================================================================
MongoDB PHI Masker - Pre-Flight Checks
======================================================================
Collection: Container
Environment File: .env

✓ Python Environment
✓ Configuration Files
✓ Environment Variables
✓ Collection Definition
✓ File System Permissions
✓ Database Connectivity

======================================================================
Pre-Flight Check Summary
======================================================================

✓ All pre-flight checks passed!

You can proceed with masking:
  python masking.py --config config/config_rules/config_Container.json
======================================================================
```

### Failed Validation

```
======================================================================
MongoDB PHI Masker - Pre-Flight Checks
======================================================================
Collection: Patients
Environment File: .env

✗ Python Environment
  ✗ Package: psutil: Not installed
    → Install package: pip install psutil

✗ Configuration Files
  ✗ Config File Exists: File not found: config/config_rules/config_Patients.json
    → Create config file at config/config_rules/config_Patients.json

✗ Environment Variables
  ✗ Env Var: MONGO_SOURCE_DB: Not set: Source database name
    → Set MONGO_SOURCE_DB in .env

✓ Collection Definition
✓ File System Permissions
✗ Database Connectivity
  ✗ Source Database Connection: Connection failed
    → Check MongoDB is running and connection settings

======================================================================
Pre-Flight Check Summary
======================================================================

✗ 5 error(s) found
⚠ 0 warning(s) found

Please fix the issues above before running masking.
======================================================================
```

### Verbose Output

```
======================================================================
MongoDB PHI Masker - Pre-Flight Checks
======================================================================
Collection: Container
Environment File: .env

✓ Python Environment
  ✓ Python Version: Python 3.11.9
  ✓ Virtual Environment: Active (/Users/user/.venv311)
  ✓ Package: pymongo: Installed
  ✓ Package: python-dotenv: Installed
  ✓ Package: psutil: Installed

✓ Configuration Files
  ✓ Config File Exists: config/config_rules/config_Container.json
  ✓ Config File Valid JSON: Valid JSON structure
  ✓ Config Section: mongodb: Present
  ✓ Config Section: processing: Present
  ✓ Config Section: masking: Present
  ✓ Masking Rules File: config/masking_rules/rules_container.json

✓ Environment Variables
  ✓ Environment File Exists: .env
  ✓ Env Var: MONGO_SOURCE_HOST: localhost
  ✓ Env Var: MONGO_SOURCE_PORT: 27017
  ✓ Env Var: MONGO_SOURCE_DB: UbiquityPhiMasked
  ✓ Env Var: MONGO_DEST_HOST: localhost
  ✓ Env Var: MONGO_DEST_PORT: 27017
  ✓ Env Var: MONGO_DEST_DB: UbiquityPhiTest
  ✓ Source MongoDB URI: URI constructable
  ✓ Destination MongoDB URI: URI constructable

✓ Collection Definition
  ✓ Collection in Rule Mapping: Mapped to rule group: rule_group_1
  ✓ PHI Fields Defined: 12 PHI fields defined

✓ File System Permissions
  ✓ Directory: logs: Writable (Log files)
  ✓ Directory: reports: Writable (Validation reports)
  ✓ Directory: checkpoints: Writable (Processing checkpoints)

✓ Database Connectivity
  ✓ Source Database Connection: Connected successfully
  ✓ Source Collection Exists: UbiquityPhiMasked.Container (3,456 documents)
  ✓ Destination Database Connection: Connected successfully
  ✓ Destination Write Permissions: Write access confirmed for UbiquityPhiTest

======================================================================
```

## Command-Line Options

| Option           | Required | Default | Description                                        |
| ---------------- | -------- | ------- | -------------------------------------------------- |
| `--collection`   | Yes      | -       | Collection name to validate                        |
| `--env`          | No       | `.env`  | Path to environment file                           |
| `--verbose`/`-v` | No       | False   | Enable verbose output (show all checks)            |
| `--fix`          | No       | False   | Attempt to fix issues automatically (creates dirs) |

## Exit Codes

| Code | Meaning | Description               |
| ---- | ------- | ------------------------- |
| 0    | Success | All checks passed         |
| 1    | Failure | One or more checks failed |

Use exit codes in scripts:

```bash
if python scripts/preflight_check.py --collection Container; then
    echo "Pre-flight checks passed, proceeding with masking..."
    python masking.py --config config/config_rules/config_Container.json
else
    echo "Pre-flight checks failed, aborting"
    exit 1
fi
```

## Typical Workflow

### Development Workflow

```bash
# 1. Check configuration is valid
python scripts/preflight_check.py --collection Patients --verbose

# 2. Fix any issues identified
# ... make necessary changes ...

# 3. Re-run validation
python scripts/preflight_check.py --collection Patients

# 4. If all checks pass, run masking
python masking.py --config config/config_rules/config_Patients.json
```

### CI/CD Integration

```yaml
# .github/workflows/masking-validation.yml
- name: Pre-Flight Checks
  run: |
    python scripts/preflight_check.py --collection Container --verbose
    if [ $? -ne 0 ]; then
      echo "Pre-flight checks failed"
      exit 1
    fi

- name: Run Masking
  run: |
    python masking.py --config config/config_rules/config_Container.json
```

### Automated Script

```bash
#!/bin/bash
# run_masking_with_validation.sh

COLLECTION=$1

if [ -z "$COLLECTION" ]; then
    echo "Usage: $0 <collection_name>"
    exit 1
fi

echo "Running pre-flight checks for $COLLECTION..."
python scripts/preflight_check.py --collection $COLLECTION --verbose

if [ $? -eq 0 ]; then
    echo "✓ Pre-flight checks passed!"
    echo "Starting masking process..."
    python masking.py --config config/config_rules/config_${COLLECTION}.json
else
    echo "✗ Pre-flight checks failed. Please fix the issues above."
    exit 1
fi
```

## Common Issues and Solutions

### Python Version Too Old

**Symptom**:

```
✗ Python Version: Python 3.10.5 (< 3.11)
  → Upgrade to Python 3.11 or higher
```

**Solution**: Install Python 3.11+:

```bash
# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Update virtual environment
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

### Missing Environment File

**Symptom**:

```
✗ Environment File Exists: File not found: .env
  → Copy .env.example to .env and configure
```

**Solution**:

```bash
cp .env.example .env
# Edit .env and fill in your MongoDB connection details
nano .env
```

### Missing Configuration File

**Symptom**:

```
✗ Config File Exists: File not found: config/config_rules/config_Patients.json
  → Create config file at config/config_rules/config_Patients.json
```

**Solution**: Create configuration file based on template:

```bash
# Copy from existing collection
cp config/config_rules/config_Container.json config/config_rules/config_Patients.json

# Edit for your collection
nano config/config_rules/config_Patients.json
```

### Collection Not Defined

**Symptom**:

```
✗ Collection in Rule Mapping: Collection 'MyCollection' not found in COLLECTION_RULE_MAPPING
  → Add 'MyCollection' to config/collection_rule_mapping.py
```

**Solution**: Add collection to `config/collection_rule_mapping.py`:

```python
COLLECTION_RULE_MAPPING = {
    # ... existing collections ...
    "MyCollection": "rule_group_1",  # Choose appropriate rule group
}
```

### Database Connection Failed

**Symptom**:

```
✗ Source Database Connection: Connection failed: [Errno 61] Connection refused
  → Check MongoDB is running and connection settings
```

**Solutions**:

1. Start MongoDB if not running:

```bash
# macOS with Homebrew
brew services start mongodb-community

# Linux with systemd
sudo systemctl start mongod

# Docker
docker start mongodb
```

2. Check connection settings in `.env`:

```bash
# Verify host and port
MONGO_SOURCE_HOST=localhost
MONGO_SOURCE_PORT=27017

# Or use full URI
MONGO_SOURCE_URI=mongodb://localhost:27017/
```

3. Test connection manually:

```bash
mongosh mongodb://localhost:27017/
```

### Missing Directories

**Symptom**:

```
✗ Directory: logs: Directory does not exist
  → Create directory: mkdir -p logs (or use --fix)
```

**Solution**: Use `--fix` mode:

```bash
python scripts/preflight_check.py --collection Container --fix
```

Or create manually:

```bash
mkdir -p logs reports checkpoints
```

### Write Permission Denied

**Symptom**:

```
✗ Directory: logs: Not writable
  → Fix permissions: chmod u+w logs
```

**Solution**:

```bash
chmod u+w logs reports checkpoints
# Or give full permissions
chmod 755 logs reports checkpoints
```

### Package Not Installed

**Symptom**:

```
✗ Package: psutil: Not installed
  → Install package: pip install psutil
```

**Solution**:

```bash
pip install psutil python-dotenv pymongo
# Or install all requirements
pip install -r requirements.txt
```

## Advanced Usage

### Multiple Collections Validation

Validate multiple collections in a script:

```bash
#!/bin/bash
# validate_all_collections.sh

COLLECTIONS=("Container" "Patients" "Tasks" "StaffAvailability")

for collection in "${COLLECTIONS[@]}"; do
    echo "Validating $collection..."
    python scripts/preflight_check.py --collection $collection
    if [ $? -ne 0 ]; then
        echo "✗ Validation failed for $collection"
        exit 1
    fi
done

echo "✓ All collections validated successfully"
```

### Pre-Commit Hook

Add pre-flight checks to git pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Only run if config files changed
if git diff --cached --name-only | grep -q "config/"; then
    echo "Config files changed, running pre-flight checks..."

    # Get collections from changed files
    for file in $(git diff --cached --name-only | grep "config/config_rules/config_"); do
        collection=$(basename $file | sed 's/config_//' | sed 's/.json//')
        echo "Checking $collection..."

        python scripts/preflight_check.py --collection $collection
        if [ $? -ne 0 ]; then
            echo "✗ Pre-flight checks failed for $collection"
            echo "Fix issues before committing"
            exit 1
        fi
    done
fi
```

### Integration with Monitoring

Send validation results to monitoring system:

```python
#!/usr/bin/env python3
"""Send pre-flight check results to monitoring system."""

import subprocess
import sys
import requests

def run_preflight(collection):
    """Run pre-flight checks and return result."""
    result = subprocess.run(
        ["python", "scripts/preflight_check.py", "--collection", collection],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout

def send_to_monitoring(collection, passed, output):
    """Send results to monitoring system."""
    requests.post(
        "https://monitoring.example.com/preflight",
        json={
            "collection": collection,
            "passed": passed,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    collection = sys.argv[1]
    passed, output = run_preflight(collection)
    send_to_monitoring(collection, passed, output)
    sys.exit(0 if passed else 1)
```

## Best Practices

1. **Always Run Before Masking**: Never skip pre-flight checks before running the masking pipeline
1. **Use Verbose Mode for Debugging**: When troubleshooting, use `--verbose` to see all checks
1. **Fix Errors First**: Address all errors before proceeding; warnings can be addressed later
1. **Integrate with CI/CD**: Add pre-flight checks to your deployment pipeline
1. **Document Custom Configuration**: If you add custom checks, document them in your project
1. **Regular Validation**: Run pre-flight checks regularly, not just before masking
1. **Version Control**: Keep `.env.example` in version control, never commit `.env`
1. **Test Connectivity**: Run connectivity checks after any infrastructure changes

## Extending Pre-Flight Checks

### Adding Custom Checks

You can extend the `PreFlightChecker` class to add custom validation:

```python
# custom_preflight.py
from scripts.preflight_check import PreFlightChecker, CheckCategory, CheckResult

class CustomPreFlightChecker(PreFlightChecker):
    """Extended pre-flight checker with custom validations."""

    def run_all_checks(self):
        """Run all checks including custom ones."""
        super().run_all_checks()
        self.check_custom_requirements()
        return all(category.passed for category in self.categories)

    def check_custom_requirements(self):
        """Add your custom validation logic."""
        category = CheckCategory(name="Custom Requirements")

        # Example: Check disk space
        import shutil
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024 ** 3)

        if free_gb > 10:
            category.checks.append(CheckResult(
                name="Disk Space",
                passed=True,
                message=f"{free_gb:.1f} GB available",
                severity="info"
            ))
        else:
            category.checks.append(CheckResult(
                name="Disk Space",
                passed=False,
                message=f"Only {free_gb:.1f} GB available",
                recommendation="Free up disk space (need > 10 GB)",
                severity="warning"
            ))

        self.categories.append(category)
```

## Troubleshooting

### Script Fails to Import Modules

**Problem**: `ImportError: cannot import name 'get_phi_fields'`

**Solution**: Ensure you're running from project root:

```bash
cd /path/to/mongo_phi_masker
python scripts/preflight_check.py --collection Container
```

### Virtual Environment Not Detected

**Problem**: Warning about missing virtual environment

**Solution**: Activate virtual environment:

```bash
source .venv311/bin/activate  # Unix/macOS
# or
.venv311\Scripts\activate  # Windows
```

### Database Connection Timeout

**Problem**: Connection tests timing out

**Solution**: Increase timeout or check network:

```bash
# Test connection manually
mongosh mongodb://localhost:27017/ --eval "db.adminCommand('ping')"

# Check network
ping localhost
```

## Related Documentation

- [Test Data Export](TEST_DATA_EXPORT.md) - Exporting PHI-rich test data
- [Masking Validation](MASKING_VALIDATION.md) - Validating masking results
- [Performance Tracking](PERFORMANCE_TRACKING.md) - Monitoring pipeline performance
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Overall testing infrastructure

## Supported Collections

Works with all collections defined in `config/collection_rule_mapping.py` (70+ collections across 8 categories).

## Performance

Pre-flight checks are designed to be fast:

- Configuration checks: < 0.1s
- Environment checks: < 0.1s
- File system checks: < 0.1s
- Database connectivity: 1-5s (depends on network)

**Total runtime**: Typically 2-7 seconds for complete validation.
