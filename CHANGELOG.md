# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## \[Unreleased\]

### Added

- **mongo_backup_tools** - Production CLI wrapper for mongodump/mongorestore/mongoexport/mongoimport
  - Phase 5: Production-ready MongoDB connection options (TLS/SSL, auth mechanisms, replica sets)
  - Environment-based configuration with --env flag
  - Comprehensive testing guide (TESTING.md v1.2.0)
- **mongo_phi_masker** - HIPAA-compliant PHI/PII masking tool (November 2025)
  - Production-grade data masking for healthcare applications
  - Configurable masking rules with JSON-based configuration
  - Email notification support for orchestration workflows
- **mongodb_index_tools** - MongoDB index management & analysis (6 tools consolidated)
- **mongodb_profiler_tools** - Query performance analysis (3 tools consolidated)
- **mongodb_test_data_tools** - Fake test data generation

### Changed

- Updated repository project count from 8 to 14 production applications
- Fixed project naming consistency (appointment_comparison → appt_comparison)
- Updated CONTRIBUTING.md import path to use correct common_config.config.settings
- Moved temporary documentation to appropriate locations:
  - BRANCH_CLEANUP_PLAN.md → docs/archive/
  - AI_COLLABORATION_GUIDE_ENHANCEMENT_PROPOSAL.md → docs/archive/
  - README_GAPS.md → mongo_phi_masker/
- Updated documentation dates to 2025-11-16

### Documentation

- Enhanced main README.md with complete project listings
- Added mongo_backup_tools and mongo_phi_masker to directory tree
- Updated project table with all 14 production projects
- Fixed cross-references to use correct project directory names

## \[0.2.0\] - 2025-11-16

### Added

- Initial repository setup with GitHub best practices
- Comprehensive .gitignore for Python projects
- MIT License
- Security policy (SECURITY.md)
- Code of Conduct (Contributor Covenant 2.1)
- Contributing guidelines (CONTRIBUTING.md)
- Issue templates (bug report, feature request)
- Pull request template
- GitHub Actions CI/CD pipeline
  - Code quality checks (Black, Ruff)
  - Multi-OS testing (Ubuntu, macOS, Windows)
  - Multi-Python version testing (3.11, 3.12)
  - Security scanning (Safety, Bandit, pip-audit)
  - CodeQL analysis
  - Coverage reporting
- Dependabot configuration for automated dependency updates
- Release automation workflow

### Projects Included

- **common_config** - Shared configuration library
- **patients_hcmid_validator** - High-volume CSV vs MongoDB validator
- **patient_data_extraction** - Cross-DB patient data extractor
- **automate_refresh** - Windows/Mac DB refresh automation
- **appt_comparison** - Appointment validation tool
- **patient_demographic** - Demographics pipeline
- **staff_appointment_visitStatus** - Visit status reporting
- **users-provider-update** - User provider validation
- **PatientOtherDetail_isActive_false** - Bulk IsActive toggler

## \[0.1.0\] - 2025-01-26

### Added

- Initial commit
- 8 production-ready Python projects
- Unified configuration system via common_config
- Comprehensive documentation (11+ docs)
- Testing infrastructure with pytest
- Code quality tooling (Black, Ruff, Pyright)
- Shared data/logs directory structure

______________________________________________________________________

## Version History

- **Unreleased** - GitHub repository setup and CI/CD
- **0.1.0** - Initial codebase with 8 projects
