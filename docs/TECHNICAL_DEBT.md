# Technical Debt Tracking

This document tracks known technical debt across the monorepo. Items are categorized by severity and project.

**Last Updated:** 2025-11-09

______________________________________________________________________

## 🔴 P0: Critical (Security/Correctness)

### Type Safety Issues - Pyright Errors

**Affected Projects:** mongo_phi_masker, db_collection_stats, common_config, mongodb_test_data_tools,
patients_hcmid_validator

**Count:** 75+ type errors

**Description:** Multiple type safety issues across projects:

- `str | None` assigned to `str` parameters (runtime crashes if None passed)
- Optional attribute access without guards (potential AttributeError)
- Missing type annotations
- Incompatible type assignments

**Example:**

```python
# mongo_phi_masker/src/core/connector.py:57
def connect(database: str):  # Expects str
    ...


database_name: str | None = get_db()
connector.connect(database_name)  # ❌ Could pass None → runtime crash
```

**Impact:**

- **Runtime failures** when None values passed to functions expecting str
- **Silent bugs** in production
- **Difficult debugging** due to missing type information

**Mitigation (Current):**

- Pyright runs in manual mode only (`pre-commit run pyright`)
- Not blocking commits/pushes
- Errors tracked here for gradual fixes

**Action Items:**

1. [ ] Audit all `str | None` → `str` assignments
1. [ ] Add type guards where needed
1. [ ] Update function signatures to accept Optional types
1. [ ] Add proper None checks before passing to functions
1. [ ] Enable pyright on pre-push once errors \< 10

**Priority:** P0 - These can cause runtime crashes

**Estimated Effort:** 2-3 weeks (75 errors × ~15 min each)

**Tracking Issue:** \[Create GitHub issue\]

______________________________________________________________________

## 🟡 P1: Important (Code Quality)

### Ruff Linting Issues (Non-E402)

**Affected Projects:** PatientOtherDetail_isActive_false, db_collection_stats, mongodb_index_tools

**Count:** 6 errors

**Description:**

```
PatientOtherDetail_isActive_false/verify_updates.py:194:69: E712 Comparison to `True` should be `cond is True` or `if cond:`
PatientOtherDetail_isActive_false/verify_updates.py:195:70: E712 Comparison to `False` should be `cond is False` or `if not cond:`
db_collection_stats/run.py:16:1: E402 Module level import not at top of file
mongodb_index_tools/run.py:20:1: E402 Module level import not at top of file
```

**Impact:**

- E712: Non-Pythonic boolean comparisons (minor)
- E402 in non-run.py files: Unexpected import ordering

**Action Items:**

1. [ ] Fix E712 boolean comparisons (5 min fix)
1. [ ] Investigate E402 in db_collection_stats/run.py and mongodb_index_tools/run.py
1. [ ] Determine if E402 is intentional or should be fixed

**Priority:** P1 - Code quality, not critical

**Estimated Effort:** 1 hour

______________________________________________________________________

## 🟢 P2: Nice to Have (Optimization)

### Intentional Patterns (Accepted Technical Debt)

#### E402 in run.py Files

**Status:** ✅ Accepted as intentional pattern

**Description:** All projects use `run.py` as entry point with sys.path manipulation:

```python
# Pattern in all run.py files
import sys

sys.path.insert(0, str(PROJECT_ROOT))
from src.module import something  # E402: Import after code
```

**Rationale:**

- Projects are standalone applications, not installable packages
- Only `common_config` is meant to be installed
- sys.path manipulation is necessary for monorepo structure
- Converting all to installable packages is overkill

**Mitigation:**

- `.ruff.toml`: `"*/run.py" = ["E402"]` (ignored only in run.py files)
- Pattern documented and accepted
- Not treated as technical debt

______________________________________________________________________

## Debt Reduction Strategy

### Phase 1: Critical Type Errors (P0)

**Timeline:** Next 2 sprints

- Focus on mongo_phi_masker (most active project)
- Fix `str | None` → `str` issues
- Add type guards for Optional handling

### Phase 2: Code Quality (P1)

**Timeline:** After Phase 1

- Fix remaining linting issues
- Standardize boolean comparisons

### Phase 3: Monitoring (Ongoing)

- Run `pre-commit run pyright` monthly
- Track new type errors in code reviews
- Gradually enable pyright on pre-push

______________________________________________________________________

## Tracking & Reporting

### Weekly Review

Run technical debt audit:

```bash
# Check type errors
pre-commit run pyright --all-files 2>&1 | grep "errors, .* warnings"

# Check linting issues
pre-commit run ruff --all-files 2>&1 | grep "Found .* errors"
```

### Monthly Report

Update this document with:

- Errors fixed
- New errors introduced
- Progress toward enabling stricter checks

### GitHub Integration

Create issues for each category:

- `tech-debt/type-safety` - P0 type errors
- `tech-debt/code-quality` - P1 linting issues

______________________________________________________________________

## References

- [.ruff.toml](../.ruff.toml) - Ruff configuration
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Hook configuration
- [pyrightconfig.json](../pyrightconfig.json) - Pyright configuration (if exists)

______________________________________________________________________

## Appendix: Full Error List

### Pyright Errors by Project

#### mongo_phi_masker (14 errors)

```
masking.py:508:19 - int vs str in log_level
masking.py:630:53 - str | None vs str in database param
masking.py:631:56 - str | None vs str in database param
masking.py:699:57 - Missing estimated_document_count on MongoConnector
masking.py:1043:35 - psutil possibly unbound
masking.py:1057:46 - with_options not known on None
masking.py:1060:51 - with_options not known on None
masking.py:1080:52 - process possibly unbound
masking.py:1095:50 - process possibly unbound
masking.py:1174:55 - process possibly unbound
src/core/connector.py:57-270 - 20+ str | None vs str issues
src/models/masking_rule.py:392-446 - 15+ type errors
src/utils/logger.py:41-140 - 4 type errors
```

#### db_collection_stats (6 errors)

```
cli.py:69:63 - str | None vs str in database_name
cli.py:74:39 - str | None vs str in database_name
cli.py:80:66 - str | None vs str in database_name
cli.py:233:82 - str | None vs str in database_name
exporter.py:67:24 - float vs int
```

#### common_config (5 errors)

```
__init__.py:7-10 - 4 warnings about __all__
utils/security.py:136:13 - int | None vs str
```

#### mongodb_test_data_tools (3 errors)

```
run.py:37:25 - Type expression error
run.py:106:28 - str | None vs str
run.py:107:27 - str | None vs str
```

#### patients_hcmid_validator (7 errors)

```
mongo_fetch.py:9:12 - dict type mismatch
runner.py:172:26 - openpyxl possibly unbound
runner.py:185:43 - iter_rows unknown
runner_excel.py:63:25 - openpyxl possibly unbound
runner_excel.py:71:41 - iter_rows unknown
runner_excel.py:73:42 - iter_rows unknown
runner_mixed_backup.py:187:47 - iter_rows unknown
```

______________________________________________________________________

**Total Technical Debt:**

- 🔴 P0: 75+ type errors (2-3 weeks effort)
- 🟡 P1: 6 linting issues (1 hour effort)
- 🟢 P2: 0 (E402 accepted as pattern)

**Progress:** 0% (baseline established 2025-11-09)
