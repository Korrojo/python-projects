# Documentation Directory

This directory contains all technical documentation for the Python Projects repository, organized by purpose and audience.

## Directory Structure

```
docs/
├── guides/              # Step-by-step how-to guides
├── best-practices/      # Reference material and patterns
├── archive/             # Historical documentation snapshots
├── index/               # Generated documentation indices
├── prompts/             # AI/automation prompts
├── schema/              # MongoDB schema definitions
└── templates/           # Document templates
```

---

## Quick Navigation

### Getting Started

**New to the repository?** Start here:
1. Read the main [README.md](../README.md) in the repository root
2. Follow [guides/NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md) for complete walkthrough with environment setup

**Adding a new project?**
- [guides/NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md) - Comprehensive 9-phase guide from environment setup to Git commit

**Setting up code quality tools?**
- [guides/LINTING.md](guides/LINTING.md) - Ruff and Pyright setup
- [guides/VENV_SETUP.md](guides/VENV_SETUP.md) - Virtual environment details

---

## Guides (Step-by-Step Instructions)

Located in `guides/`

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [NEW_PROJECT_GUIDE.md](guides/NEW_PROJECT_GUIDE.md) | Comprehensive 9-phase guide for creating any new project | Starting any new project (PRIMARY GUIDE) |
| [VENV_SETUP.md](guides/VENV_SETUP.md) | Virtual environment setup scripts | First-time setup or troubleshooting |
| [LINTING.md](guides/LINTING.md) | Code quality tools (Ruff, Pyright) | Setting up linting/formatting |
| [TESTING_GUIDE.md](guides/TESTING_GUIDE.md) | Running tests across projects | Writing or running tests |
| [REPOSITORY_STANDARDS.md](guides/REPOSITORY_STANDARDS.md) | Directory structure conventions | Understanding project organization |

---

## Best Practices (Reference Material)

Located in `best-practices/`

| Document | Purpose | Audience |
|----------|---------|----------|
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
