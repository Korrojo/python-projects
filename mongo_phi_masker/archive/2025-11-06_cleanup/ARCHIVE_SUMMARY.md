# Archive Summary - 2025-11-06

## Total Files Archived

$(find archive/2025-11-06_cleanup -type f -not -name "ARCHIVE_SUMMARY.md" | wc -l | tr -d ' ') files

## By Category

- **Verification Scripts:** $(find archive/2025-11-06_cleanup/old_scripts/verification -type f | wc -l | tr -d ' ') files
- **Test Data Scripts:** $(find archive/2025-11-06_cleanup/old_scripts/test_data -type f | wc -l | tr -d ' ') files  
- **Workflow Scripts:** $(find archive/2025-11-06_cleanup/old_scripts/workflows -type f | wc -l | tr -d ' ') files
- **Config Files:** $(find archive/2025-11-06_cleanup/old_configs -type f | wc -l | tr -d ' ') files
- **Migration Tools:** $(find archive/2025-11-06_cleanup/migration_tools -type f | wc -l | tr -d ' ') files
- **Documentation:** $(find archive/2025-11-06_cleanup/old_docs -type f | wc -l | tr -d ' ') files
- **Utilities:** $(find archive/2025-11-06_cleanup/utilities -type f | wc -l | tr -d ' ') files
- **Data Snapshots:** $(find archive/2025-11-06_cleanup/data_snapshots -type f | wc -l | tr -d ' ') files
- **Unused Modules:** $(find archive/2025-11-06_cleanup/unused_modules -type f | wc -l | tr -d ' ') files

## Archive Location

All files moved to: `archive/2025-11-06_cleanup/`

## Retained Files (Core Workflow)

### Scripts (5)
- masking.py
- scripts/generate_test_data.py
- scripts/backup_collection.sh
- scripts/restore_collection.sh  
- scripts/verify_masking.py

### Config (collection-specific configs retained)
- config/collection_rule_mapping.py
- config/config_rules/config_*.json (for active collections)
- config/masking_rules/rules_*.json (for active collections)

### Source Code (essential modules)
- src/core/masker.py
- src/core/connector.py
- src/models/masking_rule.py
- src/utils/env_config.py
- src/utils/config_loader.py
- src/utils/db_config.py
- src/utils/logger.py
- src/utils/compatibility.py

### Documentation
- README.md
- LOGGING_STANDARD.md
- ARCHIVE_PROPOSAL.md

### Tests (all retained)
- tests/

## Git History Preserved

All tracked files were moved using `git mv` to preserve commit history.
