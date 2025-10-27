# CI/CD Lessons Learned

**Date:** 2025-10-27
**Issue:** Main branch had failing CI that broke all PRs

---

## What Happened

The main branch had 3 failing CI checks:
1. **Ruff Linting (N999)** - Module naming convention violation
2. **Windows mkdir** - Used bash-specific command
3. **Windows PowerShell** - Multiline command syntax broke PowerShell parsing

All 6 Dependabot PRs inherited these failures because they branched from broken main.

---

## Root Causes

### 1. No Pre-Push Validation
- Changes were pushed without running local CI checks
- `./scripts/lint.sh` was not run before committing
- Tests passed locally but Windows-specific issues weren't caught

### 2. Windows-Specific Issues Not Tested Locally
- Development on macOS/Linux doesn't catch Windows CI issues
- GitHub Actions Windows runner uses PowerShell by default
- Bash syntax in workflows breaks on Windows

### 3. Cross-Platform Syntax Not Used
- Used `mkdir -p` instead of Python `os.makedirs()`
- Used multiline bash commands with `\` instead of single-line
- Didn't explicitly specify `shell: bash` when needed

---

## The Fixes

### Fix #1: Ruff N999 Exception
**Problem:** `staff_appointment_visitStatus` violates PEP-8 naming (should be lowercase)

**Solution:** Added exception in `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
"staff_appointment_visitStatus/**" = ["N999"]  # Legacy project naming
```

### Fix #2: Cross-Platform mkdir
**Problem:** `mkdir -p artifacts/coverage` fails on Windows

**Solution:** Use Python instead:
```yaml
- name: Create artifacts directory
  run: |
    python -c "import os; os.makedirs('artifacts/coverage', exist_ok=True)"
```

### Fix #3: Single-Line Commands
**Problem:** PowerShell interprets `--` as decrement operator in multiline commands

**Before (broken on Windows):**
```yaml
run: |
  pytest -q \
    --maxfail=1 \
    --disable-warnings
```

**After (works everywhere):**
```yaml
run: pytest -q --maxfail=1 --disable-warnings
```

---

## Prevention Strategy

### A. Pre-Push Validation (REQUIRED)

**Before every push to main, run:**
```bash
# 1. Activate venv
source .venv311/bin/activate

# 2. Run validation script
./scripts/pre-push-check.sh

# 3. Only push if validation passes
git push
```

### B. Pre-Commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "Running pre-commit checks..."
./scripts/lint.sh
exit $?
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### C. GitHub Actions Best Practices

**1. Always write cross-platform commands:**
```yaml
# ❌ DON'T: Bash-specific
run: mkdir -p dir/subdir

# ✅ DO: Cross-platform Python
run: python -c "import os; os.makedirs('dir/subdir', exist_ok=True)"
```

**2. Use single-line commands in PowerShell:**
```yaml
# ❌ DON'T: Multiline with backslashes
run: |
  command \
    --option1 \
    --option2

# ✅ DO: Single line
run: command --option1 --option2

# ✅ OR: Explicit bash
- name: Run command
  shell: bash
  run: |
    command \
      --option1 \
      --option2
```

**3. Test matrix includes Windows:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.11", "3.12"]
```

---

## Checklist: Before Pushing to Main

- [ ] Virtual environment activated
- [ ] Run `./scripts/pre-push-check.sh`
- [ ] All linting checks pass
- [ ] All tests pass locally
- [ ] Review workflow YAML for cross-platform issues
- [ ] Check that CI passed on previous commit
- [ ] Consider impact on open PRs

---

## Tools Created

### scripts/pre-push-check.sh
Automated validation script that checks:
- Virtual environment activation
- Code quality (Ruff, Black)
- All tests passing
- Common cross-platform issues in workflows

**Usage:**
```bash
./scripts/pre-push-check.sh
```

---

## Handling Broken Main Branch

**If main branch CI is broken:**

1. **Fix it immediately** - Don't merge more PRs
2. **All open PRs will fail** - They inherit the broken base
3. **After fixing main:**
   - Close all affected PRs
   - Let Dependabot recreate them
   - OR manually rebase each PR

**Command to close all PRs:**
```bash
gh pr close 1 2 3 4 5 6 --comment "Closing to rebase against fixed main"
```

---

## Key Takeaways

1. **Never skip local validation** - Always run lint and tests before pushing
2. **Write cross-platform CI from the start** - Use Python, not bash commands
3. **Test on all platforms** - If you have Windows in CI matrix, be mindful of syntax
4. **Keep main branch green** - Broken main breaks all PRs
5. **Use pre-commit hooks** - Automate validation to prevent mistakes

---

**Last Updated:** 2025-10-27
