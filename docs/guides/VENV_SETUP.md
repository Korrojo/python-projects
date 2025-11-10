# Virtual Environment Setup Scripts

Automated scripts to create and activate Python virtual environments across different operating systems.

## Scripts Overview

| Script             | Platform                       | Purpose                                  |
| ------------------ | ------------------------------ | ---------------------------------------- |
| `install_venv.sh`  | Linux/macOS/Windows (Git Bash) | Detects Python versions and creates venv |
| `install_venv.ps1` | Windows (PowerShell)           | PowerShell version of installer          |
| `activate_venv.sh` | Linux/macOS/Windows (Git Bash) | Smart venv activator                     |

## Features

✅ **Auto-detects OS** - Works on Windows, macOS, and Linux\
✅ **Finds all Python versions** - Scans system for installed
Python\
✅ **Interactive selection** - Choose your preferred Python version\
✅ **Validates installation** - Confirms venv
uses correct Python\
✅ **Python 3.11 highlighting** - Recommends Python 3.11 (repository standard)\
✅ **Safety checks**
\- Warns before overwriting existing venv\
✅ **Cross-platform** - Same workflow on all platforms

## Quick Start

### Option 1: Bash Script (Recommended for Git Bash, Linux, macOS)

```bash
# 1. Run installer
./install_venv.sh

# 2. Activate venv (must use 'source')
source ./activate_venv.sh

# 3. Install dependencies
pip install -r requirements.txt
pip install -e ./common_config
```

### Option 2: PowerShell (Windows)

```powershell
# 1. Run installer
.\install_venv.ps1

# 2. Activate venv
.\.venv311\Scripts\Activate.ps1  # Adjust for your Python version

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .\common_config
```

## Usage Details

### install_venv.sh / install_venv.ps1

**What it does:**

1. Detects your operating system
1. Searches for all installed Python versions
1. Displays available versions with recommendations
1. Creates virtual environment with selected version
1. Verifies installation

**Example output:**

```
=== Python Virtual Environment Installer ===

Detected OS: Windows

Searching for Python installations...

✓ Found py launcher (Windows)
  Found: Python 3.11.5 (py -3.11)
  Found: Python 3.12.0 (py -3.12)
  Found: Python 3.14.0 (py -3.14)

Found 3 Python installation(s):

  1) Python 3.11.5 (RECOMMENDED) - py -3.11
  2) Python 3.12.0 - py -3.12
  3) Python 3.14.0 - py -3.14

Select Python version (1-3) [default: 1]: 1

Selected: Python 3.11.5
Path: py -3.11

Creating virtual environment: .venv311
✓ Virtual environment created successfully!

Verifying virtual environment...
✓ Virtual environment Python version: 3.11.5
✓ Version verified!

=== Installation Complete! ===

Virtual environment created at: .venv311
```

**Options:**

- Interactive prompts guide you through selection
- Default choice is always option 1
- Warns if venv already exists
- Shows exact Python paths and versions

### activate_venv.sh

**What it does:**

1. Finds all virtual environments in current directory (`.venv*`)
1. Detects Python version in each venv
1. Activates selected venv
1. Verifies activation

**Example output:**

```
Activating: .venv311 (Python 3.11.5)

✓ Virtual environment activated!

Python version: Python 3.11.5
Python path: F:/ubiquityMongo_phiMasking/python/.venv311/Scripts/python

To deactivate, run: deactivate
```

**Important:** Must be run with `source`:

```bash
source ./activate_venv.sh  # ✓ Correct
./activate_venv.sh          # ✗ Won't work - creates subshell
```

## Troubleshooting

### "No Python installations found"

**Cause:** Python is not installed or not in PATH

**Solution:**

- **Windows:** Install from <https://www.python.org/downloads/windows/>
  - ✓ Check "Add Python to PATH" during installation
  - Or use `py` launcher (comes with Python 3.3+)
- **macOS:** `brew install python@3.11`
- **Linux:** `sudo apt install python3.11` (Debian/Ubuntu)

### "Failed to create virtual environment"

**Cause:** venv module not installed or insufficient permissions

**Solution:**

```bash
# Install venv module (if missing)
# Debian/Ubuntu
sudo apt install python3.11-venv

# Verify permissions
ls -la  # Should have write access to current directory
```

### "venv version differs from selected"

**Cause:** Python launcher redirecting to different version

**Solution:**

- Check `pyvenv.cfg` in venv directory to see actual Python
- Recreate venv using direct path instead of `py` launcher
- Example: Use `C:\Python311\python.exe` instead of `py -3.11`

### Virtual environment not activating (Git Bash)

**Cause:** Not using `source` command

**Solution:**

```bash
source ./activate_venv.sh  # ✓ Correct
./activate_venv.sh          # ✗ Won't work
```

### PowerShell execution policy error

**Cause:** Script execution disabled

**Solution:**

```powershell
# Check current policy
Get-ExecutionPolicy

# Enable script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run installer
.\install_venv.ps1
```

## Python Version Strategy

This repository **requires Python 3.11** for consistency:

| Python Version | Status               | Notes                                       |
| -------------- | -------------------- | ------------------------------------------- |
| 3.11.x         | ✅ **RECOMMENDED**   | Repository standard, all projects tested    |
| 3.10.x         | ⚠️ May work          | Not officially supported                    |
| 3.12.x         | ⚠️ May work          | Some packages may have compatibility issues |
| 3.14.x         | ❌ **NOT SUPPORTED** | Breaking changes, package incompatibility   |

**Why Python 3.11?**

- All documentation assumes 3.11
- Dependencies tested with 3.11
- CI/CD pipeline uses 3.11
- Consistent behavior across team
- `.venv311/` naming convention

## Migration from Old venv

If you have an existing venv with wrong Python version:

```bash
# 1. Deactivate current venv
deactivate

# 2. Run installer (will prompt to remove old venv)
./install_venv.sh

# 3. Select Python 3.11 when prompted

# 4. Activate new venv
source ./activate_venv.sh

# 5. Reinstall dependencies
pip install -r requirements.txt
pip install -e ./common_config
```

## Manual Alternative

If scripts don't work, create venv manually:

**Git Bash / Linux / macOS:**

```bash
# Using py launcher (Windows)
py -3.11 -m venv .venv311

# Using direct Python path
python3.11 -m venv .venv311

# Activate
source .venv311/bin/activate
```

**PowerShell:**

```powershell
# Using py launcher
py -3.11 -m venv .venv311

# Using direct path
C:\Python311\python.exe -m venv .venv311

# Activate
.\.venv311\Scripts\Activate.ps1
```

## See Also

- [Main README](README.md) - Repository overview
- [common_config README](common_config/README.md) - Shared configuration
- [LINTING.md](LINTING.md) - Code quality tools
