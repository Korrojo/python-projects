# Security Patterns and Best Practices

**Purpose:** Document security patterns, common vulnerabilities, and prevention strategies for this repository.

**Version:** 1.0
**Last Updated:** 2025-10-28

---

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Overview](#overview)
- [1. Credential Management](#1-credential-management)
  - [Never Commit Credentials](#never-commit-credentials)
  - [Environment Variables Pattern](#environment-variables-pattern)
  - [Credential Redaction in Logs](#credential-redaction-in-logs)
- [2. Documentation Security](#2-documentation-security)
  - [Example Credentials in Documentation](#example-credentials-in-documentation)
  - [GitHub Secret Scanning](#github-secret-scanning)
  - [Approved Placeholder Patterns](#approved-placeholder-patterns)
- [3. .gitignore Best Practices](#3-gitignore-best-practices)
  - [Data Files](#data-files)
  - [Log Files](#log-files)
  - [Environment Files](#environment-files)
- [4. Security Utilities](#4-security-utilities)
  - [Available Tools](#available-tools)
  - [Usage Examples](#usage-examples)
- [5. Security Checklist](#5-security-checklist)
  - [Before Committing Code](#before-committing-code)
  - [Before Writing Documentation](#before-writing-documentation)
  - [Before Logging Information](#before-logging-information)
- [Incident Log](#incident-log)
- [Related Documentation](#related-documentation)

</details>

---

## Overview

Security is non-negotiable in this repository. This document provides practical patterns and guidelines to prevent common security vulnerabilities, particularly around credential management and data exposure.

**Key Principles:**
1. **Never commit credentials** - Use environment variables and `.gitignore`
2. **Never log credentials** - Use redaction utilities for all logging
3. **Never use real-looking credentials in docs** - Use placeholder syntax
4. **Verify before pushing** - Pre-push hooks catch many issues

---

## 1. Credential Management

### Never Commit Credentials

**❌ NEVER do this:**
```python
# Hardcoded credentials (NEVER!)
MONGODB_URI = "mongodb+srv://admin:SuperSecret123@cluster.mongodb.net/"
API_KEY = "sk-proj-abc123xyz789"
```

**✅ ALWAYS do this:**
```python
# Use environment variables
import os
from common_config.config.settings import get_settings

settings = get_settings()
mongodb_uri = settings.mongodb_uri  # Loaded from .env
api_key = os.environ.get("API_KEY")
```

### Environment Variables Pattern

**File: `shared_config/.env`** (gitignored)
```bash
# Default environment
APP_ENV=DEV

# DEV environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=dev_database
API_KEY_DEV=dev_key_value

# PROD environment
MONGODB_URI_PROD=mongodb+srv://<actual_prod_credentials>
DATABASE_NAME_PROD=production_database
API_KEY_PROD=<actual_prod_key>
```

**Why this works:**
- `.env` files are gitignored
- Credentials never touch version control
- Easy to rotate without code changes
- Different credentials per environment

### Credential Redaction in Logs

**⚠️ CRITICAL:** Always redact credentials before logging.

**❌ NEVER do this:**
```python
logger.info(f"Connecting to: {settings.mongodb_uri}")
# Logs: mongodb+srv://user:password@host/... ← EXPOSES CREDENTIALS!
```

**✅ ALWAYS do this:**
```python
from common_config.utils.security import redact_uri

logger.info(f"Connecting to: {redact_uri(settings.mongodb_uri)}")
# Logs: mongodb+srv://***:***@host/... ← Safe!
```

**Why credential logging is dangerous:**
- Credentials visible in log files
- Credentials visible in CI/CD logs (GitHub Actions, Jenkins, etc.)
- Credentials sent to error tracking systems (Sentry, Rollbar, etc.)
- Compliance violations (SOC2, GDPR, HIPAA, etc.)
- Security incident if logs are compromised or shared

---

## 2. Documentation Security

### Example Credentials in Documentation

**🚨 INCIDENT (2025-10-28):** GitHub Secret Scanning detected "credential leaks" in documentation that were actually just examples.

**Problem:** Using realistic-looking credential patterns in documentation triggers automated security scanning.

**❌ NEVER use these patterns in documentation:**
```markdown
mongodb+srv://user:password@cluster.mongodb.net/
mongodb://admin:secret@localhost:27017
postgres://username:pass123@db.example.com:5432
API_KEY=sk-proj-abc123xyz789
```

**✅ ALWAYS use placeholder syntax:**
```markdown
mongodb+srv://<username>:<password>@cluster.mongodb.net/
mongodb://<username>:<password>@localhost:27017
postgres://<username>:<password>@db.example.com:5432
API_KEY=<your_api_key>
```

### GitHub Secret Scanning

**What it detects:**
- MongoDB Atlas URIs with credentials
- AWS access keys
- GitHub personal access tokens
- API keys from popular services
- Private keys and certificates
- Database connection strings with credentials

**How it works:**
- Automated scanning on every push
- Pattern matching against known credential formats
- Cannot distinguish real credentials from examples
- Alerts opened immediately for matches

**When alerts occur:**
1. GitHub opens a security alert
2. Alert shows file, line number, and pattern matched
3. Repository owner notified
4. Alert marked "Public leak" if in public repo

**Resolution:**
- Fix the pattern in documentation (use placeholders)
- Push the fix
- GitHub re-scans and auto-closes alert if pattern removed

### Approved Placeholder Patterns

Use these patterns in documentation to avoid triggering secret scanning:

| Type | ❌ Avoid | ✅ Use Instead |
|------|----------|----------------|
| **MongoDB URI** | `mongodb://user:pass@host` | `mongodb://<username>:<password>@host` |
| **Username/Password** | `user:password` | `<username>:<password>` |
| **API Key** | `sk-proj-abc123` | `<your_api_key>` or `YOUR_API_KEY` |
| **AWS Credentials** | `AKIA...` | `<AWS_ACCESS_KEY_ID>` |
| **Generic Secret** | `secret123` | `<secret_value>` or `***` |

**Pattern Rules:**
1. Use angle brackets: `<placeholder_name>`
2. Use descriptive names: `<username>` not `<user>`
3. Use uppercase for environment variables: `<YOUR_API_KEY>`
4. Use `***` when showing redacted output examples

---

## 3. .gitignore Best Practices

### Data Files

**Always exclude data files from version control:**

```gitignore
# Data directories - exclude content, keep structure
/data/input/*
!/data/input/.gitkeep
!/data/input/*/

/data/output/*
!/data/output/.gitkeep
!/data/output/*/

# Data files in subdirectories (IMPORTANT!)
/data/input/**/*.csv
/data/input/**/*.xlsx
/data/input/**/*.json
/data/output/**/*.csv
/data/output/**/*.xlsx
/data/output/**/*.json
```

**Why subdirectory patterns matter:**
- `/data/*.csv` only excludes root-level CSVs
- `/data/**/*.csv` excludes CSVs in all subdirectories
- Without `**` pattern, files in subdirectories get committed

**Verification before committing:**
```bash
# Dry-run to see what would be added
git add -n data/

# Should only show .gitkeep files, no CSVs/data files
```

### Log Files

```gitignore
# Logs directory
/logs/
*.log

# Specific log patterns
**/*.log
**/logs/
```

### Environment Files

```gitignore
# Environment files (CRITICAL!)
.env
.env.*
!.env.template
!.env.example

# Project-specific configs
shared_config/.env
shared_config/.env.*
*/config/.env
*/config/.env.*
```

---

## 4. Security Utilities

### Available Tools

**Import from:**
```python
from common_config.utils.security import (
    redact_uri,              # Redact credentials from URIs
    redact_password,         # Redact passwords from text
    get_safe_connection_info,  # Get safe connection info dict
)
```

### Usage Examples

#### `redact_uri(uri: str, mask: str = "***") -> str`

Redact credentials from connection URIs.

```python
from common_config.utils.security import redact_uri

# MongoDB URIs
uri = "mongodb+srv://admin:secret123@cluster.mongodb.net/"
safe_uri = redact_uri(uri)
# Returns: "mongodb+srv://***:***@cluster.mongodb.net/"

# PostgreSQL
uri = "postgresql://user:pass@localhost:5432/mydb"
safe_uri = redact_uri(uri)
# Returns: "postgresql://***:***@localhost:5432/mydb"

# Safe for logging
logger.info(f"Connecting to: {redact_uri(settings.database_uri)}")
```

#### `redact_password(text: str, mask: str = "***") -> str`

Redact passwords from text using common patterns.

```python
from common_config.utils.security import redact_password

# Redact from connection strings or logs
text = "Connection failed: password=secret123"
safe_text = redact_password(text)
# Returns: "Connection failed: password=***"

# Works with various patterns
redact_password("PWD=secret")      # → "PWD=***"
redact_password("password: abc")    # → "password: ***"
```

#### `get_safe_connection_info(uri: str, database: str) -> dict`

Get safe connection information for logging (no credentials).

```python
from common_config.utils.security import get_safe_connection_info

info = get_safe_connection_info(
    uri="mongodb+srv://user:pass@cluster.mongodb.net/",
    database="mydb"
)

# Returns: {
#     'database': 'mydb',
#     'uri': 'mongodb+srv://***:***@cluster.mongodb.net/',
#     'host': 'cluster.mongodb.net',
#     'port': None,
#     'scheme': 'mongodb+srv'
# }

logger.info(f"Connection info: {info}")  # Safe to log
```

---

## 5. Security Checklist

### Before Committing Code

- [ ] No hardcoded credentials in code
- [ ] All secrets in `.env` (gitignored)
- [ ] `redact_uri()` used for all URI logging
- [ ] No credentials in print statements
- [ ] No credentials in comments
- [ ] Data files excluded via `.gitignore`
- [ ] Run `git add -n` to verify what will be committed
- [ ] Search for potential leaks: `grep -r "password" --include="*.py"`

### Before Writing Documentation

- [ ] Use placeholder syntax: `<username>:<password>`
- [ ] No realistic-looking credentials in examples
- [ ] Check for URI patterns: `grep -r "mongodb.*://.*:.*@" docs/`
- [ ] Use `***` when showing redacted output
- [ ] Reference this document for approved patterns
- [ ] Test documentation examples don't trigger GitHub scanning

### Before Logging Information

- [ ] Import `redact_uri` if logging URIs
- [ ] Use `redact_uri()` for all connection strings
- [ ] Use `redact_password()` for text with passwords
- [ ] Never log API keys, tokens, or secrets
- [ ] Review log output to verify no credentials visible
- [ ] Check CI/CD logs for accidental exposure

---

## Incident Log

### 2025-10-28: GitHub Secret Scanning - Documentation Examples

**Severity:** Low (false positive, no real credentials exposed)
**Impact:** 3 GitHub security alerts opened

**What Happened:**
- Pushed documentation with example MongoDB URIs
- Examples used patterns like `mongodb+srv://user:password@host/`
- GitHub's automated secret scanning flagged as potential credential leaks
- Alerts opened: Issues #1, #2, #3

**Root Cause:**
- Documentation examples used realistic credential patterns
- Automated scanning cannot distinguish real from fake credentials
- Pattern matching triggered on `user:password` format

**Resolution:**
- Replaced all example credentials with placeholder syntax
- Changed `user:password` → `<username>:<password>`
- Updated 4 documentation files
- Committed fix: `d37ab2c`
- GitHub re-scanned and alerts auto-closed

**Prevention:**
- Always use `<placeholder>` syntax in documentation
- Added this document to establish standards
- Added to pre-commit checklist
- Search pattern: `grep -r "mongodb.*://.*:.*@" docs/`

**Files Affected:**
- `docs/AI_COLLABORATION_GUIDE.md`
- `docs/guides/COMMON_CONFIG_API_REFERENCE.md`
- `docs/guides/NEW_PROJECT_GUIDE.md`
- `docs/best-practices/CLI_PATTERNS.md`

**Lessons Learned:**
1. Even fake credentials trigger security scanning
2. Always use placeholder syntax in documentation
3. Test documentation examples don't match credential patterns
4. Quick response important to avoid confusion about real vs fake leaks

---

## Related Documentation

- [CLI_PATTERNS.md](CLI_PATTERNS.md) - Security Requirements section
- [COMMON_CONFIG_API_REFERENCE.md](../guides/COMMON_CONFIG_API_REFERENCE.md) - Security Utilities section
- [AI_COLLABORATION_GUIDE.md](../AI_COLLABORATION_GUIDE.md) - Security is Non-Negotiable section
- [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - Documentation security patterns

---

**Questions or new security patterns?** Update this document and notify the team.

**Security Vulnerability Found?**
1. DO NOT commit to public repo
2. Create private GitHub security advisory
3. Rotate compromised credentials immediately
4. Review git history for exposure
