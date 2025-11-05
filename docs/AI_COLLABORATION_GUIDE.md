# AI Collaboration Guide

**Purpose:** Provide this document to AI assistants at the start of new sessions to establish collaboration principles
and provide repository context.

**Version:** 1.1 **Last Updated:** 2025-11-02

______________________________________________________________________

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Quick Context](#quick-context)
- [Core Principles](#core-principles)
  - [1. Documentation First](#1-documentation-first)
  - [2. Explain, Don't Just Fix](#2-explain-dont-just-fix)
  - [3. Security is Non-Negotiable](#3-security-is-non-negotiable)
  - [4. Follow Standards](#4-follow-standards)
  - [5. Testing and Validation](#5-testing-and-validation)
- [Code Quality Tools Explained](#code-quality-tools-explained)
- [Essential Documentation (Read First)](#essential-documentation-read-first)
  - [Start Here](#start-here)
  - [Standards and Best Practices](#standards-and-best-practices)
  - [Reference Material](#reference-material)
- [Repository Structure](#repository-structure)
- [Standard CLI Pattern](#standard-cli-pattern)
- [Environment Configuration Pattern](#environment-configuration-pattern)
- \[Common Import Paths(⭐ Critical)\](#Common-Import-Paths-(⭐ Critical))
- [Common Patterns and Anti-Patterns](#common-patterns-and-anti-patterns)
  - [✅ DO](#-do)
  - [❌ DON'T](#-dont)
- [File Naming Conventions](#file-naming-conventions)
- [Todo List Management](#todo-list-management)
- [When User Opens Files](#when-user-opens-files)
- [Collaboration Workflow](#collaboration-workflow)
  - [When Starting a Task](#when-starting-a-task)
  - [During Implementation](#during-implementation)
  - [After Completion](#after-completion)
- [Error Handling Philosophy](#error-handling-philosophy)
- [Communication Style](#communication-style)
- [Project-Specific Notes](#project-specific-notes)
- [Git Workflow](#git-workflow)
- [Pre-Push Validation & Hooks](#pre-push-validation--hooks)
- [Quick Reference Card](#quick-reference-card)
- [Red Flags to Watch For](#red-flags-to-watch-for)
- [Summary Checklist](#summary-checklist)
- [Getting Help](#getting-help)
- [Related Documentation](#related-documentation)

</details>

______________________________________________________________________

## Quick Context

This is a **Python monorepo** with multiple production projects sharing:

- Virtual environment (`.venv311/`)
- Common configuration library (`common_config/`)
- Centralized data, logs, and artifacts
- Unified CI/CD and testing

**Key fact:** All projects follow strict standards documented in `docs/best-practices/` and `docs/guides/`.

______________________________________________________________________

## Core Principles

### 1. **Documentation First**

**DO:**

- ✅ Check existing documentation before implementing
- ✅ Consult `docs/guides/COMMON_CONFIG_API_REFERENCE.md` for correct import paths
- ✅ Follow `docs/best-practices/CLI_PATTERNS.md` for CLI implementations
- ✅ Update documentation when making changes
- ✅ Create documentation for new patterns

**DON'T:**

- ❌ Guess import paths (causes `ModuleNotFoundError`)
- ❌ Create new patterns without documenting them
- ❌ Skip reading existing guides
- ❌ Assume - verify with documentation

### 2. **Explain, Don't Just Fix**

**DO:**

- ✅ Explain WHY errors happened
- ✅ Explain HOW to prevent them in future
- ✅ Document root causes and prevention strategies
- ✅ Create lessons-learned documents when appropriate

**DON'T:**

- ❌ Just fix issues without explanation
- ❌ Skip root cause analysis
- ❌ Leave the user vulnerable to repeating the same mistake

**User's direct quote:**

> "please dont just fix things. Explain why it happened, and most importantly discuss what can be done to avoid this
> from happening in future projects."

### 3. **Security is Non-Negotiable**

**DO:**

- ✅ ALWAYS redact credentials in logs using `redact_uri()`
- ✅ Import from `common_config.utils.security`
- ✅ Review logs for credential exposure
- ✅ Use environment variables, never hardcode credentials
- ✅ Use `<placeholder>` syntax in documentation (e.g., `<username>:<password>`)

**DON'T:**

- ❌ NEVER log raw URIs, passwords, or API keys
- ❌ NEVER expose credentials in console output
- ❌ NEVER commit credentials to git
- ❌ NEVER use literal credential patterns in documentation (e.g., `user:password`)

**Documentation Security:**

- Use `<username>:<password>` NOT `user:password` in examples
- Literal patterns trigger GitHub Secret Scanning
- See SECURITY_PATTERNS.md lines 184-190 for approved patterns
- Previous incidents: 2025-10-28 (GitHub Secret Scanning alerts)

**Critical References:**

- `docs/best-practices/SECURITY_PATTERNS.md` - Comprehensive security guide
- `docs/best-practices/CLI_PATTERNS.md` - Security Requirements section

### 4. **Follow Standards**

**DO:**

- ✅ Use `--env` for environment switching (not `--mongodb-uri`, `--database`)
- ✅ Pass collection names via CLI `--collection` (never in `.env`)
- ✅ Follow file naming: `YYYYMMDD_HHMMSS_description.ext`
- ✅ Use standard CLI template from `docs/best-practices/CLI_PATTERNS.md`
- ✅ Follow monorepo structure and conventions

**DON'T:**

- ❌ Create project-specific .env files (use `shared_config/.env`)
- ❌ Create custom CLI patterns (use standard)
- ❌ Put collection names in configuration files
- ❌ Deviate from established patterns without discussion

### 5. **Testing and Validation**

**DO:**

- ✅ Run tests after making changes
- ✅ Verify commands work before claiming completion
- ✅ Test edge cases and error scenarios
- ✅ Run formatting (Black) and linting (Ruff) before committing
- ✅ Run type checking (Pyright) to catch type errors
- ✅ Use `./scripts/lint.sh` which runs all quality checks

**DON'T:**

- ❌ Skip testing
- ❌ Assume code works without verification
- ❌ Ignore linting errors
- ❌ Break existing tests
- ❌ Confuse Black (formatter) with Ruff (linter)

______________________________________________________________________

## Code Quality Tools Explained

**Three tools, three purposes:**

### 1. Black (Formatter) 🎨

**Purpose:** Automatically formats code to a consistent style

**Usage:**

```bash
black .              # Format all files
black --check .      # Check without modifying
black --diff .       # Show what would change
```

**In CI/CD:** `black --check --diff .` (line 42 of `.github/workflows/ci.yml`)

### 2. Ruff (Linter) 🔍

**Purpose:** Finds code quality issues, unused imports, etc.

**Usage:**

```bash
ruff check .         # Check for issues
ruff check . --fix   # Auto-fix issues
```

**In CI/CD:** `ruff check .` (line 45 of `.github/workflows/ci.yml`)

### 3. Pyright (Type Checker) 🔧

**Purpose:** Finds type errors and type inconsistencies

**Usage:**

```bash
pyright .            # Check types
pyright <file>       # Check specific file
```

**In CI/CD:** `pyright || true` (line 48 of `.github/workflows/ci.yml`, continues on error)

______________________________________________________________________

**CRITICAL RULE:**

- `scripts/lint.sh` MUST use the same tools and configuration as CI/CD
- CI/CD uses **Black for formatting** (not Ruff)
- Mismatch = push will fail CI/CD checks

______________________________________________________________________

## Essential Documentation (Read First)

### Start Here

1. **[README.md](../README.md)** - Repository overview, task-based navigation
1. **[SECURITY_PATTERNS.md](best-practices/SECURITY_PATTERNS.md)** ⭐⭐⭐ - Security guidelines (CRITICAL)
1. **[COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md)** ⭐⭐⭐ - Correct import paths
1. **[CLI_PATTERNS.md](best-practices/CLI_PATTERNS.md)** ⭐⭐ - Standard CLI patterns
1. **[NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md)** - Creating projects

### Standards and Best Practices

- **[SECURITY_PATTERNS.md](best-practices/SECURITY_PATTERNS.md)** - Security guidelines, credential handling
- **[CLI_PATTERNS.md](best-practices/CLI_PATTERNS.md)** - CLI standards (--env, --collection, security)
- **[FILE_NAMING_CONVENTIONS.md](best-practices/FILE_NAMING_CONVENTIONS.md)** - Output/log file naming
- **[IMPORT_PATH_ISSUES.md](best-practices/IMPORT_PATH_ISSUES.md)** - Common import errors
- **[CI_CD_LESSONS_LEARNED.md](best-practices/CI_CD_LESSONS_LEARNED.md)** - CI/CD best practices

### Reference Material

- **[MONGODB_VALIDATION_BEST_PRACTICES.md](best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md)** - MongoDB patterns
- **[REPOSITORY_LESSONS_LEARNED.md](best-practices/REPOSITORY_LESSONS_LEARNED.md)** - Organizational patterns
- **[TESTING_GUIDE.md](guides/TESTING_GUIDE.md)** - Testing strategies

______________________________________________________________________

## Repository Structure

```
python/
├── .venv311/              # Shared virtual environment (Python 3.11)
├── common_config/         # Shared configuration library
│   └── src/common_config/
│       ├── config/        # Settings management
│       ├── connectors/    # MongoDB, etc.
│       └── utils/         # Logging, security, file ops
├── data/
│   ├── input/<project>/   # Project input files
│   └── output/<project>/  # Project output files
├── logs/<project>/        # Project log files
├── docs/
│   ├── guides/            # How-to guides
│   └── best-practices/    # Reference material
├── scripts/               # Bootstrap and automation scripts
├── shared_config/.env     # Environment configuration
├── requirements.txt       # Shared dependencies
└── <project_name>/        # Individual projects
    ├── src/<project>/     # Project source code
    ├── tests/             # Project tests
    └── README.md          # Project documentation
```

______________________________________________________________________

## Standard CLI Pattern

**All CLI-based projects MUST follow this pattern:**

```python
import os
from pathlib import Path
import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri  # ⚠️ REQUIRED

app = typer.Typer(help="Description", no_args_is_help=True)

@app.command("command-name")
def command_name(
    env: str = typer.Option(None, "--env", help="Environment (DEV, PROD, STG)"),
    collection: str = typer.Option(None, "--collection", "-c", help="Collection name"),
):
    """Command description."""
    # 1. Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    # 2. Get settings
    settings = get_settings()
    setup_logging(Path(settings.paths.logs) / "project_name")
    logger = get_logger(__name__)

    # 3. Connect and execute
    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri,
            database_name=settings.database_name
        ) as client:
            # ⚠️ ALWAYS redact URIs in logs
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
            logger.info(f"Database: {settings.database_name}")

            # Your logic here

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise typer.Exit(code=1)
```

**See:** `docs/best-practices/CLI_PATTERNS.md` for complete details.

______________________________________________________________________

## Environment Configuration Pattern

**Standard `.env` setup:**

```bash
# Default environment
APP_ENV=DEV

# DEV environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=dev_database

# PROD environment
MONGODB_URI_PROD=mongodb+srv://<username>:<password>@cluster.mongodb.net/
DATABASE_NAME_PROD=production_database

# STG environment
MONGODB_URI_STG=mongodb+srv://<username>:<password>@cluster.mongodb.net/
DATABASE_NAME_STG=staging_database
```

**Usage:**

```bash
# Use default (DEV)
python project/run.py command

# Use PROD
python project/run.py command --env PROD

# Use STG
python project/run.py command --env STG
```

**How it works:** `common_config` automatically resolves `MONGODB_URI_<ENV>` → `MONGODB_URI` when `APP_ENV` is set.

______________________________________________________________________

## Common Import Paths (⭐ Critical)

**Always use these exact paths:**

```python
# Configuration
from common_config.config.settings import get_settings, AppSettings

# MongoDB
from common_config.connectors.mongodb import get_mongo_client, MongoDBConnector

# Logging
from common_config.utils.logger import get_logger, setup_logging, get_run_timestamp

# Security (⚠️ Required for credential safety)
from common_config.utils.security import redact_uri, redact_password, get_safe_connection_info

# File Operations
from common_config.utils.file_ops import ensure_dir, archive_file
```

**Why this is critical:** Wrong paths cause `ModuleNotFoundError`. See `docs/best-practices/IMPORT_PATH_ISSUES.md`.

______________________________________________________________________

## Common Patterns and Anti-Patterns

### ✅ DO

```python
# Use standard CLI options
python project/run.py command --env PROD --collection Users

# Redact credentials
logger.info(f"URI: {redact_uri(settings.mongodb_uri)}")

# Use environment-specific config
if env:
    os.environ["APP_ENV"] = env.upper()
settings = get_settings()

# Follow file naming
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{timestamp}_output_{database}.csv"

# Use context managers
with get_mongo_client(...) as client:
    # Work with database
```

### ❌ DON'T

```python
# Don't use custom options
python project/run.py command --mongodb-uri ... --database ...  # WRONG

# Don't log raw credentials
logger.info(f"URI: {settings.mongodb_uri}")  # SECURITY RISK

# Don't put collection names in .env
COLLECTION_NAME=Users  # WRONG - pass via CLI

# Don't hardcode environment values
mongodb_uri = "mongodb://prod-server:27017"  # WRONG

# Don't guess import paths
from common_config.db.mongo_client import ...  # WRONG PATH
```

______________________________________________________________________

## File Naming Conventions

**All output files and logs MUST use this pattern:**

```
YYYYMMDD_HHMMSS_description.ext
```

**Examples:**

- ✅ `20250128_143022_collection_stats_prod.csv`
- ✅ `20250128_143022_app.log`
- ✅ `20250128_143022_index_stats_dev.csv`
- ❌ `collection_stats_prod_20250128.csv` (timestamp not first)
- ❌ `output.csv` (no timestamp)

**Why:** Chronological sorting, easy cleanup, consistent across projects.

______________________________________________________________________

## Todo List Management

**Use the TodoWrite tool for:**

- Complex multi-step tasks (3+ steps)
- Tasks with dependencies
- User-provided task lists
- Long-running implementations

**Don't use for:**

- Single trivial tasks
- Purely conversational tasks
- Tasks completable in 1-2 steps

**Pattern:**

1. Create todos at task start
1. Mark ONE todo as in_progress before working on it
1. Mark completed IMMEDIATELY when done (don't batch)
1. Keep list current and accurate

______________________________________________________________________

## When User Opens Files

**The user opening a file in the IDE is a signal:**

- They may be reviewing your changes
- They may be about to ask about that file
- They may have found an issue
- Context: The file is relevant to current/next discussion

**Don't:** Immediately comment on every file opened. Wait for user's question/feedback.

______________________________________________________________________

## Collaboration Workflow

### When Starting a Task

1. **Understand the requirement** - Ask clarifying questions if needed
1. **Check existing patterns** - Review relevant documentation
1. **Plan if complex** - Use TodoWrite for multi-step tasks
1. **Explain approach** - Let user know your plan

### During Implementation

1. **Follow standards** - Use documented patterns
1. **Explain as you go** - Don't just code silently
1. **Update documentation** - Keep docs current
1. **Test your changes** - Verify they work

### After Completion

1. **Verify it works** - Test the implementation
1. **Explain what you did** - Summary of changes
1. **Document prevention** - How to avoid similar issues
1. **Update standards** - If new patterns emerged

______________________________________________________________________

## Error Handling Philosophy

**When errors occur:**

1. **Don't just fix** - Explain the root cause
1. **Prevent recurrence** - Document prevention strategy
1. **Update guides** - Add to relevant documentation
1. **Share lessons** - Create lessons-learned docs if needed

**Example:**

- Error: `ModuleNotFoundError: No module named 'common_config.db.mongo_client'`
- Fix: Change to `from common_config.connectors.mongodb import get_mongo_client`
- Prevention: Created `IMPORT_PATH_ISSUES.md` and updated `COMMON_CONFIG_API_REFERENCE.md`
- Result: Future developers avoid this mistake

______________________________________________________________________

## Communication Style

**DO:**

- ✅ Be concise but thorough
- ✅ Use code examples
- ✅ Explain reasoning
- ✅ Provide context
- ✅ Anticipate follow-up questions

**DON'T:**

- ❌ Be overly verbose
- ❌ Use emojis unless user does
- ❌ Assume user knows internal details
- ❌ Skip explanations

______________________________________________________________________

## Project-Specific Notes

### db_collection_stats

- Purpose: MongoDB collection and index statistics gathering
- Commands: `coll-stats` (all collections), `index-stats` (index analysis)
- Uses: Standard CLI pattern, CSV export, credential redaction
- Documentation: `db_collection_stats/README.md`

### common_config

- Purpose: Shared configuration and utilities library
- Key modules: settings, connectors, utils (logger, security, file_ops)
- Used by: All projects in the monorepo
- Documentation: `docs/guides/COMMON_CONFIG_API_REFERENCE.md`

______________________________________________________________________

## Git Workflow

⚠️ **CRITICAL: Feature Branches Are MANDATORY**

**NEVER commit directly to `main` or `master` branches.** This is the #1 most important git workflow rule.

### STEP 1: Create Feature Branch (ALWAYS DO THIS FIRST)

**Before starting ANY new work:**

```bash
# 1. Sync with main
git checkout main
git pull origin main

# 2. Create and checkout feature branch (MANDATORY)
git checkout -b feature/your-feature-name
# OR for bug fixes
git checkout -b fix/bug-description

# 3. Verify you're on the feature branch
git branch --show-current
```

**Branch naming convention:**

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### STEP 2: Commit Changes

**When committing:**

- Only commit when user explicitly asks
- Follow commit message pattern from git history
- Include footer: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
- Add co-author: `Co-Authored-By: Claude <noreply@anthropic.com>`
- Check git status before and after

### STEP 3: Create Pull Request

**After completing work:**

1. Push feature branch: `git push origin feature/your-feature-name`
1. Create pull request on GitHub
1. Wait for review and approval
1. Maintainer will merge to main

**Why feature branches matter:**

- ✅ Keeps main branch stable and production-ready
- ✅ Enables code review through pull requests
- ✅ Allows multiple features to be developed in parallel
- ✅ Makes it easy to abandon or iterate on changes
- ✅ Provides clear history and attribution

**Protection:**

A pre-commit hook prevents commits to main/master. Install hooks with:

```bash
./scripts/install-hooks.sh
```

**See also:** Git Safety Protocol in Bash tool description, CONTRIBUTING.md Development Workflow section

______________________________________________________________________

## Pre-Push Validation & Hooks

**Automatic Safety Net:**

The repository has an automatic pre-push hook that validates code before pushing.

**Location:** `.git/hooks/pre-push`

**What it does:**

1. Activates virtual environment (.venv311 or .venv312)
1. Runs `scripts/lint.sh`:
   - Black (formatter)
   - Ruff (linter)
   - Pyright (type checker)
1. Runs tests: `pytest -q --maxfail=1 --disable-warnings -m "not integration"`
1. Checks for cross-platform issues

**Manual execution:**

```bash
./scripts/pre-push-check.sh
```

**To bypass (NOT recommended):**

```bash
git push --no-verify
```

**CRITICAL:** Never bypass unless emergency. Always fix issues instead.

**Why this matters:**

- Catches issues before they reach CI/CD
- Prevents failed builds
- Ensures code quality standards
- Saves time by catching errors early

______________________________________________________________________

## Quick Reference Card

⚠️ **BEFORE STARTING ANY WORK:** → Create feature branch: `git checkout -b feature/name`

**When user asks to create a new CLI project:** → Use template from `docs/best-practices/CLI_PATTERNS.md`

**When user reports import error:** → Check `docs/guides/COMMON_CONFIG_API_REFERENCE.md` for correct path

**When user wants to add new functionality:** → Check if pattern exists, if not discuss and document

**When credentials appear in logs:** → Implement `redact_uri()` immediately

**When user says "document this":** → Add to existing docs or create new doc in `docs/best-practices/`

**When user opens a file:** → Wait for their question/feedback, don't proactively comment

**When user says "fix tests":** → Run tests, fix issues, explain what broke and why

**Before committing:** → Verify branch: `git branch --show-current` (must NOT be main/master)

______________________________________________________________________

## Red Flags to Watch For

🚨 **Immediate action required:**

- Credentials in logs
- Import errors (check API reference)
- Hardcoded environment values
- Non-standard CLI patterns
- Missing documentation for new patterns
- Skipped security utilities

🚨 **Documentation Security:**

- Literal credential patterns in docs (`user:password` instead of `<username>:<password>`)
- Realistic-looking credentials (triggers GitHub Secret Scanning)
- MongoDB URIs with credentials: `mongodb://user:pass@host` (use placeholders)
- API keys or tokens in examples without placeholders

🚨 **Git Workflow (CRITICAL):**

- Working directly on `main` or `master` branch without feature branch
- Committing to protected branches
- Skipping feature branch creation before starting work
- Not verifying current branch before committing

🚨 **Code Quality:**

- Local `lint.sh` doesn't match CI/CD configuration
- Using Ruff for formatting when CI/CD expects Black
- Skipping formatter checks before committing
- Pre-push hook bypassed (`--no-verify`)

⚠️ **Discussion needed:**

- Creating new patterns vs. using existing
- Deviating from standards
- Adding new dependencies
- Major architectural changes

______________________________________________________________________

## Summary Checklist

Before considering a task complete:

**Git Workflow (CRITICAL - Check FIRST):**

- [ ] **Feature branch created BEFORE starting work**
- [ ] Verified current branch: `git branch --show-current`
- [ ] NOT working on `main` or `master` directly
- [ ] Branch follows naming convention (feature/, fix/, docs/, etc.)

**Code Quality:**

- [ ] Code follows standards in `docs/best-practices/`
- [ ] Correct import paths from `COMMON_CONFIG_API_REFERENCE.md`
- [ ] Standard CLI pattern used if applicable
- [ ] Tests pass
- [ ] Black used for formatting (not Ruff)
- [ ] Pre-push validation passes
- [ ] Local `lint.sh` matches CI/CD (`.github/workflows/ci.yml`)

**Security:**

- [ ] Credentials redacted in all logs
- [ ] Documentation uses `<placeholder>` syntax for all credentials
- [ ] No literal credential patterns (user:password, API keys, etc.)
- [ ] Searched for patterns: `grep -r "mongodb.*://.*:.*@" docs/`
- [ ] No hardcoded values

**Documentation:**

- [ ] Documentation updated
- [ ] Root cause explained
- [ ] Prevention strategy documented
- [ ] File naming conventions followed

______________________________________________________________________

## Getting Help

**If uncertain:**

1. Search `docs/` for relevant guides
1. Check `docs/README.md` for documentation index
1. Ask user for clarification
1. Don't guess - verify

**Master documentation hub:** `README.md` at repository root

**Complete documentation index:** `docs/README.md`

______________________________________________________________________

## Related Documentation

**Essential Reading:**

- [SECURITY_PATTERNS.md](best-practices/SECURITY_PATTERNS.md) ⭐⭐⭐ - Security guidelines
- [CLI_PATTERNS.md](best-practices/CLI_PATTERNS.md) - CLI standards
- [COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths
- [FILE_NAMING_CONVENTIONS.md](best-practices/FILE_NAMING_CONVENTIONS.md) - Output file naming

**Standards & Patterns:**

- [DOCUMENTATION_STANDARDS.md](best-practices/DOCUMENTATION_STANDARDS.md)
- [IMPORT_PATH_ISSUES.md](best-practices/IMPORT_PATH_ISSUES.md)
- [MONGODB_VALIDATION_BEST_PRACTICES.md](best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md)

**CI/CD & Infrastructure:**

- [CI_CD_LESSONS_LEARNED.md](best-practices/CI_CD_LESSONS_LEARNED.md)
- `.github/workflows/ci.yml` - CI/CD pipeline configuration
- `.github/REPOSITORY_SETUP.md` - Repository setup guide

**Scripts:**

- `scripts/lint.sh` - Local code quality checks
- `scripts/pre-push-check.sh` - Pre-push validation
- `.git/hooks/pre-push` - Automatic pre-push hook

______________________________________________________________________

**Questions?** Ask the user. Better to clarify than to assume incorrectly.

**Remember:** The goal is collaboration, not just code completion. Teach, explain, and prevent future issues.
