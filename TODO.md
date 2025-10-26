# TODO / Enhancements

This document tracks planned enhancements for the `automate_refresh` tooling across Windows and macOS.

## High priority

- Export compression (gz)
  - Write exports as `yyyymmdd_HHMMSS_export_<collection>.json.gz` by default
  - CLI flags:
    - `--compress [none|gz]` (default: `gz` for prod, `none` elsewhere or configurable)
    - `--compression-level [1-9]` (default: `5`)
    - `--keep-uncompressed` (default: `false`)
  - Implementation details:
    - Stream to `gzip.open()`; write to `*.tmp` then rename atomically
    - Log compression ratio, outbound size, elapsed time
  - Mac impact:
    - Puller: `--include-pattern "*_export_<collection>.json*"` to include `.json` and `.json.gz`
    - Importer: support `.json.gz` by opening via `gzip.open` when applicable; prefer `.json.gz` when both exist

- Progress logging knob
  - Current: fixed 10,000-doc increments
  - Add CLI flag `--progress-step N` (default: 10000) to tune verbosity
  - Log format preserved: `Progress: written/size (percent) | rate=docs/s | eta=s`

## Medium priority

- Chunked exports
  - Flag `--chunk-size N` to split large exports into multiple files: `..._part0001.json(.gz)`
  - Importer: detect and import all parts for selected collection (sorted by part index)
  - Advantages: parallelizable copy and safer large transfers

- Pull hardening
  - Retries with backoff for `azcopy` failures and transient network issues
  - Optional `--max-age-days` to limit pulls to recent files only

- Integrity checks
  - Optional sha256 sidecar for each export and verification after pull

## Low priority

- Index management UX
  - CLI to list/apply indexes only (no import)
  - Validate index files before apply

- Automation examples
  - Windows Task Scheduler sample `.bat`
  - macOS `launchd` or cron sample

## Testing & docs

- Unit tests for:
  - Strict filename matching logic (yyyymmdd_HHMMSS)
  - Importer handling of `.json` vs `.json.gz`
  - Progress logging cadence

- Docs:
  - Update README with compression usage and troubleshooting once implemented
# TODO - Python Projects

## 🔴 Critical / Unfinished Items

### Code Quality

- [ ] **Fix Ruff linting issues in `common_config`** (54 auto-fixable issues)
  - Run: `ruff check . --fix --config pyproject.toml`
  - Issues: UP045 (Optional[X] → X | None), I001 (import sorting), UP035/UP006 (Dict/List → dict/list)
  - Files affected: `cli/main.py`, `config/*.py`, `db/*.py`, `export/*.py`, `extraction/*.py`, `utils/*.py`

### Documentation

- [ ] **Add docstrings to all public functions** in `common_config`
  - Priority: `cli/main.py`, `config/settings.py`, `db/connection.py`
- [ ] **Create CHANGELOG.md** to track version history
- [ ] **Document shared_config/.env variables** in shared_config/README.md

### Testing

- [ ] **Write unit tests for `common_config`** (currently minimal)
  - Priority: `config/settings.py`, `db/connection.py`, `export/data_exporter.py`
  - Target: >80% coverage
- [ ] **Add integration tests** for MongoDB connection handling
- [ ] **Test scaffolder** (`common_config init`) with various edge cases

### Legacy Cleanup

- [ ] **Deprecate `common_project/`** - migrate remaining functionality to `common_config`
  - Review `setup_environment.py` and `example_usage.py`
  - Extract any useful patterns not in `common_config`
  - Archive or delete once confirmed obsolete

## 🟡 Medium Priority

### Code Improvements

- [ ] **Add type hints** to all functions (some are missing)
- [ ] **Implement connection pooling** for MongoDB in `common_config`
- [ ] **Add retry logic** for MongoDB operations (transient failures)
- [ ] **Create base exception classes** hierarchy in `common_config.utils.exceptions`

### Configuration

- [ ] **Add JSON schema validation** for `app_config.json`
- [ ] **Support multiple environments** (dev, staging, prod) in config
- [ ] **Add config validation** on startup (fail fast if required vars missing)

### Project-Specific

- [ ] **PatientOtherDetail_isActive_false**: Add rollback functionality
- [ ] **patient_data_extraction**: Add incremental extraction (date-based filtering)
- [ ] **Create project templates** for common patterns (ETL, reporting, etc.)

### DevOps

- [ ] **Add pre-commit hooks** for Black + Ruff
  - Create `.git/hooks/pre-commit` script
- [ ] **Create CI/CD pipeline** (GitHub Actions or similar)
  - Run tests, linting, type checking
- [ ] **Add dependency scanning** (safety, pip-audit)

## 🟢 Nice to Have / Future Enhancements

### Features

- [ ] **Add async MongoDB support** (motor library)
- [ ] **Create data validation utilities** (Pydantic models for common schemas)
- [ ] **Add metrics/monitoring** integration (Prometheus, DataDog)
- [ ] **Create CLI for common operations** (db health check, config validation)
- [ ] **Add Excel validation utilities** (schema checking, data quality)

### Advanced Documentation

- [ ] **Create architecture diagrams** (project structure, data flow)
- [ ] **Add API documentation** (Sphinx or MkDocs)
- [ ] **Create video tutorials** for common workflows
- [ ] **Document best practices** for new projects

### Tooling

- [ ] **Add performance profiling** utilities
- [ ] **Create data migration tools** (schema evolution)
- [ ] **Add database seeding** utilities for testing
- [ ] **Create project dashboard** (web UI for monitoring projects)

### Code Organization

- [ ] **Split `common_config` into sub-packages** if it grows large
  - `common_config.db`, `common_config.export`, `common_config.cli`
- [ ] **Create plugin system** for extending functionality
- [ ] **Add caching layer** for frequently accessed config/data

## 📋 Completed Items

### Initial Setup

- [x] Created `common_config` shared package with Typer CLI
- [x] Migrated to Black + Ruff (removed flake8)
- [x] Standardized on Python 3.11 baseline
- [x] Created root-level `pyproject.toml` for linting config
- [x] Created `lint.sh` script for automated formatting/linting
- [x] Set up `.gitignore` with comprehensive rules
- [x] Documented linting workflow in README.md and LINTING.md
- [x] Froze requirements.txt with exact versions
- [x] Removed unused dependencies from requirements.txt

### Projects

- [x] **PatientOtherDetail_isActive_false**: Production-ready bulk update tool
- [x] **patient_data_extraction**: Migrated to `common_config`

## 🎯 Next Session Priorities

1. **Fix all Ruff linting issues** (10 min)

   ```bash
   ruff check . --fix --config pyproject.toml
   ```

2. **Write basic unit tests** for `common_config` (30 min)
   - Start with `config/settings.py` and `db/connection.py`

3. **Add pre-commit hooks** (15 min)
   - Prevent committing code with linting issues

4. **Document shared_config/.env** (10 min)
   - List all variables and their purpose

5. **Review and archive `common_project/`** (20 min)
   - Confirm nothing critical is lost

---

**Last Updated:** 2025-10-01  
**Status:** Active development, 2 production projects running
