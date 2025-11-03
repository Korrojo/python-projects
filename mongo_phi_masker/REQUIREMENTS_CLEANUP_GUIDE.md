# Requirements Cleanup Guide

**Date:** October 10, 2025

## Overview

This guide provides step-by-step instructions to clean up the project dependencies.

______________________________________________________________________

## 📋 Current Situation

- **Current requirements.txt**: 150+ packages (many unused)
- **Estimated bloat**: ~60 unused packages (~500 MB)
- **New structure**: Split into 3 focused files

______________________________________________________________________

## ✅ New Requirements Structure

### 1. **requirements-production.txt** (Production deployments)

- **Packages**: 35 essential packages
- **Use for**: Production servers, containers, minimal installs
- **Install**: `pip install -r requirements-production.txt`

### 2. **requirements-dev.txt** (Development)

- **Packages**: Production + 25 dev tools
- **Use for**: Local development, code quality, testing
- **Install**: `pip install -r requirements-dev.txt`

### 3. **requirements-viz.txt** (Visualization - Optional)

- **Packages**: Production + 11 visualization packages
- **Use for**: Running performance benchmarks, creating charts
- **Install**: `pip install -r requirements-viz.txt`

______________________________________________________________________

## 🚀 Migration Steps

### Step 1: Backup Current Environment

```powershell
# Save current environment state
pip freeze > requirements-backup-$(Get-Date -Format 'yyyyMMdd').txt

# Or copy the current file
Copy-Item requirements.txt requirements-backup.txt
```

### Step 2: Create New Virtual Environment (Recommended)

```powershell
# Create new clean environment
python -m venv venv-clean

# Activate it
.\venv-clean\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install New Requirements

```powershell
# For production use:
pip install -r requirements-production.txt

# For development (includes testing, linting, etc):
pip install -r requirements-dev.txt

# For visualization (if needed):
pip install -r requirements-viz.txt
```

### Step 4: Test the Application

```powershell
# Test basic functionality
python -m src.main --help

# Run tests (if you have them)
pytest

# Test a specific script
python scripts/check_env.py
```

### Step 5: Update Old requirements.txt (Optional)

If you want to keep backward compatibility temporarily:

```powershell
# Option A: Point to new production requirements
Copy-Item requirements-production.txt requirements.txt

# Option B: Add deprecation notice
@"
# DEPRECATED: Use requirements-production.txt, requirements-dev.txt, or requirements-viz.txt
# This file is kept for backward compatibility only
-r requirements-production.txt
"@ | Out-File requirements.txt
```

______________________________________________________________________

## 🗑️ Packages Being Removed

### Complete List of Removed Packages (60+)

#### Scientific Computing (NOT USED)

- scikit-learn==1.6.1
- scipy==1.15.2
- threadpoolctl==3.6.0
- joblib==1.4.2

#### PDF/HTML Generation (NOT USED)

- weasyprint==64.1
- tinycss2==1.4.0
- tinyhtml5==2.0.0
- pyphen==0.17.2
- cssselect2==0.8.0
- pydyf==0.11.0
- zopfli==0.2.3.post1
- Brotli==1.1.0

#### Interactive Visualization (NOT USED)

- bokeh==3.7.0

#### Jupyter/Notebook Ecosystem (NOT USED - 20+ packages)

- nbformat==5.10.4
- nbconvert==7.16.6
- nbclient==0.10.2
- mistune==3.1.3
- bleach==6.2.0
- defusedxml==0.7.1
- fastjsonschema==2.21.1
- jsonschema==4.23.0
- jsonschema-specifications==2024.10.1
- referencing==0.36.2
- rpds-py==0.23.1
- terminado==0.18.1
- Send2Trash==1.8.3
- simpervisor==1.0.0
- prometheus_client==0.21.1
- argon2-cffi==23.1.0
- argon2-cffi-bindings==21.2.0

#### Unused Web/Network

- urllib3==2.3.0
- sniffio==1.3.1
- anyio==4.9.0
- secure-smtplib==0.1.1
- beautifulsoup4==4.13.3
- soupsieve==2.6

#### Miscellaneous Unused

- narwhals==1.32.0
- overrides==7.7.0
- arrow==1.3.0
- fqdn==1.5.1
- isoduration==20.11.0
- jsonpointer==3.0.0
- python-json-logger==3.3.0
- rfc3339-validator==0.1.4
- rfc3986-validator==0.1.1
- uri-template==1.3.0
- webcolors==24.11.1
- webencodings==0.5.1
- websocket-client==1.8.0
- pyarrow==19.0.1
- Pygments==2.19.1
- ptyprocess==0.7.0
- pyzmq==26.3.0
- traitlets==5.14.3
- tornado==6.4.2
- cffi==1.17.1
- pycparser==2.22
- Jinja2==3.1.6
- MarkupSafe==3.0.2
- zipp==3.21.0
- importlib_metadata==8.6.1

______________________________________________________________________

## 🔍 Verification Checklist

After migration, verify these work:

### Core Functionality

- [ ] MongoDB connection works
- [ ] Configuration loading works
- [ ] Masking rules load correctly
- [ ] Document masking executes
- [ ] Logging functions properly

### Development Tools (if using requirements-dev.txt)

- [ ] pytest runs tests
- [ ] black formats code
- [ ] flake8 checks code
- [ ] mypy type checks

### Visualization (if using requirements-viz.txt)

- [ ] Performance benchmark script runs
- [ ] Visualization script generates charts

### Commands to Test

```powershell
# Test imports
python -c "import pymongo; print('MongoDB:', pymongo.__version__)"
python -c "from distributed import Client; print('Dask: OK')"
python -c "import psutil; print('Psutil: OK')"

# Test application
python -m src.main --help

# Test configuration
python scripts/check_env.py

# Run a simple test
python -c "from src.core.orchestrator import MaskingOrchestrator; print('Core modules: OK')"
```

______________________________________________________________________

## ⚠️ Troubleshooting

### Issue: Import errors after cleanup

**Solution**: Check if you're importing removed packages

```powershell
# Search for problematic imports
Get-ChildItem -Recurse -Filter "*.py" | Select-String "import (scikit|sklearn|scipy|bokeh|jupyter|weasyprint)"
```

### Issue: Application won't run

**Solution**: Verify you installed the right requirements

```powershell
pip list | Select-String "pymongo|distributed|psutil"
```

### Issue: Need a removed package

**Solution**: Add it to requirements-viz.txt or requirements-dev.txt

```powershell
# Add to appropriate file
Add-Content requirements-viz.txt "package-name==version"
pip install -r requirements-viz.txt
```

______________________________________________________________________

## 📊 Benefits After Cleanup

| Metric           | Before  | After     | Improvement |
| ---------------- | ------- | --------- | ----------- |
| Total Packages   | 150+    | 35 (prod) | -77%        |
| Install Size     | ~650 MB | ~150 MB   | -77%        |
| Install Time     | ~5 min  | ~1 min    | -80%        |
| Security Surface | High    | Low       | Better      |
| Maintenance      | Complex | Simple    | Easier      |

______________________________________________________________________

## 🎯 Next Steps

1. **Review PROJECT_ANALYSIS.md** for detailed analysis
1. **Backup current environment** (Step 1 above)
1. **Test with clean environment** (Steps 2-4 above)
1. **Update CI/CD pipelines** to use new requirements files
1. **Update documentation** to reference new files
1. **Remove old requirements.txt** (after verification)

______________________________________________________________________

## 📞 Questions?

If you encounter issues:

1. Check the troubleshooting section above
1. Review PROJECT_ANALYSIS.md for package usage details
1. Verify which scripts you actually use
1. Keep only necessary packages in requirements-viz.txt

______________________________________________________________________

*End of Guide*
