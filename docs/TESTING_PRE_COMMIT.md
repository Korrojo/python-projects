# Testing Pre-Commit Hooks

Quick guide to test the unified pre-commit configuration.

## Quick Tests (No Changes Needed)

### Test All Pre-Commit Hooks

```bash
pre-commit run --all-files
```

**What this does:**

- Runs all hooks that trigger on `git commit`
- Shows: trailing-whitespace, end-of-file, yaml, large files, merge conflicts, mdformat, black, ruff
- Takes 10-30 seconds on full repo

### Test Pre-Push Hooks Only

```bash
pre-commit run --hook-stage pre-push --all-files
```

**What this does:**

- Runs hooks that trigger on `git push`
- Shows: pyright (type checking), pytest (unit tests)
- Takes 30-60 seconds (pyright is slower)

### Test Individual Tools

```bash
# Test Black (Python formatter check)
pre-commit run black --all-files

# Test Ruff (Python linter)
pre-commit run ruff --all-files

# Test Pyright (Type checker)
pre-commit run pyright --all-files

# Test Pytest (Unit tests)
pre-commit run pytest-check --all-files

# Test Markdown formatting
pre-commit run mdformat --all-files
```

## Real Workflow Test

### Test Commit Workflow

```bash
# 1. Make a small change (example)
echo "# Test" >> test_file.md

# 2. Stage it
git add test_file.md

# 3. Try to commit (hooks will run automatically)
git commit -m "test: verify hooks work"

# You'll see:
# - trim trailing whitespace....Passed
# - fix end of files............Passed
# - check yaml..................Passed
# - mdformat....................Passed
# - black --check...............Passed
# - ruff check..................Passed

# 4. Clean up
git reset HEAD~1
git restore test_file.md
rm test_file.md
```

### Test Push Workflow

```bash
# After committing a change
git push

# You'll see pre-push hooks run:
# - pyright (informational).....Passed (or warnings)
# - pytest unit tests...........Passed
```

## What You Should See

### ✅ Successful Run

```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check for added large files..............................................Passed
check for merge conflicts................................................Passed
check for case conflicts.................................................Passed
mixed line ending........................................................Passed
mdformat (markdown formatter)............................................Passed
black --check (matches CI)...............................................Passed
ruff check (matches CI)..................................................Passed
```

### ❌ Failed Check (Example: Black formatting issue)

```
black --check (matches CI)...............................................Failed
- hook id: black
- exit code: 1

would reformat src/example.py

Oh no! 💥 💔 💥
1 file would be reformatted.
```

**How to fix:**

```bash
black .              # Auto-format the file
git add src/example.py
git commit -m "..."  # Try again
```

### ⚠️ Ruff Issues

```
ruff check (matches CI)..................................................Failed
- hook id: ruff
- exit code: 1

src/example.py:15:1: E402 Module level import not at top of file
Found 1 error.
```

**How to fix:**

```bash
ruff check . --fix   # Auto-fix if possible
# OR manually fix the file
git add src/example.py
git commit -m "..."  # Try again
```

## Comparison with Old Workflow

### Before (Bash Scripts)

```bash
# Old way
./scripts/lint.sh
./scripts/pre-push-check.sh

# Issues:
# - Had to run manually
# - Different from CI
# - Ruff auto-fixed locally, failed in CI
```

### After (Pre-Commit Framework)

```bash
# New way (automatic)
git commit   # Hooks run automatically
git push     # Pre-push hooks run automatically

# Manual run
pre-commit run --all-files

# Benefits:
# - Automatic on commit/push
# - Matches CI exactly
# - Faster (caches results)
# - Same behavior everywhere
```

## Verification: CI Parity

Verify local matches CI:

```bash
# What CI runs (.github/workflows/mongo-phi-masker-tests.yml):
black --check --diff .
ruff check .
pyright || true
pytest -m "unit" --cov=src --cov=masking

# What pre-commit runs (locally):
pre-commit run black        # black --check --diff ✅
pre-commit run ruff         # ruff check (NO --fix) ✅
pre-commit run pyright      # pyright (informational) ✅
pre-commit run pytest-check # pytest -m "unit" --cov ✅
```

**All match!** No local/CI surprises.

## Troubleshooting

### "pre-commit: command not found"

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

### Hooks not running on commit

```bash
# Reinstall hooks
pre-commit install
pre-commit install --hook-type pre-push

# Verify installation
ls -la .git/hooks/pre-commit
ls -la .git/hooks/pre-push
```

### Want to skip hooks (emergency only)

```bash
git commit --no-verify -m "..."   # Skip pre-commit hooks
git push --no-verify              # Skip pre-push hooks
```

**⚠️ Not recommended!** You'll likely fail CI.

### Update hooks to latest versions

```bash
pre-commit autoupdate
pre-commit run --all-files  # Test after update
```

## From mongo_phi_masker Directory

Pre-commit works from **any directory**:

```bash
cd /Users/.../python-projects/mongo_phi_masker

# All these work:
pre-commit run --all-files
pre-commit run black
git commit -m "..."
git push
```

The config at parent level (`.pre-commit-config.yaml`) applies to all projects!

## See Also

- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Configuration
- [docs/PRE_COMMIT_MIGRATION.md](./PRE_COMMIT_MIGRATION.md) - Migration details
- [Pre-commit Framework](https://pre-commit.com/) - Official docs
