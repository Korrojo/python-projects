# Lessons Learned: Import Path Issues in New Projects

**Date:** January 2025 **Context:** db_collection_stats project - MongoDB client import error

______________________________________________________________________

## What Happened

When running the newly scaffolded `db_collection_stats` project, encountered:

```
ModuleNotFoundError: No module named 'common_config.db.mongo_client'
```

The code had:

```python
from common_config.db.mongo_client import get_mongo_client  # WRONG PATH
```

But the correct import path is:

```python
from common_config.connectors.mongodb import get_mongo_client  # CORRECT PATH
```

______________________________________________________________________

## Root Cause Analysis

### What Actually Happened

1. **CLI Template is Generic** - The `common` CLI scaffolds projects with a generic `run.py` template that only includes
   basic imports (logger, settings). This is **by design** - not all projects need MongoDB.

1. **Manual Addition = Guessed Import Path** - When manually adding MongoDB functionality, I guessed the import path
   instead of checking the actual common_config codebase.

1. **No Developer Reference** - There was no documentation showing correct import paths for common_config functionality.

### Why This is a Recurring Problem

This will happen EVERY time someone:

- Adds MongoDB functionality to a new project
- Adds any non-scaffolded common_config feature
- Works on a project type they haven't built before
- Doesn't have the import paths memorized

### The Real Issue

**Lack of developer reference documentation for common_config API patterns.**

______________________________________________________________________

## The Solution: Three-Layer Prevention

### Layer 1: API Reference Documentation ✅

**Created:** `docs/guides/COMMON_CONFIG_API_REFERENCE.md`

This document provides:

- ✅ Correct import paths for all common_config modules
- ✅ Usage patterns and code examples
- ✅ Common project templates (basic, MongoDB, data processing)
- ✅ Troubleshooting section for common import errors
- ✅ Quick copy-paste patterns

**When to use:**

- Before adding any common_config functionality to a new project
- When encountering import errors
- As a quick reference during development

### Layer 2: Update NEW_PROJECT_GUIDE.md

Add a prominent section about using the API reference:

**Action Required:** Update `docs/guides/NEW_PROJECT_GUIDE.md` with:

```markdown
## Step 7: Add Project-Specific Functionality

Before adding imports from common_config, **ALWAYS** consult:
📖 [COMMON_CONFIG_API_REFERENCE.md](COMMON_CONFIG_API_REFERENCE.md)

This prevents import path errors and ensures you use correct patterns.

Common features:
- MongoDB connection → See "Database Connectors" section
- File operations → See "File Operations" section
- Custom logging → See "Logging" section
```

### Layer 3: Add to common_config README

**Action Required:** Update `common_config/README.md` with import examples at the top.

______________________________________________________________________

## Prevention Checklist

When adding common_config functionality to a new project:

- [ ] **STOP** - Don't guess the import path
- [ ] **CHECK** the API Reference: `docs/guides/COMMON_CONFIG_API_REFERENCE.md`
- [ ] **COPY** the correct import and usage pattern
- [ ] **TEST** the import works before proceeding

______________________________________________________________________

## Common Import Errors & Fixes

### 1. MongoDB Client

```python
# ❌ WRONG - Old/guessed path
from common_config.db.mongo_client import get_mongo_client

# ✅ CORRECT
from common_config.connectors.mongodb import get_mongo_client
```

### 2. Settings

```python
# ❌ WRONG
from common_config.settings import get_settings

# ✅ CORRECT
from common_config.config.settings import get_settings
```

### 3. Logger

```python
# ❌ WRONG
from common_config.logger import get_logger

# ✅ CORRECT
from common_config.utils.logger import get_logger, setup_logging
```

______________________________________________________________________

## For Maintainers

### When Refactoring common_config

If you move/rename modules in common_config:

1. **Update the API Reference immediately**

   - File: `docs/guides/COMMON_CONFIG_API_REFERENCE.md`
   - Update import paths and examples

1. **Search for old imports across all projects**

   ```bash
   grep -r "from common_config" */run.py
   ```

1. **Add deprecation warnings** (if possible)

   ```python
   import warnings
   warnings.warn(
       "common_config.db.mongo_client is deprecated. "
       "Use common_config.connectors.mongodb instead",
       DeprecationWarning
   )
   ```

1. **Update the CLI template** if the change affects common scaffolding

### Template Maintenance

The CLI template location: `common_config/src/common_config/cli/main.py` (lines 90-113)

**Current design:** Template is intentionally minimal (only logger + settings)

**Should stay this way** because:

- Not all projects need MongoDB
- Not all projects need file operations
- Forces developers to consciously add what they need
- Prevents bloat in simple projects

______________________________________________________________________

## Testing New Projects

After scaffolding a new project:

1. **Run smoke tests immediately**

   ```bash
   pytest <project>/tests/ -v
   ```

1. **Add imports incrementally**

   - Add one import
   - Test it works
   - Then add the next

1. **Use the API Reference**

   - Don't guess
   - Copy from examples

______________________________________________________________________

## Impact Analysis

**Before this fix:**

- ❌ Every new MongoDB project would hit this error
- ❌ Developer has to debug import paths
- ❌ No central reference to consult
- ❌ Time wasted on same issue repeatedly

**After this fix:**

- ✅ API Reference provides correct paths immediately
- ✅ Copy-paste patterns prevent errors before they happen
- ✅ Clear troubleshooting for when errors occur
- ✅ Self-service solution - no need to ask for help

______________________________________________________________________

## Related Documentation

- [COMMON_CONFIG_API_REFERENCE.md](../guides/COMMON_CONFIG_API_REFERENCE.md) - THE reference for import paths
- [NEW_PROJECT_GUIDE.md](../guides/NEW_PROJECT_GUIDE.md) - Project scaffolding guide
- [CI_CD_LESSONS_LEARNED.md](CI_CD_LESSONS_LEARNED.md) - CI/CD best practices

______________________________________________________________________

## Summary

**The Problem:** Import path errors when adding common_config functionality to new projects.

**Root Cause:** Lack of developer reference documentation.

**The Fix:** Created comprehensive API Reference guide with correct import paths, usage patterns, and troubleshooting.

**Prevention:** Always consult `docs/guides/COMMON_CONFIG_API_REFERENCE.md` before adding imports.

**Key Insight:** Documentation prevents problems better than fixing them after they occur.
