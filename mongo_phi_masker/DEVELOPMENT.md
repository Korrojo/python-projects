# Development Guide

## Table of Contents

- [Development Best Practices](#development-best-practices)
- [Project Architecture](#project-architecture)
- [Technical Handover](#technical-handover)

## Development Best Practices

### Code Organization & Modularity

1. **Project Structure**:

   - Separate concerns into distinct modules/packages
   - Use a standard layout (e.g., `src/`, `tests/`, `config/`, `scripts/`)
   - Keep configuration separate from code

1. **File Size and Complexity**:

   - Keep individual files small (\<300 lines if possible)
   - One class/primary function per file
   - Split functionality into logical components
   - Follow single responsibility principle

1. **Dependency Management**:

   - Use `requirements.txt` or `pyproject.toml` for dependencies
   - Pin version numbers for reproducibility
   - Use virtual environments or containers

## Project Architecture

### Current Architecture

The project follows a modular architecture with these components:

- **Main Script (masking.py)**: Core orchestration
- **Core modules**: Processor, Masker, Validator, Orchestrator
- **Models**: MaskingRule, Checkpoint
- **Utils**: MongoConnector, ConfigLoader, etc.

### Planned Refactoring

1. **Modularization**:

   - Split large files into smaller, focused modules
   - Create clear interfaces between components
   - Implement proper dependency injection

1. **Error Handling**:

   - Implement consistent error handling
   - Add comprehensive logging
   - Create meaningful error messages

## Technical Handover

### Project Overview

**MongoPHIMasker** is a Python-based solution designed to identify and mask Protected Health Information (PHI) in
MongoDB databases to ensure compliance with healthcare regulations like HIPAA.

### Key Components

1. **Core Modules**:

   - `orchestrator.py`: Main coordination of the masking process
   - `processor.py`: Handles document processing logic
   - `masker.py`: Implements masking rules
   - `validator.py`: Validates masked data

1. **Project Structure**:

   ```
   src/
   ├── core/                 # Core functionality
   ├── models/               # Data models
   ├── utils/                # Utility functions
   └── config/               # Configuration files
   tests/                   # Test files
   docs/                    # Documentation
   ```

### Development Workflow

1. Create a feature branch for changes
1. Write tests for new functionality
1. Implement changes following the style guide
1. Run tests and ensure all pass
1. Submit a pull request for review

### Known Issues and Technical Debt

- See TESTING.md for current test status and known issues
- Monitor performance with large collections
- Improve error handling for edge cases
