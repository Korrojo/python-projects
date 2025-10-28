# Documentation Directory

> **📌 Note:** This is the **detailed documentation index**. For quick task-based navigation, see the [Master README](../README.md) at repository root.

This directory contains all technical documentation for the Python Projects repository, organized by purpose and audience.

## How to Use This Documentation

**Two ways to find what you need:**

1. **Task-Based (Faster)** → Use [Master README](../README.md)
   - "I want to create a new project" → Direct link to guide
   - "I'm getting import errors" → Direct link to troubleshooting
   - "I need reference material" → Direct links to relevant docs

2. **Browse by Type (Comprehensive)** → Use this page
   - See all available documentation
   - Understand organization structure
   - Explore by category (guides, best practices, archives)

---

## Directory Structure

```
docs/
├── AI_COLLABORATION_GUIDE.md  # 🤖 Guide for AI assistants (session context)
├── guides/              # Step-by-step how-to guides
├── best-practices/      # Reference material and patterns
├── archive/             # Historical documentation snapshots
├── index/               # Generated documentation indices
├── prompts/             # AI/automation prompts
├── schema/              # MongoDB schema definitions
└── templates/           # Document templates
```

---

## Navigation Flow

**Start here for common tasks:**

### Your Situation → What to Read

| If you want to... | Go to... |
|-------------------|----------|
| **🤖 AI assistant starting new session** | [AI_COLLABORATION_GUIDE.md](AI_COLLABORATION_GUIDE.md) ← Start here for context |
| **Get started quickly** | [Master README](../README.md) → 5-Minute Quickstart |
| **Create a new project** | [Master README](../README.md) → "I Want to Create a New Project" |
| **Fix an error** | [Master README](../README.md) → "I'm Encountering Errors" |
| **Browse all docs** | Stay here, see sections below |
| **Find something specific** | Use sections below or search in your editor |

---

## Quick Navigation

### For New Developers

**Complete path for first-time setup:**
1. [Master README](../README.md) - Quickstart (5 minutes)
2. [guides/NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md) - Full walkthrough (30-60 minutes)
3. [guides/COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md) - ⭐ **Bookmark this** for development

### For Active Development

**Keep these open while coding:**
- ⭐⭐ [guides/COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths & patterns
- [Master README](../README.md) - Quick reference for common tasks

**Before committing:**
- [best-practices/CI_CD_LESSONS_LEARNED.md](best-practices/CI_CD_LESSONS_LEARNED.md) - Avoid CI failures

### For Troubleshooting

**Import errors:**
- [guides/COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md) - Correct paths
- [best-practices/IMPORT_PATH_ISSUES.md](best-practices/IMPORT_PATH_ISSUES.md) - Why & prevention

**Environment issues:**
- [guides/VENV_SETUP.md](guides/VENV_SETUP.md) - Virtual environment
- [Master README](../README.md) → Troubleshooting section

**CI/CD failures:**
- [best-practices/CI_CD_LESSONS_LEARNED.md](best-practices/CI_CD_LESSONS_LEARNED.md) - Common issues & fixes

---

## Guides (Step-by-Step Instructions)

Located in `guides/`

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md) | Comprehensive 9-phase guide for creating any new project | Starting any new project (PRIMARY GUIDE) |
| [COMMON_CONFIG_API_REFERENCE.md](guides/COMMON_CONFIG_API_REFERENCE.md) | ⭐ Import paths and usage patterns for common_config | **Before adding ANY common_config imports** |
| [VENV_SETUP.md](guides/VENV_SETUP.md) | Virtual environment setup scripts | First-time setup or troubleshooting |
| [LINTING.md](guides/LINTING.md) | Code quality tools (Ruff, Pyright) | Setting up linting/formatting |
| [TESTING_GUIDE.md](guides/TESTING_GUIDE.md) | Running tests across projects | Writing or running tests |
| [REPOSITORY_STANDARDS.md](guides/REPOSITORY_STANDARDS.md) | Directory structure conventions | Understanding project organization |

---

## Best Practices (Reference Material)

Located in `best-practices/`

| Document | Purpose | Audience |
|----------|---------|----------|
| [CI_CD_LESSONS_LEARNED.md](best-practices/CI_CD_LESSONS_LEARNED.md) | CI/CD failures and prevention strategies | All developers |
| [CLI_PATTERNS.md](best-practices/CLI_PATTERNS.md) ⭐ | Standard CLI patterns (--env, --collection) | All developers |
| [FILE_NAMING_CONVENTIONS.md](best-practices/FILE_NAMING_CONVENTIONS.md) | Standard patterns for output files and logs | All developers |
| [IMPORT_PATH_ISSUES.md](best-practices/IMPORT_PATH_ISSUES.md) | Common import errors and how to prevent them | All developers |
| [MONGODB_VALIDATION_BEST_PRACTICES.md](best-practices/MONGODB_VALIDATION_BEST_PRACTICES.md) | Technical patterns for validation/migration tools | Developers building data tools |
| [REPOSITORY_LESSONS_LEARNED.md](best-practices/REPOSITORY_LESSONS_LEARNED.md) | Organizational patterns and common pitfalls | All developers |

These documents provide:
- Reusable code patterns
- MongoDB query optimization strategies
- Project structure best practices
- Common pitfalls and solutions

---

## Archive (Historical Documentation)

Located in `archive/`

Contains documentation snapshots from October 2025:
- [DOCUMENTATION_SUMMARY.md](archive/DOCUMENTATION_SUMMARY.md) - Meta-documentation summary
- [FINAL_SUMMARY.md](archive/FINAL_SUMMARY.md) - Project completion summary
- [README_DOCUMENTATION.md](archive/README_DOCUMENTATION.md) - Previous navigation guide

These are kept for historical reference but are not actively maintained.

---

## Other Directories

### schema/
MongoDB collection schemas and validation rules.

### templates/
Reusable document templates for new projects.

### prompts/
AI/automation prompts and scripts.

### index/
Generated documentation indices (auto-created).

---

## Contributing Documentation

When adding new documentation:

1. **How-to guides** → Place in `guides/`
   - Step-by-step instructions
   - Setup procedures
   - Tutorials

2. **Reference material** → Place in `best-practices/`
   - Design patterns
   - Best practices
   - Code examples

3. **Historical records** → Place in `archive/`
   - Completed project summaries
   - Deprecated guides
   - Historical snapshots

4. **Update this README** to include your new document in the appropriate section

---

## Documentation Standards

- Use clear, descriptive filenames (UPPERCASE_WITH_UNDERSCORES.md)
- Include a table of contents for documents >100 lines
- Add "Last Updated" dates for reference material
- Use code blocks with language tags for syntax highlighting
- Include "When to use this document" sections

---

## Related Documentation

- [Main README](../README.md) - Repository overview and setup
- [CHANGELOG](../CHANGELOG.md) - Version history
- [CONTRIBUTING](../CONTRIBUTING.md) - Contribution guidelines
- [TODO](../TODO.md) - Planned enhancements

---

**Last Updated:** 2025-10-27
