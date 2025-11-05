# Python Projects Repository

> **Monorepo containing 13 Python projects with shared configuration, centralized data/logs, and unified tooling.**

**Latest:** 🆕 mongo_phi_masker integrated - Production-grade HIPAA-compliant PHI/PII masking tool - Nov 2025

______________________________________________________________________

## 🚀 5-Minute Quickstart

**First time here? Start with these 3 steps:**

```bash
# 1. Create virtual environment (Python 3.11 required)
./install_venv.sh          # macOS/Linux/Git Bash
# OR
./install_venv.ps1         # Windows PowerShell

# 2. Activate environment
source .venv311/bin/activate      # macOS/Linux/Git Bash
# OR
.venv311/Scripts/activate.bat     # Windows CMD
# OR
./activate_venv.ps1               # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt
pip install -e ./common_config
```

**Verify setup:**

```bash
python -c "from common_config.config.settings import get_settings; print('✅ Setup complete!')"
```

**Next:** Configure your environment → See [Environment Setup](#environment-setup) below

______________________________________________________________________

## 📖 Documentation Hub

**Choose your path based on what you want to do:**

### 🆕 I'm New Here

**Start here:** [Repository Overview & First-Time Setup](#repository-overview)

**Then read:**

1. [Environment Setup](#environment-setup) - Configure MongoDB and paths
1. [Creating Your First Project](#creating-your-first-project) - Scaffold a new project
1. [Code Quality Standards](#code-quality-standards) - Pre-push validation

### 🔨 I Want to Create a New Project

**Primary guide:** [`docs/guides/NEW_PROJECT_GUIDE.md`](docs/guides/NEW_PROJECT_GUIDE.md) ⭐ **← START HERE**

- 9-phase walkthrough from environment setup to Git commit
- Cross-platform (macOS, Linux, Windows)
- Complete with verification steps

**Essential reading:**

- [`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md) ⭐⭐ **← READ BEFORE CODING**
  - Correct import paths for common_config (prevents errors)
  - MongoDB connection patterns
  - Copy-paste code templates

**Supporting docs:**

- [`docs/guides/TESTING_GUIDE.md`](docs/guides/TESTING_GUIDE.md) - Writing and running tests
- [`docs/guides/REPOSITORY_STANDARDS.md`](docs/guides/REPOSITORY_STANDARDS.md) - Directory structure

### 🐛 I'm Encountering Errors

**Import errors?**

- [`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md) - Correct import paths
- [`docs/best-practices/IMPORT_PATH_ISSUES.md`](docs/best-practices/IMPORT_PATH_ISSUES.md) - Why errors happen &
  prevention

**CI/CD failures?**

- [`docs/best-practices/CI_CD_LESSONS_LEARNED.md`](docs/best-practices/CI_CD_LESSONS_LEARNED.md) - Common failures &
  fixes
- [Code Quality Standards](#code-quality-standards) - Pre-push validation

**Environment issues?**

- [`docs/guides/VENV_SETUP.md`](docs/guides/VENV_SETUP.md) - Virtual environment troubleshooting

### 📚 I Need Reference Material

**Best practices:**

- [`docs/AI_COLLABORATION_GUIDE.md`](docs/AI_COLLABORATION_GUIDE.md) 🤖 - Guide for AI assistants (session context)
- [`docs/best-practices/CLI_PATTERNS.md`](docs/best-practices/CLI_PATTERNS.md) ⭐ - Standard CLI patterns (--env,
  --collection)
- [`docs/best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md`](docs/best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md)
  \- 20 reusable patterns
- [`docs/best-practices/REPOSITORY_LESSONS_LEARNED.md`](docs/best-practices/REPOSITORY_LESSONS_LEARNED.md) -
  Organizational patterns

**Technical guides:**

- [`docs/guides/LINTING.md`](docs/guides/LINTING.md) - Ruff and Pyright setup
- [`docs/guides/TESTING_GUIDE.md`](docs/guides/TESTING_GUIDE.md) - Testing strategies

**Complete index:**

- [`docs/README.md`](docs/README.md) - All documentation organized by type

### 🔍 I'm Looking for Something Specific

**Use the docs index:** [`docs/README.md`](docs/README.md)

**Common searches:**

- CLI patterns (--env, --collection) → [`docs/best-practices/CLI_PATTERNS.md`](docs/best-practices/CLI_PATTERNS.md)
- MongoDB patterns →
  [`docs/best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md`](docs/best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md)
- Performance optimization → `appointment_comparison/PERFORMANCE_OPTIMIZATIONS.md`
- Project structure → [`docs/guides/REPOSITORY_STANDARDS.md`](docs/guides/REPOSITORY_STANDARDS.md)
- Migrating legacy projects →
  [`docs/best-practices/REPOSITORY_LESSONS_LEARNED.md`](docs/best-practices/REPOSITORY_LESSONS_LEARNED.md) Section 7

______________________________________________________________________

## 🏗️ Repository Overview

### What is This Repository?

A **monorepo** containing multiple Python projects that share:

- ✅ Single virtual environment (`.venv311/`)
- ✅ Shared configuration (`shared_config/.env`)
- ✅ Common utilities (`common_config` package)
- ✅ Centralized data/logs directories
- ✅ Unified code quality tools
- ✅ Consistent MongoDB access patterns

### Key Principles

1. **One Virtual Environment** - All projects use `.venv311/` (Python 3.11)
1. **Shared Configuration** - MongoDB URIs, database names in `shared_config/.env`
1. **Centralized Paths** - All projects use `data/`, `logs/`, `artifacts/` at repo root
1. **Common Utilities** - `common_config` provides settings, logging, MongoDB connectors
1. **Code Quality** - Automated pre-push validation prevents CI failures

### Directory Structure

```
python/
├── .venv311/                    # Shared virtual environment (Python 3.11)
├── shared_config/
│   └── .env                     # MongoDB URIs, database names, environment config
├── common_config/               # Shared library (install with: pip install -e ./common_config)
│   └── src/common_config/
│       ├── config/              # Settings loader
│       ├── connectors/          # MongoDB connection helpers
│       ├── utils/               # Logging, file operations
│       └── cli/                 # Project scaffolding CLI
├── data/                        # Centralized data directory
│   ├── input/<project>/         # Project-specific inputs
│   └── output/<project>/        # Project-specific outputs
├── logs/<project>/              # Centralized logs (per-project subdirs)
├── artifacts/                   # Test reports, coverage (gitignored)
├── docs/                        # Documentation hub ← YOU ARE HERE
│   ├── guides/                  # Step-by-step how-to guides
│   ├── best-practices/          # Reference material & patterns
│   └── README.md                # Documentation index
├── scripts/                     # Shared utility scripts
│   ├── pre-push-check.sh        # Validation script
│   └── lint.sh                  # Code quality checks
├── .github/workflows/           # CI/CD
├── pyproject.toml               # Black, Ruff config
├── requirements.txt             # Shared dependencies
└── README.md                    # ← THIS FILE (Master documentation hub)

# Individual Projects (12 total)
├── appointment_comparison/      # Athena CSV vs MongoDB validator
├── automate_refresh/            # MongoDB export/import automation
├── db_collection_stats/         # MongoDB collection statistics tool
├── mongodb_index_tools/         # 🆕 MongoDB index management & analysis (6 tools consolidated)
├── mongodb_profiler_tools/      # 🆕 Query performance analysis (3 tools consolidated)
├── mongodb_test_data_tools/     # 🆕 Fake test data generation
├── patient_data_extraction/     # Cross-DB patient extractor
├── patient_demographic/         # Demographics pipeline
├── patients_hcmid_validator/    # High-volume CSV validator
├── PatientOtherDetail_isActive_false/  # Bulk Admits.IsActive updater
├── staff_appointment_visitStatus/      # Appointment status tools
└── users-provider-update/       # Provider data updater
```

______________________________________________________________________

## ⚙️ Environment Setup

### 1. Configure MongoDB Connection

Create or edit `shared_config/.env`:

```bash
# MongoDB Connection (environment-specific)
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=UbiquityDevelopment

MONGODB_URI_PROD=mongodb://production-server:27017
DATABASE_NAME_PROD=UbiquityProduction

# Active environment (selects which _<ENV> variables to use)
APP_ENV=DEV  # Options: DEV, STG, PROD, LOCL, etc.
```

### 2. Verify Configuration

```bash
python -c "from common_config.config.settings import get_settings; s=get_settings(); print(f'ENV: {s.app_env}\nURI: {s.mongodb_uri}\nDB: {s.database_name}')"
```

**Expected output:**

```
ENV: DEV
URI: mongodb://localhost:27017
DB: UbiquityDevelopment
```

### 3. Environment Variables Explained

**Pattern:** `<VARIABLE>_<ENV>`

**Required variables:**

- `MONGODB_URI_<ENV>` - MongoDB connection string
- `DATABASE_NAME_<ENV>` - Database name
- `APP_ENV` - Selects which environment to use

**Optional variables:**

- `BACKUP_DIR_<ENV>` - Backup/export directory
- `LOG_DIR_<ENV>` - Override default log location

**Precedence (last wins):**

1. `shared_config/.env` (lowest priority)
1. `config/.env` (project-level, if exists)
1. `.env` (project root, rare)
1. OS environment variables (highest priority)

______________________________________________________________________

## 🆕 Creating Your First Project

### Quick Command

```bash
# Scaffold new project structure
common my_new_project
```

**This creates:**

- `my_new_project/` with standard structure
- Template `run.py` with logging setup
- Smoke tests in `tests/`
- Centralized directories: `data/input/my_new_project/`, `logs/my_new_project/`

### ⚠️ IMPORTANT - Before Writing Code

**Step 1:** Read the scaffolding guide → [`docs/guides/NEW_PROJECT_GUIDE.md`](docs/guides/NEW_PROJECT_GUIDE.md)

**Step 2:** Before adding ANY imports from `common_config`: →
[`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md) ⭐

**Why Step 2 is critical:** Guessing import paths causes errors like:

```
ModuleNotFoundError: No module named 'common_config.db.mongo_client'
```

The API Reference shows you the **correct** paths:

```python
# ✅ CORRECT
from common_config.connectors.mongodb import get_mongo_client
from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger
```

______________________________________________________________________

## ✅ Code Quality Standards

### Pre-Push Validation (Automated)

**All code must pass validation before pushing to main or creating PRs.**

A **git pre-push hook** automatically runs:

- ✅ Virtual environment check
- ✅ Code formatting (Black)
- ✅ Linting (Ruff)
- ✅ All tests pass
- ✅ Cross-platform compatibility

**Normal workflow:**

```bash
# Just push - validation runs automatically
git push
```

**Manual validation:**

```bash
./scripts/pre-push-check.sh
```

**Emergency bypass** (not recommended):

```bash
git push --no-verify  # Skips validation
```

**Why this matters:** Prevents CI failures, broken builds, and Windows compatibility issues.

**Details:** [`docs/best-practices/CI_CD_LESSONS_LEARNED.md`](docs/best-practices/CI_CD_LESSONS_LEARNED.md)

### Running Code Quality Tools

```bash
# Format and lint specific project
./scripts/lint.sh my_project/

# Format and lint entire repo
./scripts/lint.sh .

# Run tests for specific project
pytest my_project/tests/ -v

# Run all tests
pytest -q --maxfail=1 --disable-warnings -m "not integration"
```

______________________________________________________________________

## 📦 Current Projects

This repository contains 8+ production projects:

| Project                               | Purpose                                                        | Documentation                                 |
| ------------------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| **appointment_comparison**            | Validates Athena CSV appointments vs MongoDB StaffAvailability | `appointment_comparison/README.md`            |
| **automate_refresh**                  | MongoDB export/import automation (Windows/Mac)                 | `automate_refresh/README.md`                  |
| **db_collection_stats**               | Gathers and exports MongoDB collection statistics              | `db_collection_stats/README.md`               |
| **patient_data_extraction**           | Cross-database patient data extractor                          | `patient_data_extraction/README.md`           |
| **patient_demographic**               | Patient demographics pipeline                                  | `patient_demographic/README.md`               |
| **patients_hcmid_validator**          | High-volume CSV validator with MongoDB lookup                  | `patients_hcmid_validator/README.md`          |
| **PatientOtherDetail_isActive_false** | Bulk updates Admits.IsActive field                             | `PatientOtherDetail_isActive_false/README.md` |
| **staff_appointment_visitStatus**     | Staff appointment status management                            | `staff_appointment_visitStatus/README.md`     |

**See individual project READMEs for usage instructions.**

______________________________________________________________________

## 🧪 Testing

### Quick Commands

```bash
# Run all tests (excludes integration tests by default)
pytest -q --maxfail=1 --disable-warnings -m "not integration"

# Run tests for specific project
pytest my_project/tests/ -v

# Run with coverage
pytest --cov=my_project --cov-report=term-missing

# Run integration tests (require MongoDB)
pytest -m "integration"
```

### Testing Philosophy

- **Unit tests:** Fast (\<1s each), no external dependencies, use mocks
- **Integration tests:** Marked with `@pytest.mark.integration`, may require MongoDB
- **CI runs:** Unit tests only (integration tests excluded)

**Full guide:** [`docs/guides/TESTING_GUIDE.md`](docs/guides/TESTING_GUIDE.md)

______________________________________________________________________

## 🛠️ Common Tasks

### Scaffold a New Project

```bash
common my_new_project
```

**Guide:** [`docs/guides/NEW_PROJECT_GUIDE.md`](docs/guides/NEW_PROJECT_GUIDE.md)

### Run Code Quality Checks

```bash
./scripts/lint.sh my_project/
```

### Add MongoDB to a Project

**FIRST:** Read [`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md)

**Then:** Use this pattern:

```python
from common_config.connectors.mongodb import get_mongo_client
from common_config.config.settings import get_settings

settings = get_settings()
with get_mongo_client(
    mongodb_uri=settings.mongodb_uri,
    database_name=settings.database_name
) as client:
    db = client[settings.database_name]
    # Use database
```

### Fix Import Errors

1. Check [`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md) for correct path
1. See [`docs/best-practices/IMPORT_PATH_ISSUES.md`](docs/best-practices/IMPORT_PATH_ISSUES.md) for common mistakes

### Migrate a Legacy Project

**Guide:** [`docs/best-practices/REPOSITORY_LESSONS_LEARNED.md`](docs/best-practices/REPOSITORY_LESSONS_LEARNED.md)
Section 7

______________________________________________________________________

## 🔗 Quick Links

### Essential Reading (Everyone)

1. [NEW_PROJECT_GUIDE.md](docs/guides/NEW_PROJECT_GUIDE.md) - Creating new projects
1. [COMMON_CONFIG_API_REFERENCE.md](docs/guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths & patterns
1. [CI_CD_LESSONS_LEARNED.md](docs/best-practices/CI_CD_LESSONS_LEARNED.md) - Preventing CI failures

### Reference Material

- [CLI_PATTERNS.md](docs/best-practices/CLI_PATTERNS.md) - Standard CLI patterns (--env, --collection)
- [MONGODB_VALIDATION_BEST_PRACTICES.md](docs/best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md) - 20 reusable
  patterns
- [REPOSITORY_LESSONS_LEARNED.md](docs/best-practices/REPOSITORY_LESSONS_LEARNED.md) - Project structure patterns
- [TESTING_GUIDE.md](docs/guides/TESTING_GUIDE.md) - Testing strategies

### Complete Documentation Index

- [docs/README.md](docs/README.md) - All docs organized by type

______________________________________________________________________

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'common_config'"

```bash
# Install common_config in editable mode
pip install -e ./common_config
```

### "ModuleNotFoundError: No module named 'common_config.db.mongo_client'"

**Wrong import path.** See: [`docs/guides/COMMON_CONFIG_API_REFERENCE.md`](docs/guides/COMMON_CONFIG_API_REFERENCE.md)

```python
# ✅ CORRECT
from common_config.connectors.mongodb import get_mongo_client
```

### "MongoDB URI not found"

Add to `shared_config/.env`:

```bash
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=your_database
APP_ENV=DEV
```

### CI/CD Failures

**Read:** [`docs/best-practices/CI_CD_LESSONS_LEARNED.md`](docs/best-practices/CI_CD_LESSONS_LEARNED.md)

**Quick fix:**

```bash
# Run validation before pushing
./scripts/pre-push-check.sh
```

### Virtual Environment Issues

**Guide:** [`docs/guides/VENV_SETUP.md`](docs/guides/VENV_SETUP.md)

______________________________________________________________________

## 📊 Repository Statistics

- **Projects:** 8+ production applications
- **Shared Library:** common_config (settings, logging, MongoDB)
- **Python Version:** 3.11
- **Code Quality:** Black (formatting), Ruff (linting), Pyright (type checking)
- **Testing:** pytest with coverage tracking
- **CI/CD:** GitHub Actions (automated testing, multi-platform)

______________________________________________________________________

## 🤝 Contributing

### Before Making Changes

1. **Read:** [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
1. **Run:** `./scripts/pre-push-check.sh` before committing
1. **Ensure:** All tests pass and code is formatted

### Creating New Documentation

**How-to guides** → `docs/guides/` **Reference material** → `docs/best-practices/` **Historical records** →
`docs/archive/`

**Then:** Update `docs/README.md` to include your new document

______________________________________________________________________

## 📝 License & Support

See individual project READMEs for project-specific licensing.

For questions or issues, create an issue in the repository.

______________________________________________________________________

**Last Updated:** 2025-01-27
