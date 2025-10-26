# Linting and Formatting Guide

This project uses **Ruff** (formatter + linter) and **Pyright** (type checker) for code quality.

## Tools

- **Ruff**: Fast Python formatter and linter (replaces Black, isort, pyupgrade, etc.)
- **Pyright**: Static type checker (integrated via Pylance in VS Code)

## Installation

```bash
# 1. Create and activate your Python virtual environment (recommended):
./install_venv.sh           # Bash/Git Bash/Linux/macOS
./install_venv.ps1          # PowerShell (Windows)

# After running the install script, follow the printed instructions:
#   source activate_venv.sh        # Bash/Git Bash/Linux/macOS
#   ./activate_venv.ps1            # PowerShell (Windows)
#   .venv311/Scripts/activate.bat  # CMD (Windows)

# 2. Install dependencies:
pip install -r requirements.txt

# 3. Install linting tools:
pip install ruff
# Pyright is optional for CLI - VS Code has it built-in via Pylance
npm install -g pyright  # Optional for command-line type checking
```

## Configuration

All configuration is in `pyproject.toml` at the root level:

- Line length: 120 characters
- Target Python version: 3.11
- Ruff rules: pycodestyle, Pyflakes, isort, pep8-naming, pyupgrade, bugbear, comprehensions

## Usage

### Quick Start - Format, Lint, and Type Check Everything

```bash
./lint.sh
```

> **Tip:** Always activate your virtual environment before running any linting, formatting, or type checking commands.

### Format and Lint Specific Directory/File

```bash
./lint.sh PatientOtherDetail_isActive_false/
./lint.sh common_config/src/
./lint.sh run.py
```

### Individual Commands

**Format code with Ruff:**

```bash
# Format entire project
ruff format .

# Format specific directory
ruff format PatientOtherDetail_isActive_false/

# Format specific file
ruff format run.py

# Check only (don't modify)
ruff format --check .
```

**Lint code with Ruff:**

```bash
# Lint entire project
ruff check .

# Lint specific directory
ruff check common_config/

# Auto-fix issues
ruff check . --fix

# Show all issues (including fixed)
ruff check . --fix --show-fixes
```

**Type check with Pyright:**

```bash
# Type check entire project
pyright .

# Type check specific directory
pyright common_config/

# Type check specific file
pyright run.py
```

**Check imports with Ruff (isort replacement):**

```bash
# Ruff includes isort functionality
ruff check . --select I --fix
```

## Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
ruff format --check .
ruff check .
pyright .
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## CI/CD Integration

Add to your CI pipeline:

```bash
pip install black ruff
black --check .
ruff check .
```

## VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Common Ruff Rules

- **E**: pycodestyle errors (PEP 8 violations)
- **W**: pycodestyle warnings
- **F**: Pyflakes (unused imports, undefined names)
- **I**: isort (import sorting)
- **N**: pep8-naming (naming conventions)
- **UP**: pyupgrade (Python version upgrades)
- **B**: bugbear (common bugs)
- **C4**: comprehensions (better comprehensions)

## Ignoring Rules

**Per-file:**

```python
# ruff: noqa: E501
```

**Per-line:**

```python
x = very_long_line()  # noqa: E501
```

**In pyproject.toml:**

```toml
[tool.ruff]
ignore = ["E501"]
```

## Troubleshooting

**Black and Ruff conflict:**
- Black handles line length (E501), so Ruff ignores it
- Run Black first, then Ruff

**Import sorting:**
- Ruff's isort is enabled by default
- First-party packages defined in `pyproject.toml`

**Unused imports in `__init__.py`:**
- Automatically ignored via `per-file-ignores`
