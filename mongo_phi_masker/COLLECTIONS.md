# Collection Configuration Inventory

This document tracks the PHI masking configuration for all MongoDB collections.

## Quick Validation

**Note:** Validation is now **automatic** when using `orchestrate_masking.sh` (Step 0).

You can disable automatic validation with `--skip-validation` flag:

```bash
# Skip validation (not recommended unless config is known-good)
./scripts/orchestrate_masking.sh --collection Patients --skip-validation ...
```

For manual validation or testing:

```bash
# Validate specific collection
python scripts/validate_collection.py --collection Patients

# Validate all collections
python scripts/validate_collection.py --all
```

______________________________________________________________________

## Production-Ready Collections (9)

All collections below have complete configuration and can be used with the orchestration script.

| Collection                 | Config File                          | Rules File                          | Rules Count     | Status               |
| -------------------------- | ------------------------------------ | ----------------------------------- | --------------- | -------------------- |
| **Container**              | `config_Container.json`              | `rules_Container.json`              | TBD             | ✅ Ready             |
| **Messages**               | `config_Messages.json`               | `rules_Messages.json`               | 3 (placeholder) | ⚠️ Rules need review |
| **OfflineAppointments**    | `config_OfflineAppointments.json`    | `rules_OfflineAppointments.json`    | TBD             | ✅ Ready             |
| **PatientCarePlanHistory** | `config_PatientCarePlanHistory.json` | `rules_PatientCarePlanHistory.json` | TBD             | ✅ Ready             |
| **PatientReportFaxQueue**  | `config_PatientReportFaxQueue.json`  | `rules_PatientReportFaxQueue.json`  | 3 (placeholder) | ⚠️ Rules need review |
| **Patients**               | `config_Patients.json`               | `rules_Patients.json`               | 34              | ✅ Production-tested |
| **StaffAvailability**      | `config_StaffAvailability.json`      | `rules_StaffAvailability.json`      | TBD             | ✅ Ready             |
| **Tasks**                  | `config_Tasks.json`                  | `rules_Tasks.json`                  | 3               | ✅ Ready             |
| **container_emergency**    | `config_container_emergency.json`    | `rules_Container.json` (shared)     | TBD             | ✅ Ready             |

______________________________________________________________________

## Naming Convention

**Standardized naming** (as of 2025-11-06):

- **Config files**: `config/<CollectionName>.json` (PascalCase)
- **Rules files**: `rules_<CollectionName>.json` (PascalCase)
- **Collection names**: Match MongoDB collection names exactly

### Example

For a collection named `Patients`:

- Config: `config/config_rules/config_Patients.json`
- Rules: `config/masking_rules/rules_Patients.json`
- PATH_MAPPING: `"Patients": { ... }` (if needed for test data)

______________________________________________________________________

## Configuration Files

### Required Fields in Config File

```json
{
    "mongodb": {
        "source": { "uri": "${MONGO_SOURCE_URI}", ... },
        "destination": { "uri": "${MONGO_DEST_URI}", ... }
    },
    "processing": {
        "masking_mode": "in-situ",
        "batch_size": { ... }
    },
    "masking": {
        "rules_path": "config/masking_rules/rules_<CollectionName>.json",
        "default_rules": "config/masking_rules/default.json"
    },
    "phi_collections": ["<CollectionName>"],
    "validation": { ... },
    "metrics": { ... },
    "connection": { ... }
}
```

### Required Fields in Rules File

```json
{
    "rules": [
        {"field": "FieldName", "rule": "masking_rule", "params": null},
        ...
    ]
}
```

______________________________________________________________________

## Adding a New Collection

### Step 1: Create Config File

```bash
cp config/config_rules/config_Patients.json config/config_rules/config_NewCollection.json
```

Edit the file:

- Update `phi_collections` array
- Update `rules_path` to point to `rules_NewCollection.json`

### Step 2: Create Rules File

```bash
# Create from template
cat > config/masking_rules/rules_NewCollection.json << 'EOF'
{
    "rules": [
        {"field": "PatientName", "rule": "random_uppercase_name", "params": null},
        {"field": "Email", "rule": "replace_email", "params": "xxxxx@xxxx.com"}
    ]
}
EOF
```

### Step 3: Add PATH_MAPPING (Optional)

Only needed if you want to generate test data (Step 0).

Edit `config/collection_rule_mapping.py`:

```python
PATH_MAPPING = {
    # ... existing collections ...
    "NewCollection": {
        "PatientName": "Patient.Name",
        "Email": "Contact.Email",
        # ... field mappings ...
    }
}
```

### Step 4: Validate

```bash
python scripts/validate_collection.py --collection NewCollection
```

### Step 5: Test

```bash
# Generate test data (optional)
python scripts/generate_test_data.py \
  --env LOCL \
  --db local-phi-unmasked \
  --collection NewCollection \
  --size 100

# Run orchestration
bash scripts/orchestrate_masking.sh \
  --src-env LOCL \
  --src-db local-phi-unmasked \
  --proc-env DEV \
  --proc-db dev-phidb \
  --dst-env LOCL \
  --dst-db local-phi-masked \
  --collection NewCollection
```

______________________________________________________________________

## Available Masking Rules

Common rules used in `rules_*.json` files:

| Rule                     | Description                      | Example Params          |
| ------------------------ | -------------------------------- | ----------------------- |
| `random_uppercase_name`  | Generate random uppercase name   | `null`                  |
| `random_uppercase`       | Random uppercase string          | `null`                  |
| `replace_string`         | Replace with fixed string        | `"xxxxxxxxxx"`          |
| `replace_email`          | Replace with fixed email         | `"xxxxx@xxxx.com"`      |
| `replace_gender`         | Replace with fixed gender        | `"Female"`              |
| `random_10_digit_number` | Random 10-digit number           | `null`                  |
| `add_milliseconds`       | Shift dates by milliseconds      | `63072000000` (2 years) |
| `lowercase_match`        | Match lowercase version of field | `"FirstName"`           |

______________________________________________________________________

## Cleanup History

### 2025-11-06: Collection Configuration Standardization

**Issues Fixed:**

1. ✅ Fixed typo: `config_StaffAavailability.json` → `config_StaffAvailability.json`
1. ✅ Standardized rules file naming to PascalCase
1. ✅ Fixed wrong references: 3 configs pointing to non-existent `tasks_rules.json`
1. ✅ Created missing rules files: `rules_Messages.json`, `rules_PatientReportFaxQueue.json`
1. ✅ Updated all config files to reference correct rules files

**Results:**

- Before: 2 complete collections, 6 with missing files
- After: **9 complete collections, all validated** ✅

______________________________________________________________________

## Notes

### Placeholder Rules

**Messages** and **PatientReportFaxQueue** have placeholder rules that should be customized:

- Review actual collection schema
- Identify all PHI fields
- Add appropriate masking rules for each field

### Shared Rules Files

`container_emergency` shares `rules_Container.json` with `Container` collection. This is intentional for emergency scenarios.

### PATH_MAPPING Cleanup

18 orphaned entries exist in `PATH_MAPPING` (collections defined but no config/rules):

- `CancelAppointmentHistory`, `CompletedExceptionAppointments`, `DeletedPatientChart`, etc.
- These can be removed or configs can be created as needed

______________________________________________________________________

## Troubleshooting

### Error: "Config file not found"

```bash
# Check if config file exists
ls config/config_rules/config_YourCollection.json

# If missing, create from template (see "Adding a New Collection" above)
```

### Error: "Rules file not found"

```bash
# Check what rules file the config expects
cat config/config_rules/config_YourCollection.json | grep rules_path

# Verify the file exists
ls config/masking_rules/rules_YourCollection.json

# If missing, create it (see "Adding a New Collection" above)
```

### Validate Before Running

Always validate before orchestration:

```bash
python scripts/validate_collection.py --collection YourCollection
```

______________________________________________________________________

## See Also

- [README.md](README.md) - Main documentation
- [LOGGING_STANDARD.md](LOGGING_STANDARD.md) - Logging format standards
- `scripts/validate_collection.py` - Collection validation script
- `scripts/orchestrate_masking.sh` - Automated orchestration workflow
