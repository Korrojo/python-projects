# Markdown Formatting with mdformat (Pure Python)

**Purpose:** Document markdown formatting automation using mdformat - a pure Python solution.

**Version:** 1.0 **Last Updated:** 2025-11-02

______________________________________________________________________

## Overview

This repository uses **mdformat** - a pure Python markdown formatter that works like Black but for markdown files.

**Why mdformat?**

- ✅ **Pure Python** - No Node.js dependencies (consistent with Python monorepo)
- ✅ **Like Black** - Same philosophy, auto-formats to consistent style
- ✅ **Fast** - Written in Python, installed via pip
- ✅ **Configurable** - Uses `pyproject.toml` (same as Black/Ruff)
- ✅ **Automated** - Integrated into pre-push hooks and CI/CD

______________________________________________________________________

## Quick Start

### Check Markdown Formatting

```bash
./scripts/markdown-lint.sh check
```

### Auto-Fix Markdown Formatting

```bash
./scripts/markdown-lint.sh fix
```

______________________________________________________________________

## Installation

**mdformat is already in `requirements.txt`**

### First Time Setup

```bash
# Install all dependencies (includes mdformat)
pip install -r requirements.txt
```

### Manual Installation

```bash
# Install mdformat and plugins
pip install mdformat mdformat-gfm mdformat-tables mdformat-frontmatter
```

### Verify Installation

```bash
mdformat --version
```

______________________________________________________________________

## Configuration

### pyproject.toml

mdformat configuration is in the root `pyproject.toml` file (same as Black and Ruff).

```toml
[tool.mdformat]
wrap = 120  # Max line length (matches Black)
number = false  # Don't use numbered lists
```

**Why this config?**

- **wrap = 120** - Matches Black line length for consistency
- **number = false** - Preserves manual list numbering

______________________________________________________________________

## Usage

### Command Line

**Check formatting (no changes):**

```bash
mdformat --check --wrap 120 README.md
mdformat --check --wrap 120 docs/**/*.md
```

**Auto-fix formatting:**

```bash
mdformat --wrap 120 README.md
mdformat --wrap 120 docs/**/*.md
```

### Using Scripts

**Check all markdown files:**

```bash
./scripts/markdown-lint.sh check
```

**Auto-fix all markdown files:**

```bash
./scripts/markdown-lint.sh fix
```

______________________________________________________________________

## What mdformat Fixes

### ✅ Auto-Fixed Issues

mdformat automatically fixes:

1. **Line wrapping** - Wraps long lines at 120 characters
1. **Heading spacing** - Adds blank lines around headings
1. **List formatting** - Consistent list indentation
1. **Code block formatting** - Proper fencing and spacing
1. **Link formatting** - Consistent link style
1. **Table formatting** - Aligns table columns
1. **Whitespace** - Removes trailing spaces, extra blank lines

### Example: Before & After

**Before:**

```markdown
# My Heading
Some text with a very long line that exceeds the 120 character limit and should be wrapped to multiple lines for better readability.
- Item 1
- Item 2
```

**After:**

```markdown
# My Heading

Some text with a very long line that exceeds the 120 character limit and
should be wrapped to multiple lines for better readability.

- Item 1
- Item 2
```

______________________________________________________________________

## Integration

### Pre-Push Hook

mdformat runs automatically before every `git push`.

**Location:** `scripts/pre-push-check.sh`

**Order:**

1. Virtual environment activated
1. **Markdown formatting** ← mdformat check
1. Python code formatting (Black)
1. Python linting (Ruff)
1. Type checking (Pyright)
1. Tests

**To bypass (NOT recommended):**

```bash
git push --no-verify
```

### CI/CD Integration

mdformat runs in GitHub Actions CI/CD pipeline.

**Location:** `.github/workflows/ci.yml`

**Job:** `lint` (Code Quality & Linting)

**What happens:**

1. Install mdformat and plugins via pip
1. Run `mdformat --check` on all .md files
1. Fail build if formatting issues found

______________________________________________________________________

## Plugins

### Installed Plugins

1. **mdformat-gfm** - GitHub Flavored Markdown support

   - Tables
   - Task lists
   - Strikethrough

1. **mdformat-tables** - Table formatting

   - Column alignment
   - Consistent spacing

1. **mdformat-frontmatter** - YAML frontmatter support

   - Preserves YAML headers
   - Common in documentation generators

______________________________________________________________________

## Common Workflows

### 1. Format Before Committing

```bash
# Fix all markdown files
./scripts/markdown-lint.sh fix

# Check what changed
git diff

# Commit
git add .
git commit -m "docs: Format markdown files"
```

### 2. Format Specific Files

```bash
mdformat --wrap 120 README.md
mdformat --wrap 120 docs/guides/SETUP.md
```

### 3. Format Entire Directory

```bash
mdformat --wrap 120 docs/
```

______________________________________________________________________

## Comparison with Node.js Solutions

### Why NOT markdownlint-cli2?

**markdownlint-cli2** (Node.js-based):

- ❌ Requires Node.js (inconsistent with Python monorepo)
- ❌ Requires `package.json` and `node_modules/`
- ❌ Different configuration format (.markdownlint.json)
- ❌ Additional dependency management (npm)

**mdformat** (Pure Python):

- ✅ Pure Python (consistent with Python monorepo)
- ✅ Installed via pip (same as other Python tools)
- ✅ Same configuration format (pyproject.toml)
- ✅ Single dependency manager (pip)
- ✅ Same philosophy as Black (auto-format, minimal config)

______________________________________________________________________

## Excluded Files/Directories

The script automatically excludes:

- `.venv*/**` - Virtual environments
- `node_modules/**` - NPM packages (if any)
- `temp/**` - Temporary files
- `artifacts/**` - Build artifacts
- `build/**` - Build directories
- `dist/**` - Distribution directories

______________________________________________________________________

## Troubleshooting

### mdformat not found

**Solution:**

```bash
pip install -r requirements.txt
# or
pip install mdformat mdformat-gfm mdformat-tables mdformat-frontmatter
```

### Permission denied

**Solution (Linux/macOS):**

```bash
chmod +x scripts/markdown-lint.sh
```

### "File would be reformatted"

This is expected in check mode. To fix:

```bash
./scripts/markdown-lint.sh fix
```

### Want to ignore a file

Create `.mdformatignore` in repository root:

```gitignore
temp/
artifacts/
CHANGELOG.md  # Example: ignore specific file
```

______________________________________________________________________

## Best Practices

### 1. Run Before Committing

```bash
./scripts/markdown-lint.sh fix
```

### 2. Use in VS Code

Install the mdformat extension:

- Extension: "mdformat"
- Format on save: Enabled

### 3. Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
./scripts/markdown-lint.sh fix
git add *.md
```

______________________________________________________________________

## Comparison to Black (Python Code Formatter)

| Feature         | Black (Python)              | mdformat (Markdown)         |
| --------------- | --------------------------- | --------------------------- |
| **Language**    | Python                      | Markdown                    |
| **Philosophy**  | Auto-format, minimal config | Auto-format, minimal config |
| **Config file** | `pyproject.toml`            | `pyproject.toml`            |
| **Line length** | 120                         | 120 (configurable)          |
| **Install**     | `pip install black`         | `pip install mdformat`      |
| **Usage**       | `black .`                   | `mdformat .`                |

**Both are pure Python solutions with the same philosophy!**

______________________________________________________________________

## Advanced Usage

### Format with Specific Options

```bash
# No line wrapping
mdformat --wrap no README.md

# Different wrap length
mdformat --wrap 80 README.md

# Keep numbered lists
mdformat --number README.md
```

### Integration with Other Tools

```bash
# Check formatting in CI
mdformat --check docs/

# Format and show diff
mdformat --check --diff README.md
```

______________________________________________________________________

## Statistics (Initial Setup)

**Repository-wide formatting (2025-11-02):**

- **Tool:** mdformat v0.7.22
- **Files:** 65 markdown files
- **Auto-formatted:** All files
- **Consistency:** 100%

______________________________________________________________________

## Related Documentation

- [scripts/README.md](../../scripts/README.md) - Script documentation
- [pyproject.toml](../../pyproject.toml) - Configuration
- [requirements.txt](../../requirements.txt) - Dependencies
- [mdformat GitHub](https://github.com/executablebooks/mdformat)
- [mdformat plugins](https://mdformat.readthedocs.io/)

______________________________________________________________________

## Summary

**mdformat is the markdown equivalent of Black:**

- ✅ Pure Python
- ✅ Auto-formats to consistent style
- ✅ Minimal configuration
- ✅ Integrated into workflow
- ✅ Matches repository philosophy

**No Node.js required!** 🎉

______________________________________________________________________

## Contributing

When adding new markdown files:

1. Write your documentation
1. Run `./scripts/markdown-lint.sh fix`
1. Commit changes
1. Pre-push hook validates formatting

**The formatting is automatic - focus on content!**
