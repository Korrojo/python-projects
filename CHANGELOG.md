# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## \[Unreleased\]

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
