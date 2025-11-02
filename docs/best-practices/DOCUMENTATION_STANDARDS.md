# Documentation Standards

**Purpose:** Standards and best practices for writing technical documentation in this repository.

**Version:** 1.0 **Last Updated:** 2025-10-28

______________________________________________________________________

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Overview](#overview)
- [File Organization](#file-organization)
  - [Directory Structure](#directory-structure)
  - [File Naming Conventions](#file-naming-conventions)
  - [When to Create New Documents](#when-to-create-new-documents)
- [Document Structure](#document-structure)
  - [Required Sections](#required-sections)
  - [Optional Sections](#optional-sections)
  - [Table of Contents](#table-of-contents)
- [Writing Style](#writing-style)
  - [Tone and Voice](#tone-and-voice)
  - [Formatting Guidelines](#formatting-guidelines)
  - [Code Examples](#code-examples)
- [Security in Documentation](#security-in-documentation)
  - [Credential Examples](#credential-examples)
  - [Sensitive Information](#sensitive-information)
  - [Pre-Commit Checklist](#pre-commit-checklist)
- [Code Blocks](#code-blocks)
  - [Language Tags](#language-tags)
  - [Syntax Highlighting](#syntax-highlighting)
  - [Example Patterns](#example-patterns)
- [Links and References](#links-and-references)
  - [Internal Links](#internal-links)
  - [External Links](#external-links)
  - [Cross-References](#cross-references)
- [Version Control](#version-control)
  - [Last Updated Dates](#last-updated-dates)
  - [Version Numbers](#version-numbers)
  - [Change History](#change-history)
- [Common Patterns](#common-patterns)
  - [Do's and Don'ts Sections](#dos-and-donts-sections)
  - [Warning and Info Boxes](#warning-and-info-boxes)
  - [Examples and Counter-Examples](#examples-and-counter-examples)
- [Accessibility](#accessibility)
  - [Descriptive Headers](#descriptive-headers)
  - [Alt Text for Images](#alt-text-for-images)
  - [Clear Language](#clear-language)
- [Quality Checklist](#quality-checklist)
- [Related Documentation](#related-documentation)

</details>

______________________________________________________________________

## Overview

Good documentation is critical for maintainability, onboarding, and collaboration. This document establishes standards
to ensure consistency and quality across all documentation in this repository.

**Core Principles:**

1. **Clear and Concise** - Get to the point quickly
1. **Example-Driven** - Show, don't just tell
1. **Secure by Default** - No credentials, use placeholders
1. **Maintainable** - Easy to update and extend

______________________________________________________________________

## File Organization

### Directory Structure

```
docs/
├── guides/              # Step-by-step how-to guides
├── best-practices/      # Reference material and patterns
├── archive/             # Historical documentation snapshots
├── templates/           # Document templates
└── README.md           # Documentation index
```

**Guidelines:**

- **Guides** (`guides/`) - Tutorials, setup instructions, how-to guides
- **Best Practices** (`best-practices/`) - Design patterns, standards, reference material
- **Archive** (`archive/`) - Completed project summaries, deprecated guides

### File Naming Conventions

**Format:** `UPPERCASE_WITH_UNDERSCORES.md`

**Examples:**

- ✅ `NEW_PROJECT_GUIDE.md`
- ✅ `CLI_PATTERNS.md`
- ✅ `COMMON_CONFIG_API_REFERENCE.md`
- ❌ `new-project-guide.md`
- ❌ `CLIPatterns.md`

**Why uppercase?**

- Easy to spot documentation files in file listings
- Consistent with industry conventions (README, CHANGELOG, etc.)
- Clear distinction from code files

### When to Create New Documents

**Create a new guide when:**

- Setting up a new tool or process (>5 steps)
- Documenting a complete workflow
- Providing comprehensive tutorials

**Create a new best practices document when:**

- Establishing standards for a specific pattern
- Documenting lessons learned from incidents
- Providing reference material for common tasks

**Update existing documents when:**

- Adding examples to existing patterns
- Clarifying existing instructions
- Fixing errors or outdated information

______________________________________________________________________

## Document Structure

### Required Sections

Every documentation file MUST include:

1. **Title** (H1)
1. **Purpose statement** (2-3 sentences)
1. **Table of Contents** (if >100 lines) - Use collapsible format
1. **Content sections** with clear headings
1. **Related Documentation** links at end
1. **Last Updated date**

**Template:**

```markdown
# Document Title

**Purpose:** Brief description of what this document covers (2-3 sentences).

**Version:** 1.0
**Last Updated:** YYYY-MM-DD

---

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Section 1](#section-1)
- [Section 2](#section-2)

</details>

---

## Section 1

Content here...

---

## Related Documentation

- [Link to related doc](path/to/doc.md)
```

### Optional Sections

Include these when relevant:

- **Prerequisites** - Requirements before starting
- **Quick Start** - Fastest path to get started
- **Troubleshooting** - Common issues and solutions
- **Examples** - Real-world use cases
- **FAQ** - Frequently asked questions
- **Change History** - Major updates log

### Table of Contents

**When required:**

- Documents >100 lines
- Documents with >5 major sections
- Complex guides with multiple phases

**Format:** Use collapsible HTML `<details>` tag

```markdown
<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Section 1](#section-1)
  - [Subsection 1.1](#subsection-11)
  - [Subsection 1.2](#subsection-12)
- [Section 2](#section-2)

</details>
```

**Why collapsible?**

- Saves screen space
- User can hide if not needed
- `open` attribute shows by default

______________________________________________________________________

## Writing Style

### Tone and Voice

**DO:**

- ✅ Use clear, direct language
- ✅ Write in second person ("you") for guides
- ✅ Use active voice: "Run this command" not "This command should be run"
- ✅ Be concise - respect the reader's time
- ✅ Use examples liberally

**DON'T:**

- ❌ Be overly formal or academic
- ❌ Use passive voice excessively
- ❌ Include unnecessary filler words
- ❌ Assume expert knowledge without explanation

### Formatting Guidelines

**Emphasis:**

- **Bold** for emphasis, important terms
- *Italics* for slight emphasis, technical terms
- `Code` for commands, variables, file names

**Lists:**

- Use bullet points for unordered items
- Use numbered lists for sequential steps
- Indent sub-items for hierarchy

**Sections:**

- H1 (`#`) - Document title only
- H2 (`##`) - Major sections
- H3 (`###`) - Subsections
- H4 (`####`) - Rarely needed

### Code Examples

**Always include:**

1. **Context** - What the code does
1. **The code** - Properly formatted
1. **Expected output** - What to expect

**Example pattern:**

````markdown
Run this command to check Python version:

```bash
python --version
````

**Expected output:**

```
Python 3.11.9
```

````

---

## Security in Documentation

### Credential Examples

**🚨 CRITICAL:** Never use realistic credential patterns in examples.

**❌ NEVER use:**
```markdown
mongodb+srv://user:password@cluster.mongodb.net/
API_KEY=sk-proj-abc123xyz789
AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF
````

**✅ ALWAYS use placeholders:**

```markdown
mongodb+srv://<username>:<password>@cluster.mongodb.net/
API_KEY=<your_api_key>
AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
```

**Why this matters:**

- Prevents GitHub Secret Scanning alerts
- Avoids confusion about real vs fake credentials
- Industry standard for documentation
- Prevents accidental credential exposure if patterns are copied

**Approved placeholder patterns:**

| Type              | Pattern                            |
| ----------------- | ---------------------------------- |
| Username/Password | `<username>:<password>`            |
| API Keys          | `<your_api_key>` or `YOUR_API_KEY` |
| AWS Keys          | `<AWS_ACCESS_KEY_ID>`              |
| Tokens            | `<token>` or `YOUR_TOKEN`          |
| Redacted Output   | `***:***`                          |

### Sensitive Information

**Never include in documentation:**

- Real credentials (even for dev/test environments)
- Real API keys or tokens
- Real database URIs with credentials
- Personal information (emails, names, unless public)
- Internal system details (hostnames, IPs for production)

**Safe to include:**

- Localhost URIs: `mongodb://localhost:27017`
- Example domains: `example.com`, `test.local`
- Placeholder values with clear markers: `<value>`

### Pre-Commit Checklist

Before committing documentation:

```bash
# Check for credential-like patterns
grep -r "mongodb.*://.*:.*@" docs/ | grep -v "<username>:<password>"

# Check for common secrets
grep -ri "password\|secret\|key\|token" docs/ | grep -v "<" | grep -v "\*\*\*"

# Verify no real-looking URIs
grep -rE "mongodb.*://.+:.+@" docs/
```

**If matches found:**

- Review each match
- Replace with placeholder syntax
- Re-run checks to verify

______________________________________________________________________

## Code Blocks

### Language Tags

**Always specify language for syntax highlighting:**

````markdown
```python
def hello():
    print("Hello, World!")
````

````

**Supported languages:**
- `python` - Python code
- `bash` - Shell commands
- `json` - JSON data
- `yaml` - YAML configuration
- `sql` - SQL queries
- `markdown` - Markdown examples
- `text` - Plain text (no highlighting)

### Syntax Highlighting

**DO:**
```markdown
```python
from common_config.config.settings import get_settings

settings = get_settings()
````

````

**DON'T:**
```markdown
````

from common_config.config.settings import get_settings settings = get_settings()

```
```

(Missing language tag results in no syntax highlighting)

### Example Patterns

**Pattern 1: Command with output**

````markdown
**Run this command:**
```bash
python --version
````

**Expected output:**

```
Python 3.11.9
```

````

**Pattern 2: Before/After comparison**
```markdown
**Before:**
```python
# Old way
uri = settings.mongodb_uri
logger.info(f"URI: {uri}")  # ❌ Exposes credentials
````

**After:**

```python
# New way
from common_config.utils.security import redact_uri

uri = settings.mongodb_uri
logger.info(f"URI: {redact_uri(uri)}")  # ✅ Safe
```

````

**Pattern 3: Do's and Don'ts**
```markdown
**❌ Don't do this:**
```python
password = "hardcoded123"  # Bad!
````

**✅ Do this instead:**

```python
password = os.environ.get("PASSWORD")  # Good!
```

````

---

## Links and References

### Internal Links

**Use relative paths:**
```markdown
See [CLI Patterns](../best-practices/CLI_PATTERNS.md) for details.
````

**Anchor links for same document:**

```markdown
See [Security Section](#security-in-documentation) above.
```

**Why relative paths?**

- Work in both GitHub and local editors
- Don't break if repository name changes
- More maintainable

### External Links

**Always include link text:**

```markdown
✅ Good: See [Python Documentation](https://docs.python.org/) for details.
❌ Bad: See https://docs.python.org/ for details.
```

**For external tools/services:**

- Link to official documentation
- Include version if relevant
- Use stable URLs, not version-specific when possible

### Cross-References

**At end of every document:**

```markdown
## Related Documentation

- [Document 1](path/to/doc1.md) - Brief description
- [Document 2](path/to/doc2.md) - Brief description
```

______________________________________________________________________

## Version Control

### Last Updated Dates

**Format:** `YYYY-MM-DD`

**Location:** Near top of document, after purpose

```markdown
**Last Updated:** 2025-10-28
```

**When to update:**

- Major content changes
- Structural changes
- Important corrections
- NOT for typo fixes or minor clarifications

### Version Numbers

**Use semantic versioning:**

- `1.0` - Initial release
- `1.1` - Minor additions/clarifications
- `2.0` - Major restructure or breaking changes

```markdown
**Version:** 1.0
**Last Updated:** 2025-10-28
```

### Change History

**For major documents, include change log:**

```markdown
## Change History

### Version 1.1 (2025-10-28)
- Added security patterns section
- Updated code examples
- Fixed broken links

### Version 1.0 (2025-01-15)
- Initial release
```

______________________________________________________________________

## Common Patterns

### Do's and Don'ts Sections

**Use clear markers:**

```markdown
**✅ DO:**
- Use clear examples
- Include error handling
- Test all code snippets

**❌ DON'T:**
- Hardcode credentials
- Skip error handling
- Assume prior knowledge
```

### Warning and Info Boxes

**Use emoji for visual emphasis:**

```markdown
🚨 **CRITICAL:** This is a critical security warning.

⚠️ **WARNING:** This might cause issues if not done correctly.

💡 **TIP:** Here's a helpful tip to save time.

📝 **NOTE:** Additional information to consider.

✅ **SUCCESS:** Indicates successful completion.
```

### Examples and Counter-Examples

**Always show both:**

````markdown
**Example - Correct Usage:**
```python
# Good code here
````

**Example - Incorrect Usage:**

```python
# Bad code here
```

**Why this is wrong:** Explanation of the problem.

````

---

## Accessibility

### Descriptive Headers

**DO:**
```markdown
## Setting Up Virtual Environment
## Troubleshooting Import Errors
````

**DON'T:**

```markdown
## Setup
## Errors
```

### Alt Text for Images

**If using images (avoid when possible):**

```markdown
![Architecture diagram showing MongoDB connection flow](images/architecture.png)
```

### Clear Language

- Avoid jargon without explanation
- Define acronyms on first use
- Use simple sentence structure
- Break complex topics into steps

______________________________________________________________________

## Quality Checklist

Before finalizing documentation:

**Structure:**

- [ ] Title is clear and descriptive
- [ ] Purpose statement present
- [ ] Table of contents included (if >100 lines)
- [ ] All sections have clear headings
- [ ] Related documentation links at end
- [ ] Last updated date included

**Content:**

- [ ] All code examples tested and working
- [ ] No real credentials or secrets
- [ ] Placeholders use `<angle_brackets>` syntax
- [ ] All commands include expected output
- [ ] Links work (both internal and external)
- [ ] No typos or grammatical errors

**Security:**

- [ ] No credential patterns that trigger GitHub scanning
- [ ] All examples use placeholder syntax
- [ ] Ran security grep checks (see checklist above)
- [ ] No internal/sensitive system information

**Style:**

- [ ] Consistent formatting throughout
- [ ] Code blocks have language tags
- [ ] Lists are properly formatted
- [ ] Tone is clear and professional

**Verification:**

- [ ] Rendered correctly in Markdown viewer
- [ ] All anchor links work
- [ ] File follows naming conventions
- [ ] Located in correct directory

______________________________________________________________________

## Related Documentation

- [SECURITY_PATTERNS.md](SECURITY_PATTERNS.md) - Security best practices for documentation
- [CLI_PATTERNS.md](CLI_PATTERNS.md) - Standard CLI documentation patterns
- [FILE_NAMING_CONVENTIONS.md](FILE_NAMING_CONVENTIONS.md) - File naming standards
- [AI_COLLABORATION_GUIDE.md](../AI_COLLABORATION_GUIDE.md) - Documentation principles for AI collaboration

______________________________________________________________________

**Questions about documentation standards?** Update this document and share with the team.

**Found an issue in existing documentation?** Fix it and update the Last Updated date.
