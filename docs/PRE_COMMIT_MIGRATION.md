# Pre-Commit Framework Migration

**Date:** 2025-11-09 **Status:** Completed

## Summary

Migrated from dual validation approach (bash scripts + subdirectory pre-commit) to a **unified pre-commit framework**
for the entire monorepo.

## Problem Statement

We had two validation mechanisms:

1. Parent bash scripts (`scripts/lint.sh`, `scripts/pre-push-check.sh`)
1. mongo_phi_masker-specific `.pre-commit-config.yaml`

**Issues:**

- ❌ Unnecessary complexity - both did the same thing
- ❌ Discrepancy: Ruff used `--fix` locally but CI used check-only
- ❌ Risk of local/CI parity issues (same as PR #34 fixed for Black)
- ❌ Duplication of validation logic

## Solution

Created ONE unified `.pre-commit-config.yaml` at parent level that:

- ✅ Works for ALL 20+ projects in monorepo
- ✅ Exactly matches GitHub Actions CI (preserves PR #34 fix)
- ✅ Replaces bash scripts with pre-commit framework
- ✅ Single source of truth

## CI Parity Preserved

**Critical:** All hooks run in CHECK mode to match CI exactly:

```yaml
# CI Configuration (.github/workflows/mongo-phi-masker-tests.yml)
black --check --diff .    # Check only, no auto-format
ruff check .              # Check only, no --fix
pyright || true           # Informational
pytest -m "unit" --cov=src --cov=masking

# Pre-Commit Configuration (matches above)
black: --check --diff     # ✅ Matches CI
ruff: (no --fix flag)     # ✅ Matches CI (FIXED discrepancy!)
pyright: informational    # ✅ Matches CI
pytest: (local hook)      # ✅ Matches CI
```

**Previously:** Ruff had `--fix` in pre-commit but not in CI → discrepancy **Now:** Ruff check-only in both → parity
maintained

## Changes Made

### Files Added

- `.pre-commit-config.yaml` - Unified config for entire monorepo

### Files Deprecated

- `mongo_phi_masker/.pre-commit-config.yaml` → `.pre-commit-config.yaml.deprecated`

### Hooks Installed

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

## Usage

### For All Developers

```bash
# One-time setup (if not done)
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# Run manually
pre-commit run --all-files          # All hooks
pre-commit run black                # Black only
pre-commit run ruff                 # Ruff only
pre-commit run pyright              # Pyright only (pre-push)

# To manually fix issues (hooks only CHECK, don't fix)
black .                             # Auto-format with Black
ruff check . --fix                  # Auto-fix with Ruff
```

### Hooks Run Automatically

**Pre-commit stage:**

- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-added-large-files
- check-merge-conflict
- check-case-conflict
- mixed-line-ending
- mdformat (markdown)
- **black --check** (no auto-format!)
- **ruff check** (no auto-fix!)

**Pre-push stage:**

- pyright (informational)
- pytest unit tests (if tests/ exists)

## Migration for Projects

### mongo_phi_masker

- ✅ Already using pre-commit - seamless transition
- ✅ Just uses parent config now instead of local
- ✅ No behavior change

### Other Projects

- ✅ Opt-in with `pre-commit install`
- ✅ Or continue using bash scripts (still work)
- ✅ Gradual migration supported

## Bash Scripts Status

**scripts/lint.sh** and **scripts/pre-push-check.sh** still work but are now:

- Optional - pre-commit is preferred
- Maintained for backward compatibility
- May be deprecated in future

## Benefits

1. **CI Parity**: Local validation matches CI exactly (no surprises in PRs)
1. **Faster**: Pre-commit caches results, only checks changed files
1. **Cross-Platform**: Works on Windows, Mac, Linux
1. **Single Source**: One config for all projects
1. **Extensible**: Easy to add new projects or hooks

## Rollback Plan

If issues arise:

```bash
# Restore mongo_phi_masker specific config
git mv mongo_phi_masker/.pre-commit-config.yaml.deprecated \
       mongo_phi_masker/.pre-commit-config.yaml

# Reinstall subdirectory hooks
cd mongo_phi_masker
pre-commit install
pre-commit install --hook-type pre-push
```

## Testing

Verified:

- ✅ Black check matches CI (`--check --diff`)
- ✅ Ruff check matches CI (no `--fix`)
- ✅ Pyright runs on pre-push (informational)
- ✅ Works from any directory in monorepo
- ✅ Pytest runs for projects with tests/

## References

- PR #34: Fixed Black local/CI discrepancy (bash scripts)
- PR #36: Added pre-commit to mongo_phi_masker
- This Migration: Unified both approaches

## See Also

- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Unified configuration
- [.github/workflows/mongo-phi-masker-tests.yml](../.github/workflows/mongo-phi-masker-tests.yml) - CI config
- [Pre-commit Framework](https://pre-commit.com/) - Documentation
