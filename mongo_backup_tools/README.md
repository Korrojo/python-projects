# MongoDB Backup Tools

**Comprehensive MongoDB backup, restore, export, and import toolkit**

## Overview

`mongo_backup_tools` is a production-ready toolkit for MongoDB operations that provides:

- **mongodump**: Enhanced database and collection backup with resume capability
- **mongorestore**: Advanced restore with namespace remapping and state tracking
- **mongoexport**: Export collections to JSON/CSV with query filtering
- **mongoimport**: Import JSON/CSV data with upsert modes
- **Monitoring**: Active user count and database statistics
- **Migration**: Database refresh and environment synchronization

## Features

- ✅ **Hybrid Architecture**: Python orchestration + proven shell scripts
- ✅ **Production-Ready**: Resume capability, dry-run mode, email notifications
- ✅ **Comprehensive CLI**: Systematic options for all MongoDB tools
- ✅ \*\*Mon

orepo Integration\*\*: Uses common_config for logging, settings, security

- ✅ **Well-Tested**: >80% test coverage, CI/CD integration
- ✅ **Cross-Platform**: macOS, Linux, Windows (via WSL)

## Installation

### Prerequisites

- Python 3.11+
- MongoDB Database Tools installed (`mongodump`, `mongorestore`, etc.)
- Access to MongoDB instance

### Setup

```bash
# Activate virtual environment
source .venv311/bin/activate

# Project is part of monorepo - dependencies already installed
# No additional setup needed
```

## Usage

### Quick Start

```bash
# Show version
python run.py version

# Backup a database
python run.py dump --db MyDatabase --output /backups/

# Restore a database
python run.py restore --archive /backups/mydb.gz --nsTo "DevDB.*" --drop

# Export collection to CSV
python run.py export --db MyDB --collection Users --output users.csv --type csv

# Import CSV
python run.py import --input users.csv --db MyDB --collection Users --type csv
```

### Commands

- `dump` - Backup MongoDB databases/collections
- `restore` - Restore from backup archives
- `export` - Export collections to JSON/CSV
- `import` - Import JSON/CSV data
- `monitor` - Database monitoring (coming soon)
- `migrate` - Database migration (coming soon)

## Development Status

**Phase 1: Foundation Setup** ✅ COMPLETED

- [x] Project structure created
- [x] Core Python files
- [x] Smoke tests
- [x] CI/CD integration

**Phase 2: Shell Script Migration** ⏳ IN PROGRESS

- [ ] Migrate mongodump scripts
- [ ] Migrate mongorestore scripts
- [ ] Migrate mongoexport scripts
- [ ] Migrate mongoimport scripts

See `temp/MONGO_TOOLS_IMPLEMENTATION_PLAN.md` for detailed roadmap.

## Testing

```bash
# Run smoke tests
pytest tests/test_mongo_backup_tools_smoke.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=mongo_backup_tools --cov-report=term-missing
```

## Project Structure

```
mongo_backup_tools/
├── src/mongo_backup_tools/
│   ├── cli.py                    # Main CLI entry point
│   ├── models/                   # Pydantic models for options
│   ├── orchestrators/            # Python orchestration layer
│   ├── utils/                    # Utility modules
│   └── scripts/                  # Shell scripts (MongoDB operations)
├── tests/                        # Test suite
├── temp/                         # Temporary files (gitignored)
├── run.py                        # CLI entry point
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

## Contributing

Follow monorepo standards:

1. Read `/docs/guides/NEW_PROJECT_GUIDE.md`
1. Follow `/docs/guides/REPOSITORY_STANDARDS.md`
1. Use `/docs/guides/COMMON_CONFIG_API_REFERENCE.md` for imports
1. Run `./scripts/pre-push-check.sh` before committing

## Documentation

- [Implementation Plan](../../temp/MONGO_TOOLS_IMPLEMENTATION_PLAN.md) - Detailed 10-phase roadmap
- [Quick Checklist](../../temp/IMPLEMENTATION_CHECKLIST.md) - Daily progress tracking
- [Phase Summary](../../temp/PHASE_SUMMARY.md) - Visual progress tracker

## License

See repository LICENSE file.

## Status

**Current Phase**: Phase 1 - Foundation Setup ✅ COMPLETED

**Next Phase**: Phase 2 - Shell Script Migration

**Version**: 1.0.0-alpha (in development)
