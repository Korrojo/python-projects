# MongoDB Test Data Generator

Generate realistic fake test data for MongoDB collections using Python Faker library. Migrated from JavaScript
`data_faker` project.

## Features

- ✅ **Realistic Data Generation** - Uses Faker library for authentic-looking test data
- ✅ **Patient Records** - Generates patient documents with acuity intensity history
- ✅ **Batch Processing** - Efficient batch insertion for large datasets
- ✅ **Connection Retry** - Automatic retry logic for database connection failures
- ✅ **Environment Configuration** - DEV/PROD environment support via `common_config`
- ✅ **Reproducible Data** - Optional random seed for consistent test data
- ✅ **Progress Tracking** - Rich console output with progress indicators

## Installation

This project uses the repository-wide shared virtual environment. See the root README.md for setup instructions.

### Required Dependencies

```bash
pip install Faker pymongo typer rich
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

# PROD Environment (use with caution!)
MONGODB_URI_PROD=mongodb+srv://<username>:<password>@cluster.mongodb.net
DATABASE_NAME_PROD=UbiquityProduction
```

⚠️ **Warning:** Be careful when generating test data in production environments!

## Usage

### Generate Test Data

```bash
# Generate 100 patient records in DEV
python mongodb_test_data_tools/run.py generate \
    --collection Patients \
    --total 100 \
    --batch-size 10 \
    --env DEV

# Generate with custom parameters
python mongodb_test_data_tools/run.py generate \
    --collection Patients \
    --total 1000 \
    --batch-size 50 \
    --env DEV \
    --inserted-by "test_script" \
    --seed 42
```

### Command Options

| Option          | Short | Description                                  | Default |
| --------------- | ----- | -------------------------------------------- | ------- |
| `--collection`  | `-c`  | Target collection name (required)            | -       |
| `--total`       | `-t`  | Total number of documents to generate        | 100     |
| `--batch-size`  | `-b`  | Number of documents per batch                | 10      |
| `--env`         | `-e`  | Environment (DEV, PROD, etc.)                | DEV     |
| `--inserted-by` | -     | Username/system for insertedBy field         | system  |
| `--seed`        | -     | Random seed for reproducible data (optional) | None    |

### Display Information

```bash
# Show generator information
python mongodb_test_data_tools/run.py info
```

## Generated Data Structure

### Patient Document

```json
{
  "_id": ObjectId("..."),
  "PatientId": 12345,
  "FirstName": "John",
  "MiddleName": "Michael",
  "LastName": "Doe",
  "PatientAcuityIntensityHistory": [
    {
      "_id": ObjectId("...") or null,
      "AcuityLevel": "High",
      "AcuityRef": 5,
      "BHAcuityRef": 3,
      "BHAcuityValue": "Moderate",
      "CreatedByName": "Jane Smith",
      "CreatedByRef": "uuid-...",
      "CreatedOn": ISODate("2023-05-15T10:30:00Z"),
      "CreatedTimeZone": "America/New_York",
      "EmrId": 98765,
      "EndDate": ISODate("2023-06-15T10:30:00Z") or null,
      "Intensity": "Medium",
      "IntensityRef": 7,
      "LastUpdatedBySystemRef": 42,
      "LastUpdatedBySystemValue": "System",
      "NotesOnAcuityChange": "Patient condition improved significantly.",
      "NotesUpdatedOn": ISODate("2023-05-16T14:20:00Z"),
      "PatientRef": 12345,
      "StartDate": ISODate("2023-05-15T10:30:00Z"),
      "UpdatedByName": "Dr. Johnson",
      "UpdatedByRef": "uuid-...",
      "UpdatedOn": ISODate("2023-05-16T14:20:00Z"),
      "UpdatedTimeZone": "America/New_York"
    }
  ],
  "RecordLastModifiedByRef": "uuid-...",
  "RecordLastModifiedUTC": ISODate("2023-11-02T12:00:00Z"),
  "insertedBy": "system",
  "insertedAt": ISODate("2023-11-02T12:00:00Z")
}
```

### Key Features

- **ObjectId Generation:** Documents use ObjectIds with timestamps from the past 7 days
- **Acuity History:** Each patient has 1-3 history entries
- **Null IDs:** At least one history entry has `_id: null` (realistic for embedded documents)
- **Realistic Data:** Names, dates, and values generated using Faker library
- **Audit Fields:** Tracks `insertedBy` and `insertedAt` for debugging

## Migration from JavaScript

This project is a Python migration of the JavaScript `data_faker` tool with equivalent functionality:

| JavaScript                  | Python                  | Status |
| --------------------------- | ----------------------- | ------ |
| `faker.js`                  | `Faker` library         | ✅     |
| `acuityIntensityHistory.js` | `data_generator.py`     | ✅     |
| `config.js`                 | `common_config`         | ✅     |
| `logger.js`                 | `rich.console`          | ✅     |
| Bulk operations             | `pymongo` bulk inserts  | ✅     |
| Connection retry            | Retry logic in `run.py` | ✅     |

## Examples

### Quick Test Data Generation

```bash
# Generate 10 test patients for quick testing
python mongodb_test_data_tools/run.py generate -c Patients -t 10 -b 5 -e DEV
```

### Large Dataset Generation

```bash
# Generate 10,000 patients (for load testing)
python mongodb_test_data_tools/run.py generate -c Patients -t 10000 -b 100 -e DEV
```

### Reproducible Test Data

```bash
# Generate same data every time (useful for consistent testing)
python mongodb_test_data_tools/run.py generate -c Patients -t 50 -e DEV --seed 42
```

## Performance

- **Batch Size:** Larger batches (50-100) provide better performance
- **Connection Pooling:** Uses MongoDB connection pooling for efficiency
- **Typical Rate:** ~500-1000 documents/second (depends on network and MongoDB performance)

## Troubleshooting

### Connection Issues

```
Error: Unable to connect to MongoDB after 5 attempts
```

**Solution:**

- Verify `shared_config/.env` has correct MongoDB URI
- Check network connectivity
- Ensure MongoDB server is running
- Verify credentials are correct

### Import Errors

```
ModuleNotFoundError: No module named 'common_config'
```

**Solution:**

```bash
# Install common_config in development mode
pip install -e common_config/
```

### Permission Denied

```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

```bash
# Make script executable
chmod +x mongodb_test_data_tools/run.py
```

## Best Practices

1. **Always use DEV environment** for test data generation
1. **Verify collection name** before generating large datasets
1. **Use batch sizes** appropriate for your MongoDB instance
1. **Clean up test data** after testing is complete
1. **Use seeds** for reproducible test scenarios

## Related Projects

- **mongodb_index_tools** - MongoDB index management and analysis
- **mongodb_profiler_tools** - Query performance analysis
- **mongodb_masking_tools** - PHI/PII data masking

## Contributing

When modifying this tool:

1. Run linting: `./scripts/lint.sh mongodb_test_data_tools/`
1. Test with small dataset first
1. Verify generated data structure
1. Update documentation

## Author

- **Demesew Abebe**
- **Version:** 1.0.0
- **Date:** 2025-11-02
- **Migrated from:** JavaScript data_faker project

## License

Internal use only - Korrojo/Ubiquity
