# Test Data Export Script

The Test Data Export Script (`scripts/export_test_data.py`) intelligently selects and exports documents with maximum PHI
field coverage for testing purposes. This ensures that your test data includes documents with the richest set of PHI
fields, making it ideal for comprehensive masking validation.

## Features

- **PHI Field Ranking**: Scores documents based on PHI field presence (1 point per field)
- **Intelligent Selection**: Automatically selects documents with highest PHI coverage
- **Flexible Export**: Export to same or different MongoDB instance
- **Detailed Reporting**: Generates JSON reports with scoring details
- **Query Filtering**: Support for MongoDB query filters to narrow selection
- **Collection Management**: Option to drop existing destination collections

## How It Works

### PHI Field Scoring Algorithm

The script uses a simple but effective scoring system:

1. For each document in the source collection:
   - Check presence of each PHI field defined for that collection type
   - Award 1 point for each PHI field that exists and has a non-null/non-empty value
   - Calculate coverage percentage
1. Sort all documents by score (highest first)
1. Select top N documents for export

### Example Scoring

For a `Patients` collection document with 37 PHI fields:

- Document A: 35 fields present = 35 points (94.6% coverage)
- Document B: 28 fields present = 28 points (75.7% coverage)
- Document C: 15 fields present = 15 points (40.5% coverage)

The export script would prioritize Document A > B > C.

## Usage

### Basic Export

Export top 10 PHI-rich documents from Patients collection:

```bash
python scripts/export_test_data.py \
    --collection Patients \
    --count 10 \
    --source-uri mongodb://localhost:27017 \
    --source-db production_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db
```

This creates a collection named `test_Patients_unmasked` in the `test_db` database.

### Advanced Examples

#### Export with Custom Collection Name

```bash
python scripts/export_test_data.py \
    --collection Container \
    --count 20 \
    --source-uri mongodb://localhost:27017 \
    --source-db prod_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --dest-collection test_container_rich_phi
```

#### Export with MongoDB Query Filter

Only export documents matching a specific criteria:

```bash
python scripts/export_test_data.py \
    --collection Patients \
    --count 50 \
    --source-uri mongodb://localhost:27017 \
    --source-db prod_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --query '{"Status": "Active", "CreatedDate": {"$gte": "2024-01-01"}}'
```

#### Drop Existing Collection

Replace existing test collection:

```bash
python scripts/export_test_data.py \
    --collection Patients \
    --count 10 \
    --source-uri mongodb://localhost:27017 \
    --source-db prod_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --drop-existing
```

#### Export to Different MongoDB Instance

```bash
python scripts/export_test_data.py \
    --collection StaffAvailability \
    --count 15 \
    --source-uri mongodb://prod-server:27017 \
    --source-db UbiquityPhiMasked \
    --dest-uri mongodb://test-server:27017 \
    --dest-db test_environment
```

#### Custom Report Location

```bash
python scripts/export_test_data.py \
    --collection Tasks \
    --count 25 \
    --source-uri mongodb://localhost:27017 \
    --source-db prod_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --report reports/tasks_export_$(date +%Y%m%d).json
```

## Output

### Exported Collection

The script creates a new collection in the destination database with documents that have the highest PHI field coverage.
Default naming convention: `test_{collection}_unmasked`

### Scoring Report

A detailed JSON report is generated (default: `reports/phi_export_report.json`) containing:

```json
{
  "collection": "Patients",
  "timestamp": "2025-01-01T10:30:00",
  "total_documents_selected": 10,
  "phi_field_count": 37,
  "phi_fields": ["FirstName", "LastName", "Email", "..."],
  "documents": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "score": 35,
      "coverage_percent": 94.6,
      "present_fields": ["FirstName", "LastName", "Email", "..."],
      "missing_fields": ["MiddleNameLower", "UserName"]
    }
  ]
}
```

## Command-Line Options

| Option              | Required | Default                          | Description                                     |
| ------------------- | -------- | -------------------------------- | ----------------------------------------------- |
| `--collection`      | Yes      | -                                | Source collection name                          |
| `--count`           | No       | 10                               | Number of top documents to export               |
| `--source-uri`      | Yes      | -                                | Source MongoDB connection URI                   |
| `--source-db`       | Yes      | -                                | Source database name                            |
| `--dest-uri`        | Yes      | -                                | Destination MongoDB URI (can be same as source) |
| `--dest-db`         | Yes      | -                                | Destination database name                       |
| `--dest-collection` | No       | `test_{collection}_unmasked`     | Destination collection name                     |
| `--query`           | No       | None                             | MongoDB query filter in JSON format             |
| `--drop-existing`   | No       | False                            | Drop destination collection if it exists        |
| `--report`          | No       | `reports/phi_export_report.json` | Path to save scoring report                     |

## Typical Workflow

### 1. Export PHI-Rich Test Data

```bash
python scripts/export_test_data.py \
    --collection Patients \
    --count 10 \
    --source-uri mongodb://prod:27017 \
    --source-db production \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --drop-existing
```

### 2. Review the Scoring Report

```bash
cat reports/phi_export_report.json | jq '.documents[] | {score, coverage_percent, missing_fields}'
```

### 3. Verify Exported Documents

```bash
mongosh mongodb://localhost:27017/test_db --eval "db.test_Patients_unmasked.count()"
mongosh mongodb://localhost:27017/test_db --eval "db.test_Patients_unmasked.findOne()"
```

### 4. Run Masking on Test Data

```bash
python masking.py \
    --config config/config_rules/config_Patients.json \
    --env .env.test \
    --collection test_Patients_unmasked
```

### 5. Compare Original vs Masked

Use the validation comparison script (coming in Priority 1, Phase 2):

```bash
python scripts/validate_masking.py \
    --original test_Patients_unmasked \
    --masked test_Patients_masked \
    --report validation_results.json
```

## Performance Considerations

- **Document Scanning**: The script scans all documents in the source collection to calculate scores
- **Large Collections**: For collections with millions of documents, consider:
  - Using `--query` to filter to a subset
  - Running during off-peak hours
  - Increasing batch size if needed
- **Memory Usage**: Scoring information is kept in memory for all scanned documents
- **Network**: Exporting to a different MongoDB instance involves network transfer

### Example with Query Filter for Large Collections

```bash
# Export only recent documents
python scripts/export_test_data.py \
    --collection Patients \
    --count 50 \
    --source-uri mongodb://prod:27017 \
    --source-db prod_db \
    --dest-uri mongodb://localhost:27017 \
    --dest-db test_db \
    --query '{"CreatedDate": {"$gte": "2024-01-01"}}'
```

## Troubleshooting

### Connection Errors

```
Error: MongoServerSelectionTimeoutError
```

**Solution**: Verify MongoDB URIs are correct and MongoDB instances are running:

```bash
mongosh mongodb://localhost:27017 --eval "db.adminCommand('ping')"
```

### Collection Not Found

```
Error: Collection 'Patients' not found in mapping
```

**Solution**: Ensure the collection is defined in `config/collection_rule_mapping.py`

### No Documents Found

```
Warning: No documents found matching criteria
```

**Solution**: Check the query filter or verify source collection has documents:

```bash
mongosh mongodb://localhost:27017/source_db --eval "db.Patients.count()"
```

## Integration with Masking Workflow

The export script is part of a comprehensive testing strategy:

```
1. Export PHI-rich documents    → scripts/export_test_data.py
2. Run masking                  → masking.py
3. Validate masking results     → scripts/validate_masking.py (Priority 1, next phase)
4. Analyze performance          → scripts/performance_analysis.py (Priority 2)
```

## Related Documentation

- [Test Data Generation](TEST_DATA_GENERATION_PROPOSAL.md) - Generating synthetic test data with Faker
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Overall testing infrastructure roadmap
- [Testing Environments](TESTING_ENVIRONMENTS.md) - Setting up test environments

## Supported Collections

The script supports all collections defined in `config/collection_rule_mapping.py`:

- **Category 1**: Container (12 PHI fields)
- **Category 2**: Patients, PatientPanel, PatientHistory, PatientNotesHistory (37 PHI fields)
- **Category 3**: PatientsMovedToLocalOutreach, Patients_Dat_Audio_Location_Reset (28 PHI fields)
- **Category 4**: PCP, MedicalRecordRequests, PatientReportFaxQueue, etc. (10 PHI fields)
- **Category 5**: Appointments, OfflineAppointments, StaffAvailability, etc. (10 PHI fields)
- **Category 6**: PatientCarePlan, PatientCarePlanHistory (5 PHI fields)
- **Category 7**: PatientInsuranceHistory (3 PHI fields)
- **Category 8**: Tasks, Messages, ExternalReferral, etc. (4 PHI fields)

## Next Steps

After exporting test data:

1. **Validate Field Coverage**: Review the scoring report to ensure adequate PHI field coverage
1. **Run Masking**: Use the exported data as input for masking tests
1. **Compare Results**: Use validation scripts to verify masking accuracy
1. **Iterate**: If coverage is insufficient, adjust `--count` or `--query` parameters
