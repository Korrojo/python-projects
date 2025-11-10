# Repository Standards & Best Practices

**Created:** 2025-10-24\
**Purpose:** Establish consistent standards for directory structure and testing across the Python monorepo

______________________________________________________________________

## 1. Directory Structure Standards

### Current State Analysis

**Root Level:**

- ✅ `archive/` - Repository-wide archived files (old packages, deprecated env files)
- ✅ `docs/` - Repository documentation (best practices, lessons learned, schemas)
- ✅ `tests/` - Repository-wide integration tests
- ⚠️ **No `artifacts/` at root** (only in users-provider-update project)

**Project Level (varies by project):**

- ✅ All projects have `archive/` (7 projects)
- ❌ Only 2 projects have `tests/` (appointment_comparison, PatientOtherDetail_isActive_false)
- ❌ Only 1 project has `artifacts/` (users-provider-update)
- ❌ No projects have `docs/` subdirectories

**Scattered Archive Directories:**

- Root: `./archive/`
- Projects: 7 project-level `archive/` folders
- Data: `./data/input/appointment_comparison/archive/`, `./data/output/patients_hcmid_validator/archive/`
- Logs: `./logs/archive/`, `./logs/locl/automate_refresh/archive/`, `./logs/patients_hcmid_validator/archive/`

______________________________________________________________________

## 📋 RECOMMENDED STANDARDS

### A. Directory Hierarchy - Three-Tier Approach

#### **Tier 1: Root-Level Directories** (Repository-Wide)

These should exist ONLY at root level - single source of truth:

```
python/
├── archive/              # Deprecated code, old configs, historical files
│   ├── YYYYMMDD_description/  # Timestamped subdirectories
│   └── README.md         # What's archived and why
│
├── docs/                 # Repository-wide documentation
│   ├── architecture/     # System design, ADRs
│   ├── best-practices/   # Coding standards, patterns
│   ├── guides/           # How-to guides, tutorials
│   ├── schema/           # MongoDB schemas (shared)
│   └── api/              # API documentation
│
├── tests/                # Integration & cross-project tests
│   ├── integration/      # Tests that span multiple projects
│   ├── conftest.py       # Shared test fixtures
│   └── test_*.py         # Smoke tests for shared components
│
└── artifacts/            # Build outputs, generated files (NEW)
    ├── reports/          # Test reports, coverage reports
    ├── wheels/           # Built packages (.whl files)
    └── dist/             # Distribution builds
```

**Rationale:**

- ✅ **Single source of truth** - No confusion about where things are
- ✅ **Centralized documentation** - Easy to find and maintain
- ✅ **Shared test infrastructure** - Reusable fixtures and utilities
- ✅ **Clean builds** - All artifacts in one place, easy to .gitignore

______________________________________________________________________

#### **Tier 2: Shared Infrastructure** (Already Standardized)

These exist at root and are used by all projects:

```
python/
├── data/                 # ALL project data (already standardized ✅)
│   ├── input/<project>/
│   └── output/<project>/
│
├── logs/                 # ALL project logs (already standardized ✅)
│   └── <project>/
│
├── shared_config/        # Single .env source (already standardized ✅)
│   └── .env
│
├── common_config/        # Shared library package (already standardized ✅)
│   └── src/
│
└── temp/                 # Temporary files (already exists ✅)
```

______________________________________________________________________

#### **Tier 3: Project-Level Directories** (Per-Project)

Each project should have this **minimal, consistent** structure:

```
<project_name>/
├── src/                  # Source code (if multi-module project)
│   └── <project_name>/   # Package directory
│
├── tests/                # ⚠️ SHOULD EXIST for ALL projects
│   ├── conftest.py       # Project-specific fixtures
│   ├── test_*.py         # Unit tests
│   └── integration/      # Project integration tests (optional)
│
├── archive/              # Project-specific archived code ONLY
│   └── YYYYMMDD_description/
│
├── run.py                # Main entry point (already standardized ✅)
├── requirements.txt      # Dependencies (already standardized ✅)
└── README.md             # Project-specific documentation
```

**What should NOT exist at project level:**

- ❌ `config/` - Use shared_config/.env instead (already removed ✅)
- ❌ `data/` - Use root data/<project>/ instead (already removed ✅)
- ❌ `logs/` - Use root logs/<project>/ instead (already removed ✅)
- ❌ `docs/` - Use root docs/ with project subdirectories if needed
- ❌ `artifacts/` - Use root artifacts/ instead

______________________________________________________________________

### B. Archive Strategy - Hierarchical by Type

**Problem:** Currently 13 archive directories scattered across the repo

**Solution:** Hierarchical archive structure at ROOT ONLY:

```
archive/
├── code/                    # Deprecated source code
│   ├── 20251024_refactored_packages/
│   │   ├── appointment_comparison_pyproject.toml
│   │   └── patients_hcmid_validator_pyproject.toml
│   └── 20251020_old_scripts/
│
├── config/                  # Old configuration files
│   ├── 20251024_project_configs/
│   │   ├── appointment_comparison/
│   │   ├── patient_demographic/
│   │   └── README.md  # Why these were archived
│   └── 20251024_env_files/
│
├── data/                    # Archived data files (historical)
│   └── 20251024_sample_data/
│
├── logs/                    # Old log files (if needed)
│   └── 20251020_migration_logs/
│
└── docs/                    # Deprecated documentation
    └── 20251024_old_design_docs/
```

**Migration Plan:**

1. Move all project `archive/` contents to root `archive/code/<project>/`
1. Remove all project-level `archive/` directories
1. Clean up data/logs archive subdirectories into root `archive/data/` and `archive/logs/`

______________________________________________________________________

### C. Artifacts vs Archive - Clear Distinction

| Directory    | Purpose                           | Lifespan              | In Git?            |
| ------------ | --------------------------------- | --------------------- | ------------------ |
| `archive/`   | Historical code, deprecated files | Permanent (reference) | ✅ Yes             |
| `artifacts/` | Build outputs, test reports       | Temporary (rebuild)   | ❌ No (.gitignore) |

**Artifacts should contain:**

- Test coverage reports (HTML, XML)
- Built wheels/packages
- Performance benchmarks
- CI/CD outputs

**Archive should contain:**

- Deprecated source code (with explanation)
- Old configuration files (with migration notes)
- Historical documentation (with timestamps)

______________________________________________________________________

## 2. Testing Standards

### Current State Analysis

**✅ What exists:**

- Root `tests/` directory with integration tests
- GitHub Actions CI workflow (`.github/workflows/python-ci.yml`)
- Common_config has smoke tests
- 2 projects have basic smoke tests (appointment_comparison, PatientOtherDetail_isActive_false)

**❌ What's missing:**

- 7 projects have NO tests (78% of projects untested!)
- No pytest configuration in root `pyproject.toml`
- No coverage requirements
- No pre-commit hooks
- Tests run manually, not enforced

______________________________________________________________________

### RECOMMENDED TESTING STANDARDS

#### A. Test Coverage Requirements

**Minimum standards by project type:**

| Project Type            | Min Coverage | Test Types Required |
| ----------------------- | ------------ | ------------------- |
| Library (common_config) | 80%          | Unit + Integration  |
| CLI Scripts (run.py)    | 60%          | Smoke + Integration |
| Data Pipelines          | 70%          | Unit + E2E          |
| Validators              | 75%          | Unit + Edge Cases   |

#### B. Required Test Structure

**Every project MUST have:**

```
<project>/
└── tests/
    ├── conftest.py              # Fixtures (DB mocks, sample data)
    ├── test_smoke.py            # Import tests, basic sanity checks
    ├── test_<module>_unit.py    # Unit tests for each module
    └── integration/             # Integration tests (optional)
        └── test_<feature>_e2e.py
```

**Minimum tests for EVERY project:**

```python
# tests/test_smoke.py - MANDATORY
def test_imports():
    """All modules can be imported without errors."""
    # Import all public modules
    pass


def test_entry_point():
    """Main entry point (run.py) can be executed."""
    # Test run.py --help works
    pass


def test_dependencies():
    """All required dependencies are installed."""
    # Import key dependencies
    pass
```

#### C. Root pyproject.toml - Pytest Configuration

Add this to root `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",                    # Show summary of all test outcomes
    "--strict-markers",       # Enforce marker registration
    "--strict-config",        # Enforce config validity
    "--cov=common_config",    # Coverage for common_config
    "--cov-report=term-missing",  # Show missing lines
    "--cov-report=html:artifacts/coverage",  # HTML report
    "--cov-fail-under=70",    # Fail if coverage < 70%
]
markers = [
    "integration: Integration tests (deselect with '-m \"not integration\"')",
    "slow: Slow tests (deselect with '-m \"not slow\"')",
    "db: Tests requiring database connection",
]

[tool.coverage.run]
source = ["common_config", "*/src"]
omit = [
    "*/tests/*",
    "*/.venv*/*",
    "*/archive/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

#### D. GitHub Actions - Enhanced CI/CD

Update `.github/workflows/python-ci.yml`:

```yaml
name: Python CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main", "develop"]

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov pytest-html
          pip install -r requirements.txt
          pip install -e ./common_config

      - name: Run linting
        run: |
          pip install ruff
          ruff check . --output-format=github

      - name: Run tests with coverage
        run: |
          mkdir -p artifacts/coverage
          pytest -v --cov --cov-report=html:artifacts/coverage --cov-report=xml

      - name: Upload coverage to Codecov (optional)
        uses: codecov/codecov-action@v3
        if: always()
        with:
          file: ./artifacts/coverage.xml
          fail_ci_if_error: false

      - name: Upload test artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: artifacts/

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install pyright
          pip install -r requirements.txt
      - name: Type check
        run: pyright
```

#### E. Pre-commit Hooks (Recommended)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest
        args: [tests/, -m, "not slow", --maxfail=1]
        language: system
        pass_filenames: false
        always_run: true
```

#### F. Test Writing Guidelines

**1. Use descriptive test names:**

```python
# ✅ Good
def test_patient_ref_comparison_handles_string_to_int_conversion():
    pass


# ❌ Bad
def test_compare():
    pass
```

**2. Follow AAA pattern (Arrange, Act, Assert):**

```python
def test_mongo_connection_with_invalid_uri():
    # Arrange
    invalid_uri = "mongodb://invalid:27017"

    # Act
    result = test_connection(invalid_uri)

    # Assert
    assert result["connected"] is False
    assert "error" in result
```

**3. Use fixtures for common setup:**

```python
# conftest.py
@pytest.fixture
def sample_patient_data():
    return {"PatientRef": 123, "FirstName": "John"}


# test_file.py
def test_patient_processing(sample_patient_data):
    result = process_patient(sample_patient_data)
    assert result is not None
```

**4. Mock external dependencies:**

```python
from unittest.mock import Mock, patch


def test_mongodb_query_without_real_db():
    with patch("pymongo.MongoClient") as mock_client:
        mock_db = Mock()
        mock_client.return_value = {"database": mock_db}
        # Test logic here
```

______________________________________________________________________

## 3. Implementation Roadmap

### Phase 1: Directory Restructuring (Week 1)

**Priority: HIGH**

- [ ] Create root `artifacts/` directory
- [ ] Add `artifacts/` to `.gitignore`
- [ ] Consolidate all `archive/` directories to root with hierarchy
- [ ] Remove project-level `archive/` directories
- [ ] Update documentation references

**Estimated effort:** 4-6 hours

______________________________________________________________________

### Phase 2: Testing Infrastructure (Week 1-2)

**Priority: HIGH**

- [ ] Add pytest config to root `pyproject.toml`
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Update GitHub Actions workflow
- [ ] Add `.pre-commit-config.yaml`

**Estimated effort:** 4-6 hours

______________________________________________________________________

### Phase 3: Per-Project Test Coverage (Week 2-4)

**Priority: MEDIUM**

For each of 7 untested projects:

- [ ] Create `tests/` directory
- [ ] Add `test_smoke.py` (imports, entry point)
- [ ] Add `conftest.py` with project fixtures
- [ ] Achieve 30% coverage minimum
- [ ] Document what's NOT tested and why

**Estimated effort per project:** 2-4 hours\
**Total:** 14-28 hours

______________________________________________________________________

### Phase 4: Coverage Improvement (Ongoing)

**Priority: LOW**

- [ ] Increase coverage to 60% for all CLI scripts
- [ ] Increase coverage to 70% for data pipelines
- [ ] Increase coverage to 80% for common_config
- [ ] Add integration tests for cross-project scenarios

**Estimated effort:** Ongoing, 2-4 hours per sprint

______________________________________________________________________

## 4. Success Metrics

### Directory Structure

- ✅ Single `archive/` at root with hierarchical structure
- ✅ Single `docs/` at root (no project-level docs/)
- ✅ Single `artifacts/` at root (gitignored)
- ✅ All projects have `tests/` directory
- ✅ Zero project-level data/, logs/, config/ directories

### Testing

- ✅ 100% of projects have smoke tests
- ✅ 70%+ overall test coverage
- ✅ GitHub Actions passing on all PRs
- ✅ Pre-commit hooks enforcing quality
- ✅ Test artifacts uploaded to CI

______________________________________________________________________

## 5. Best Practices Summary

### Python Development Standards

1. **One source of truth** - Root-level for shared resources
1. **Hierarchical organization** - Group by type, then by date/project
1. **Test everything** - No project without tests
1. **Automate quality** - CI/CD + pre-commit hooks
1. **Document decisions** - README in every archive subdirectory
1. **Version artifacts** - Timestamp all archived items

### Anti-Patterns to Avoid

- ❌ Duplicating directories across projects
- ❌ Committing build artifacts to git
- ❌ Creating projects without tests
- ❌ Archiving without explanation/documentation
- ❌ Mixing active code with archived code

______________________________________________________________________

## Appendix: Project Inventory

### Projects WITH Tests (2/9 = 22%)

1. ✅ appointment_comparison - Has `tests/test_smoke.py`
1. ✅ PatientOtherDetail_isActive_false - Has `tests/test_smoke.py`

### Projects WITHOUT Tests (7/9 = 78%)

1. ❌ automate_refresh
1. ❌ patient_data_extraction
1. ❌ patient_demographic
1. ❌ patients_hcmid_validator
1. ❌ sample_project
1. ❌ staff_appointment_visitStatus
1. ❌ users-provider-update

### Archive Directories to Consolidate (13 total)

- Root: `./archive/`
- Projects: 7 directories
- Data: 2 directories
- Logs: 3 directories

______________________________________________________________________

**Next Steps:** Review and approve this standard, then proceed with Phase 1 implementation.
