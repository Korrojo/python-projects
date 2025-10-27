# Contributing to Python Projects

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this repository.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Adding a New Project](#adding-a-new-project)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- Familiarity with MongoDB (for most projects)

### Initial Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/python-projects.git
   cd python-projects
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Korrojo/python-projects.git
   ```

4. **Set up virtual environment**:
   ```bash
   # Automated setup (recommended)
   ./install_venv.sh  # macOS/Linux/Git Bash
   # OR
   ./install_venv.ps1  # Windows PowerShell

   # Activate environment
   source activate_venv.sh  # macOS/Linux/Git Bash
   # OR
   ./activate_venv.ps1  # Windows PowerShell
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e ./common_config
   ```

6. **Configure environment**:
   ```bash
   cp shared_config/.env.example shared_config/.env
   # Edit shared_config/.env with your configuration
   ```

7. **Verify setup**:
   ```bash
   python -c "from common_config.config import get_settings; print(get_settings())"
   pytest -q
   ```

## Development Workflow

### Creating a Feature Branch

```bash
# Sync with upstream
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# OR for bug fixes
git checkout -b fix/bug-description
```

### Branch Naming Convention

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

## Coding Standards

### Python Style Guide

We follow PEP 8 with these configurations:

- **Line length**: 120 characters
- **Target version**: Python 3.11
- **Formatter**: Black
- **Linter**: Ruff

### Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking (optional)
pyright
```

### Type Hints

- Use type hints for all function signatures
- Use `from typing import` for complex types
- Example:
  ```python
  from typing import Optional, Dict, List

  def process_data(
      data: List[Dict[str, Any]],
      options: Optional[Dict[str, str]] = None
  ) -> pd.DataFrame:
      ...
  ```

### Documentation

- Use docstrings for all public functions/classes
- Follow Google or NumPy docstring format
- Example:
  ```python
  def validate_patient(patient_id: str, collection: str) -> bool:
      """Validate patient record against database.

      Args:
          patient_id: The patient's HcmId
          collection: MongoDB collection name

      Returns:
          True if validation passes, False otherwise

      Raises:
          ConnectionError: If database connection fails
      """
      ...
  ```

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Use pytest framework
- Aim for >80% code coverage
- Use markers for test categorization:
  ```python
  import pytest

  @pytest.mark.integration
  def test_database_connection():
      ...

  @pytest.mark.slow
  def test_large_dataset():
      ...
  ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=common_config --cov-report=html

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Test Organization

```python
# tests/test_module.py
import pytest
from common_config.config import get_settings

class TestConfiguration:
    """Tests for configuration management."""

    def test_settings_load(self):
        """Test settings load correctly."""
        settings = get_settings()
        assert settings.app_env is not None

    @pytest.mark.integration
    def test_database_connection(self):
        """Test actual database connection."""
        # Integration test code
        ...
```

## Commit Guidelines

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**

```
feat(patients): add CSV batch validation

Implement batch validation for patient HcmId records with
configurable batch size and progress reporting.

Closes #123
```

```
fix(config): resolve environment variable precedence

Fixed issue where OS environment variables weren't overriding
.env file values as expected.

Fixes #456
```

### Commit Best Practices

- Make atomic commits (one logical change per commit)
- Write clear, descriptive commit messages
- Reference issues/PRs when applicable
- Keep commits focused and small

## Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run pre-push validation** (REQUIRED):
   ```bash
   # Ensure virtual environment is activated
   source .venv311/bin/activate

   # Run automated validation
   ./scripts/pre-push-check.sh
   ```

   **This script automatically checks:**
   - ✅ Virtual environment is activated
   - ✅ Code formatting (Black)
   - ✅ Linting (Ruff)
   - ✅ All tests pass
   - ✅ Cross-platform compatibility issues

   **Note:** A git pre-push hook is configured to run this automatically.
   You can bypass it in emergencies with `git push --no-verify` (not recommended).

3. **Manual quality checks** (if needed):
   ```bash
   # Format code
   black .

   # Lint
   ruff check .

   # Run tests
   pytest

   # Check types (optional)
   pyright
   ```

4. **Update documentation**:
   - Update README if adding new features
   - Add docstrings to new functions
   - Update CHANGELOG.md if applicable

### Submitting Pull Request

1. **Push your branch**:
   ```bash
   git push origin your-feature-branch
   ```

2. **Create PR on GitHub**:
   - Use a clear, descriptive title
   - Fill out the PR template completely
   - Link related issues
   - Add screenshots for UI changes
   - Request review from maintainers

3. **PR Title Format**:
   ```
   feat(scope): Short description of change
   ```

### PR Review Process

- Address reviewer feedback promptly
- Keep discussions professional and constructive
- Make requested changes in new commits
- Once approved, maintainers will merge

### After Merge

```bash
# Update your local main
git checkout main
git pull upstream main

# Delete feature branch
git branch -d your-feature-branch
git push origin --delete your-feature-branch
```

## Project Structure

### Repository Layout

```
.
├── common_config/           # Shared configuration library
├── {project_name}/          # Individual project directories
│   ├── src/                 # Source code
│   ├── tests/               # Project-specific tests
│   ├── README.md            # Project documentation
│   └── requirements.txt     # Project dependencies
├── data/                    # Shared data directory
│   ├── input/{project}/
│   └── output/{project}/
├── logs/                    # Shared logs directory
├── tests/                   # Repository-level tests
├── docs/                    # Documentation
└── shared_config/           # Shared configuration
    └── .env                 # Environment variables (not committed)
```

### Common Config Structure

The `common_config` library provides:

- **config/**: Settings management, path resolution
- **db/**: MongoDB connection utilities
- **utils/**: Logging, exceptions, helpers
- **cli/**: Command-line scaffolding tools
- **export/**: Data export utilities
- **extraction/**: Data extraction helpers

## Adding a New Project

### Using the Scaffolder

```bash
# Create new project from template
python -m common_config scaffold my_new_project
```

This creates:
- Project directory structure
- Sample source files
- README template
- requirements.txt
- Test setup

### Manual Setup

1. **Create project directory**:
   ```bash
   mkdir my_new_project
   cd my_new_project
   ```

2. **Create structure**:
   ```bash
   mkdir -p src tests
   touch README.md requirements.txt
   ```

3. **Create requirements.txt**:
   ```
   # Common config (shared library)
   -e ../common_config

   # Additional dependencies
   ```

4. **Create data directories**:
   ```bash
   mkdir -p ../data/input/my_new_project
   mkdir -p ../data/output/my_new_project
   ```

5. **Follow conventions**:
   - Use `common_config` for settings, logging, DB connections
   - Write to shared `data/output/{project}/`
   - Log to shared `logs/{project}/`
   - Follow existing project patterns

### Project Checklist

- [ ] README.md with usage instructions
- [ ] requirements.txt with dependencies
- [ ] Tests in tests/ directory
- [ ] Uses common_config for configuration
- [ ] Follows shared path conventions
- [ ] Includes example usage
- [ ] Documents environment variables needed
- [ ] Adds entry to main README.md

## Questions?

- Check existing issues/discussions
- Review documentation in `docs/`
- Ask in pull request comments
- Contact maintainers

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes
- CONTRIBUTORS.md (if created)

Thank you for contributing! 🎉
