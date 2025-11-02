# MongoDB PHI/PII Data Masking Tools

**= SECURITY CRITICAL:** Mask Protected Health Information (PHI) and Personally Identifiable Information (PII) in
MongoDB collections for compliance and testing purposes.

  **WARNING:** This tool PERMANENTLY modifies data. Always backup before use!

## Features

-  **Two-Step Process** - Safe workflow: add flag, then mask
-  **Field-Specific Masking** - Different rules for names, dates, phones, emails, etc.
-  **Recursive Masking** - Handles nested objects and arrays
-  **Batch Processing** - Efficient processing with configurable batch size
-  **Dry Run Mode** - Test before executing (enabled by default)
-  **Status Reporting** - Track masking progress across collections
-  **Environment Support** - DEV/PROD configuration via `common_config`
-  **Safety Checks** - Confirmation prompts for production environments

## Installation

This project uses the repository-wide shared virtual environment. See the root README.md for setup instructions.

### Required Dependencies

```bash
pip install pymongo typer rich
```

(Already included in root `requirements.txt`)

## Configuration

Configure MongoDB connection in `shared_config/.env`:

```bash
# Default environment
APP_ENV=DEV

# DEV Environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=UbiquityDevelopment

# PROD Environment
MONGODB_URI_PROD=mongodb+srv://<username>:<password>@cluster.mongodb.net
DATABASE_NAME_PROD=UbiquityProduction
```

## Masking Rules

### Field-Specific Masking

| Field Type                 | Original            | Masked                                    | Preservation       |
| -------------------------- | ------------------- | ----------------------------------------- | ------------------ |
| **Names**                  | "John Doe"          | "ABCD EFG" (random uppercase)             | Length, spaces     |
| **Notes/Text**             | "Patient has..."    | "xxxxxxxxxx"                              | None               |
| **DOB**                    | 1990-01-15          | Timestamp + 207360000000ms                | None               |
| **Phone**                  | "555-1234"          | Random 10-digit number                    | None               |
| **Email**                  | "john@example.com"  | "xxxxxx@xxxx.com"                         | None               |
| **Gender**                 | "Male"              | "xxxxxx"                                  | None               |
| **Addresses/IDs**          | "123 Main St"       | "xxxxxxxxxx"                              | None               |
| **File Paths**             | "/path/to/file.pdf" | "//vm_fs01/Projects/EMRQAReports/..."     | None               |

### Name Fields

Masked: PatientName, PatientFirstName, PatientMiddleName, PatientLastName, FirstName, MiddleName, LastName, UserName

### Text/Note Fields

Masked: HPINote, Notes, FinalNotes, Comments, OtherReason, VisitNotes, HomeText, VisitStatusNote, ReasonDetails,
Reason, EmployerStreet, HealthPlanMemberId, SubscriberId, Street1, Street2, City, StateCode, Zip5, StateName,
PrimaryMemberName, SnapShot, Goals, VisitAddress

### Phone Fields

Masked: PhoneNumber, HomePhoneNumber, WorkPhoneNumber

### Email Fields

Masked: Email

### Gender Fields

Masked: Gender

### Path Fields

Masked: Path

### DOB Fields

Masked: Dob, PrimaryMemberDOB

## Usage

### Step 1: Add isMasked Flag

Add `isMasked: false` to all documents that don't have the flag:

```bash
# Dry run (no changes)
python mongodb_masking_tools/run.py add-flag --collection Patients --env DEV

# Execute on specific collection
python mongodb_masking_tools/run.py add-flag --collection Patients --env DEV --execute

# Execute on ALL collections
python mongodb_masking_tools/run.py add-flag --env DEV --execute
```

### Step 2: Mask PHI/PII Data

Mask all documents where `isMasked: false`:

```bash
# Dry run (no changes)
python mongodb_masking_tools/run.py mask --collection Patients --env DEV

# Execute on specific collection
python mongodb_masking_tools/run.py mask --collection Patients --env DEV --execute

# Execute on ALL collections
python mongodb_masking_tools/run.py mask --env DEV --execute

# Custom batch size
python mongodb_masking_tools/run.py mask --collection Patients --env DEV --batch-size 500 --execute
```

### Step 3: Check Status

View masking status for collections:

```bash
# All collections
python mongodb_masking_tools/run.py status --env DEV

# Specific collection
python mongodb_masking_tools/run.py status --collection Patients --env DEV
```

### Command Options

#### add-flag Command

| Option         | Short | Description                            | Default |
| -------------- | ----- | -------------------------------------- | ------- |
| `--collection` | `-c`  | Specific collection (None = all)       | None    |
| `--env`        | `-e`  | Environment (DEV, PROD, etc.)          | DEV     |
| `--dry-run`    | -     | Dry run mode (no changes)              | True    |
| `--execute`    | -     | Execute mode (make changes)            | False   |

#### mask Command

| Option         | Short | Description                            | Default |
| -------------- | ----- | -------------------------------------- | ------- |
| `--collection` | `-c`  | Specific collection (None = all)       | None    |
| `--env`        | `-e`  | Environment (DEV, PROD, etc.)          | DEV     |
| `--batch-size` | `-b`  | Documents per batch                    | 200     |
| `--dry-run`    | -     | Dry run mode (no changes)              | True    |
| `--execute`    | -     | Execute mode (make changes)            | False   |
| `--seed`       | -     | Random seed (testing only)             | None    |

#### status Command

| Option         | Short | Description                            | Default |
| -------------- | ----- | -------------------------------------- | ------- |
| `--collection` | `-c`  | Specific collection (None = all)       | None    |
| `--env`        | `-e`  | Environment (DEV, PROD, etc.)          | DEV     |

## Workflow Example

Complete workflow for masking a single collection:

```bash
# 1. Check current status
python mongodb_masking_tools/run.py status --collection Patients --env DEV

# 2. Add isMasked flag (dry run first)
python mongodb_masking_tools/run.py add-flag --collection Patients --env DEV
python mongodb_masking_tools/run.py add-flag --collection Patients --env DEV --execute

# 3. Mask data (dry run first)
python mongodb_masking_tools/run.py mask --collection Patients --env DEV
python mongodb_masking_tools/run.py mask --collection Patients --env DEV --execute

# 4. Verify completion
python mongodb_masking_tools/run.py status --collection Patients --env DEV
```

## Safety Features

### 1. Dry Run by Default

All operations default to dry run mode - you must explicitly use `--execute` to make changes:

```bash
# Safe - no changes
python run.py mask --collection Patients --env DEV

# Dangerous - makes changes
python run.py mask --collection Patients --env DEV --execute
```

### 2. Production Warnings

When running against PROD environment, the tool displays warnings and requires confirmation:

```
  WARNING: You are about to PERMANENTLY MASK PRODUCTION data!
This operation is IRREVERSIBLE and will destroy original data!

Are you absolutely sure you want to continue? [y/N]:
```

### 3. Two-Step Process

The workflow requires two separate commands, preventing accidental execution:

1. `add-flag` - Adds tracking field
2. `mask` - Performs masking

### 4. Status Reporting

Check masking status before and after operations:

```bash
python run.py status --env DEV
```

## Migration from JavaScript

This project is a Python migration of the JavaScript `MASKING_SCRIPTS_PHI_PII` tool with equivalent functionality:

| JavaScript                         | Python               | Status |
| ---------------------------------- | -------------------- | ------ |
| `add_isMasked_*.js`                | `add-flag` command   |      |
| `mask_single_collection.js`        | `mask -c` command    |      |
| `mask_multiple_collections.js`     | `mask` command       |      |
| `maskFields()` function            | `MaskingEngine`      |      |
| Batch processing (200 docs)        | Configurable batches |      |
| Recursive masking                  | Recursive masking    |      |
| Status tracking                    | `status` command     |      |

### Behavior Validation

The Python version maintains exact masking behavior:

-  Name masking preserves length and spaces
-  DOB offset matches JavaScript: 207360000000 milliseconds
-  Phone numbers are 10-digit integers
-  Fixed strings match exactly ("xxxxxxxxxx", "xxxxxx@xxxx.com", etc.)
-  Recursive processing for nested objects
-  Batch size default: 200 documents
-  Only processes documents where `isMasked: false`

## Performance

- **Batch Size:** Default 200 documents (configurable)
- **Connection Pooling:** Uses MongoDB connection pooling
- **Typical Rate:** ~100-500 documents/second (depends on document complexity)
- **Memory Usage:** Processes documents in batches to minimize memory footprint

## Examples

### Mask All Collections in DEV

```bash
# Step 1: Add flags
python mongodb_masking_tools/run.py add-flag --env DEV --execute

# Step 2: Mask data
python mongodb_masking_tools/run.py mask --env DEV --execute
```

### Mask Single Collection

```bash
python mongodb_masking_tools/run.py add-flag -c Appointments --env DEV --execute
python mongodb_masking_tools/run.py mask -c Appointments --env DEV --execute
```

### Large Collection (Optimize Performance)

```bash
# Use larger batch size for better performance
python mongodb_masking_tools/run.py mask -c Patients --env DEV -b 500 --execute
```

### Check Status After Masking

```bash
# See which collections are fully masked
python mongodb_masking_tools/run.py status --env DEV
```

## Troubleshooting

### "No unmasked documents" Message

```
Collection: No unmasked documents, skipping
```

**Meaning:** All documents already have `isMasked: true` or collection is empty.

### "Would add flag to N documents"

This is normal in dry run mode. Add `--execute` to actually add flags.

### Connection Timeout

```
Error: Unable to connect to MongoDB after 5 attempts
```

**Solution:**

- Verify MongoDB URI in `shared_config/.env`
- Check network connectivity
- Ensure MongoDB server is running

### Bulk Write Error

```
Error in batch N: [BulkWriteError details]
```

**Solution:**

- Review error details in output
- Check document schema issues
- Reduce batch size if memory-related

## Best Practices

### 1. Always Backup First

```bash
# Create backup before masking
mongodump --uri="<connection_uri>" --db=<database> --out=backup_$(date +%Y%m%d)
```

### 2. Test in DEV First

Never run masking operations directly in production without testing in DEV environment first.

### 3. Use Dry Run

Always run with dry run mode first to see what will be changed:

```bash
# Check what would happen
python run.py mask --collection Patients --env DEV

# Then execute
python run.py mask --collection Patients --env DEV --execute
```

### 4. Monitor Progress

For large datasets, monitor progress:

```bash
# Check status periodically
watch -n 30 'python mongodb_masking_tools/run.py status --env DEV'
```

### 5. Document Masking Operations

Keep a log of when and what was masked for compliance auditing.

## Security Considerations

### 1. Irreversible Operation

  **WARNING:** Masking permanently destroys original data. There is NO undo operation.

### 2. Backup Policy

**Required:** Always maintain backups before masking production data.

### 3. Access Control

- Limit who can run masking operations
- Use separate credentials for masking operations
- Log all masking activities

### 4. Compliance

This tool helps with HIPAA, GDPR, and other compliance requirements by:

- Removing PHI/PII from non-production environments
- Enabling safe testing with production-like data
- Documenting masking operations

### 5. Testing

Always test masking operations on a copy of production data before applying to actual production.

## Related Projects

- **mongodb_index_tools** - MongoDB index management and analysis
- **mongodb_profiler_tools** - Query performance analysis
- **mongodb_test_data_tools** - Generate fake test data

## Contributing

When modifying this tool:

1. **Maintain masking behavior** - Any changes to masking rules must be documented
2. **Add tests** - Validate masking output matches expected results
3. **Run linting:** `./scripts/lint.sh mongodb_masking_tools/`
4. **Test thoroughly** - Test with realistic data structures
5. **Document changes** - Update README with any new functionality

## Author

- **Demesew Abebe**
- **Version:** 1.0.0
- **Date:** 2025-11-02
- **Migrated from:** JavaScript MASKING_SCRIPTS_PHI_PII

## License

Internal use only - Korrojo/Ubiquity

---

##   Final Warning

**This tool permanently modifies data. There is no undo.**

-  Always backup first
-  Test in DEV environment
-  Use dry run mode
-  Verify with status command
-  Document operations for compliance
- L Never rush masking operations
- L Never skip dry run testing
- L Never mask without backup
