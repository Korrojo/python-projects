# Code Quality Enforcement - No Bypass Policy

**Status:** MANDATORY for all contributors **Effective Date:** 2025-11-16

## The Problem

Using `git push --no-verify` or `git commit --no-verify` bypasses critical quality checks:

- ❌ Code formatting (Black, mdformat)
- ❌ Linting (Ruff)
- ❌ Type checking (Pyright)
- ❌ Unit tests
- ❌ Security checks

**Result:** CI failures, broken builds, wasted time, and frustrated team members.

## The Solution: Multi-Layer Protection

We've implemented a 3-layer defense system to prevent hook bypass:

### Layer 1: Local Git Command Wrapper 🛡️

**Location:** `scripts/git-safe`

A wrapper script that intercepts git commands and **blocks `--no-verify` flag**.

**Installation:**

```bash
./scripts/install-git-safety.sh
```

**Usage:**

```bash
# These commands are protected:
git safe-push        # Instead of: git push --no-verify
git safe-commit      # Instead of: git commit --no-verify

# Or add alias to your shell:
alias git='./scripts/git-safe'
```

**What happens when blocked:**

```
╔════════════════════════════════════════════════════════════════╗
║                    🚫 SECURITY VIOLATION 🚫                     ║
╠════════════════════════════════════════════════════════════════╣
║  The --no-verify flag is BLOCKED in this repository           ║
║                                                                ║
║  Why: Bypassing hooks leads to CI failures and broken builds  ║
╚════════════════════════════════════════════════════════════════╝

📋 Proper Workflow:
  1. Fix the validation errors shown in the hook output
  2. Run: ./scripts/pre-push-check.sh to verify fixes
  3. Commit the fixes: git add . && git commit --amend
  4. Push without --no-verify: git push

⚠️  If you bypass this check, your PR will fail CI anyway!
```

### Layer 2: GitHub Branch Protection Rules 🔐

**Required for:** `main`, `master`, and all `release/*` branches

**Configuration (Admins only):**

Settings → Branches → Branch protection rules:

- ✅ Require status checks to pass before merging
  - ✅ CI/CD Pipeline / CI Summary
  - ✅ CI/CD Pipeline / Code Quality & Linting
  - ✅ All project-specific test suites
- ✅ Require branches to be up to date before merging
- ✅ Require linear history
- ✅ Do not allow bypassing the above settings
- ✅ Restrict who can push to matching branches
- ✅ Require pull request reviews before merging (1 reviewer minimum)

**Result:** Even if someone bypasses local checks, **the PR cannot be merged** until all CI checks pass.

### Layer 3: CI/CD Strict Mode ⚡

**Configuration:** `.github/workflows/`

All CI workflows run in **strict mode**:

```yaml
# Fail fast on any error
set -e

# Run all checks (no shortcuts)
- Markdown formatting check
- Python code formatting (Black) - check mode only
- Linting (Ruff)
- Type checking (Pyright) - warnings allowed
- Unit tests - must pass 100%
- Integration tests - on main/release branches
- Security scanning
- Cross-platform validation
```

**Result:** PRs with quality issues **cannot pass CI**, blocking merge.

## Enforcement Policy

### For Contributors

1. **MUST** run `./scripts/pre-push-check.sh` before every push
1. **MUST NOT** use `--no-verify` flag (blocked by git-safe wrapper)
1. **MUST** fix all validation errors before pushing
1. **MUST** ensure all CI checks pass before requesting review

### For Reviewers

1. **MUST NOT** approve PRs with failing CI checks
1. **MUST** verify all 18+ CI checks are green ✅
1. **SHOULD** reject PRs with "skipped" security checks

### For Maintainers

1. **MUST** enforce branch protection rules on all protected branches
1. **MUST NOT** merge PRs with failing checks
1. **SHOULD** review security violation logs monthly

## Violation Tracking

All `--no-verify` attempts are logged:

**Location:** `.git/security-violations.log`

**Format:**

```
[2025-11-16 19:27:39] BLOCKED: git push --no-verify (user: developer1)
[2025-11-16 20:15:22] BLOCKED: git commit -m "fix" --no-verify (user: developer2)
```

**Review:** Monthly by tech leads

## Emergency Override Procedure

In **genuine emergencies only** (production down, security hotfix):

1. **Get approval** from 2 tech leads
1. **Document reason** in PR description
1. **Use this command** (requires admin):
   ```bash
   # Bypass wrapper (not recommended)
   /usr/bin/git push --no-verify
   ```
1. **Create follow-up PR** to fix validation issues within 24 hours

## Common Scenarios & Solutions

### Scenario 1: "Pre-push check failed on CHANGELOG.md formatting"

**Wrong:**

```bash
git push --no-verify  # ❌ BLOCKED
```

**Right:**

```bash
# Fix the formatting
mdformat --wrap 120 CHANGELOG.md

# Verify fix
./scripts/pre-push-check.sh

# Amend commit
git add CHANGELOG.md
git commit --amend --no-edit

# Push normally
git push
```

### Scenario 2: "Linting failed, I need to push urgently"

**Wrong:**

```bash
git push --no-verify  # ❌ BLOCKED, and CI will fail anyway!
```

**Right:**

```bash
# Auto-fix linting issues
./scripts/lint.sh .

# Commit fixes
git add -u
git commit --amend --no-edit

# Push (will succeed now)
git push
```

### Scenario 3: "Tests are failing but I want to create the PR for review"

**Wrong:**

```bash
git push --no-verify  # ❌ BLOCKED
```

**Right:**

```bash
# Option A: Mark PR as draft
git push  # Let it fail CI
# Then create PR as DRAFT on GitHub

# Option B: Skip tests that require specific environment
pytest -m "not integration"  # Run only unit tests locally

# Option C: Fix the tests
pytest -v  # See what's failing
# Fix the issues
git add -u
git commit --amend
git push
```

## Installation Guide

### For New Contributors

```bash
# 1. Clone repository
git clone https://github.com/Korrojo/python-projects.git
cd python-projects

# 2. Install git safety wrapper
./scripts/install-git-safety.sh

# 3. Install pre-commit and pre-push hooks
./scripts/install-hooks.sh

# 4. Verify setup
./scripts/pre-push-check.sh

# 5. (Optional) Add global alias
echo "alias git='$(pwd)/scripts/git-safe'" >> ~/.bashrc
source ~/.bashrc
```

### For Existing Contributors

```bash
# Update to latest
git pull origin main

# Install safety wrapper
./scripts/install-git-safety.sh

# Update hooks
./scripts/install-hooks.sh
```

## FAQ

### Q: Why can't I use --no-verify in emergencies?

**A:** Because:

1. The CI will fail anyway, so you're just delaying the inevitable
1. It creates technical debt that someone else has to clean up
1. It sets a bad precedent for other developers
1. 99% of "emergencies" are poor planning

**Better:** Fix the issue properly or create a DRAFT PR.

### Q: What if the pre-push check is broken?

**A:**

1. Report the issue in #dev-help
1. Fix the pre-push script itself
1. Create a PR to fix the check
1. Do NOT bypass it

### Q: This slows down my workflow!

**A:**

1. Pre-push checks run in \<30 seconds on average
1. CI failures waste hours of team time
1. Fixing broken CI wastes your time too
1. The checks catch real issues before they become problems

**Solution:** Run checks more frequently:

```bash
# Before committing
./scripts/lint.sh .

# Before pushing
./scripts/pre-push-check.sh
```

### Q: Can I disable this for my feature branch?

**A:** No. The policy applies to **all branches**. Branch protection rules will block merging anyway.

## Monitoring & Metrics

Track these metrics monthly:

- `--no-verify` block attempts (from `.git/security-violations.log`)
- CI failure rate on PRs
- Average time to fix CI failures
- Number of PRs merged with failing checks (should be 0)

**Goal:** Zero bypasses, \<5% CI failure rate

## Updates to This Policy

This policy may be updated by:

- Tech leads (for clarifications)
- Engineering managers (for enforcement changes)
- All hands vote (for major changes)

**Change log:** See git history of this file

## References

- [Pre-commit Hooks Guide](../docs/PRE_COMMIT_MIGRATION.md)
- [CI/CD Lessons Learned](../docs/best-practices/CI_CD_LESSONS_LEARNED.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Testing Guide](../docs/guides/TESTING_GUIDE.md)

______________________________________________________________________

**Last Updated:** 2025-11-16 **Policy Owner:** Tech Lead **Questions:** #dev-help channel
