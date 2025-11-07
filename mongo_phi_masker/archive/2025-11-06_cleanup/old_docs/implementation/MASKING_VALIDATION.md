# Masking Validation Script

The Masking Validation Script (`scripts/validate_masking.py`) compares original and masked documents to verify that PHI
fields are properly masked while non-PHI fields are preserved. This ensures the masking process is working correctly and
maintaining data integrity.

## Features

- **Field-by-Field Comparison**: Compares every PHI and non-PHI field between original and masked documents
- **PHI Masking Verification**: Ensures PHI fields have been changed (masked)
- **Data Preservation Checks**: Verifies non-PHI fields remain unchanged
- **Statistical Analysis**: Provides detailed statistics on masking success rates
- **Flexible Comparison**: Compare collections in same or different databases
- **Detailed Reporting**: Generates comprehensive JSON reports with field-level details
- **Sample Size Control**: Option to limit validation to a subset of documents

## How It Works

### Validation Algorithm

For each document pair (original vs masked):

1. **PHI Field Validation**:

   - Check if PHI field exists in both documents
   - Verify the value has changed (been masked)
   - Flag if PHI field remains unchanged
   - Track missing PHI fields

1. **Non-PHI Field Validation**:

   - Identify all non-PHI fields (excluding nested PHI containers)
   - Compare original vs masked values
   - Flag any unexpected changes
   - Verify data preservation

1. **Statistics Calculation**:

   - PHI masking rate (% of PHI fields successfully masked)
   - Non-PHI preservation rate (% of non-PHI fields unchanged)
   - Documents with issues
   - Overall validation status

### Validation Status Levels

| Status            | PHI Masking Rate | Non-PHI Preservation Rate |
| ----------------- | ---------------- | ------------------------- |
| EXCELLENT         | ≥ 95%            | ≥ 95%                     |
| GOOD              | ≥ 90%            | ≥ 90%                     |
| ACCEPTABLE        | ≥ 80%            | ≥ 80%                     |
| NEEDS_IMPROVEMENT | ≥ 70%            | Any                       |
| FAILED            | < 70%            | Any                       |

## Usage

### Basic Validation (Same Database)

Compare two collections in the same database:

```bash
python scripts/validate_masking.py \
    --uri mongodb://localhost:27017 \
    --database test_db \
    --original-collection test_Patients_unmasked \
    --masked-collection test_Patients_masked \
    --collection-type Patients
```

### Advanced Examples

#### Compare Collections in Different Databases

```bash
python scripts/validate_masking.py \
    --original-uri mongodb://localhost:27017 \
    --original-db source_db \
    --original-collection Patients \
    --masked-uri mongodb://localhost:27017 \
    --masked-db dest_db \
    --masked-collection Patients_masked \
    --collection-type Patients
```

#### Validate with Sample Size Limit

For large collections, validate only a subset:

```bash
python scripts/validate_masking.py \
    --uri mongodb://localhost:27017 \
    --database test_db \
    --original-collection test_Container_unmasked \
    --masked-collection test_Container_masked \
    --collection-type Container \
    --sample-size 100
```

#### Verbose Output with Custom Report

```bash
python scripts/validate_masking.py \
    --uri mongodb://localhost:27017 \
    --database test_db \
    --original-collection test_Patients_unmasked \
    --masked-collection test_Patients_masked \
    --collection-type Patients \
    --report validation_patients_$(date +%Y%m%d).json \
    --verbose
```

#### Validate Different MongoDB Instances

```bash
python scripts/validate_masking.py \
    --original-uri mongodb://prod-server:27017 \
    --original-db production \
    --original-collection StaffAvailability \
    --masked-uri mongodb://test-server:27017 \
    --masked-db test_environment \
    --masked-collection StaffAvailability_masked \
    --collection-type StaffAvailability
```

## Output

### Console Output

The script provides real-time progress and summary:

```
======================================================================
MongoDB PHI Masker - Masking Validation
======================================================================

Configuration:
  Collection type: Patients
  Original: test_db.test_Patients_unmasked
  Masked: test_db.test_Patients_masked
  Sample size: All documents

2025-01-04 14:30:15 - INFO - Connecting to original: test_db.test_Patients_unmasked
2025-01-04 14:30:15 - INFO - Connecting to masked: test_db.test_Patients_masked
2025-01-04 14:30:15 - INFO - ✓ Connected to both databases
2025-01-04 14:30:15 - INFO - Original documents: 10
2025-01-04 14:30:15 - INFO - Masked documents: 10
2025-01-04 14:30:15 - INFO - Comparing 10 documents...

======================================================================
✓ Validation Complete!
======================================================================

Summary:
  Duration: 2.34s
  Documents analyzed: 10
  Overall status: EXCELLENT

PHI Fields:
  Total checked: 370
  Masked: 350 (94.59%)
  Unchanged: 5
  Documents with issues: 1

Non-PHI Fields:
  Total checked: 180
  Preserved: 180 (100.0%)
  Changed: 0
  Documents with issues: 0

Report saved: reports/validation_report.json

Next steps:
  1. Review full report: cat reports/validation_report.json | jq '.statistics'
  2. Investigate PHI fields that were not masked
```

### Validation Report (JSON)

Detailed JSON report structure:

```json
{
  "validation_timestamp": "2025-01-04T14:30:17",
  "collection_type": "Patients",
  "original": {
    "uri": "mongodb://localhost:27017",
    "database": "test_db",
    "collection": "test_Patients_unmasked",
    "count": 10
  },
  "masked": {
    "uri": "mongodb://localhost:27017",
    "database": "test_db",
    "collection": "test_Patients_masked",
    "count": 10
  },
  "comparison": {
    "documents_compared": 10,
    "missing_in_masked": 0,
    "missing_ids": []
  },
  "statistics": {
    "documents_analyzed": 10,
    "phi_fields": {
      "total_checked": 370,
      "total_masked": 350,
      "total_unchanged": 5,
      "total_missing": 15,
      "masking_rate_percent": 94.59,
      "missing_rate_percent": 4.05,
      "documents_with_issues": 1
    },
    "non_phi_fields": {
      "total_checked": 180,
      "total_preserved": 180,
      "total_changed": 0,
      "preservation_rate_percent": 100.0,
      "documents_with_issues": 0
    },
    "overall_status": "EXCELLENT"
  },
  "document_results": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "phi_fields_checked": 37,
      "phi_fields_masked": 35,
      "phi_fields_unchanged": 0,
      "phi_fields_missing": 2,
      "non_phi_fields_checked": 18,
      "non_phi_fields_preserved": 18,
      "non_phi_fields_changed": 0,
      "phi_field_details": [
        {
          "field": "FirstName",
          "path": "FirstName",
          "status": "MASKED",
          "original": "John",
          "masked": "XXXXX"
        }
      ],
      "non_phi_field_issues": [],
      "errors": []
    }
  ]
}
```

## Command-Line Options

| Option                  | Required | Default                          | Description                                           |
| ----------------------- | -------- | -------------------------------- | ----------------------------------------------------- |
| `--uri`                 | No       | -                                | MongoDB URI (for both collections if same database)   |
| `--database`            | No       | -                                | Database name (for both collections if same database) |
| `--original-uri`        | No       | Value of `--uri`                 | Original collection MongoDB URI                       |
| `--original-db`         | No       | Value of `--database`            | Original database name                                |
| `--original-collection` | Yes      | -                                | Original collection name                              |
| `--masked-uri`          | No       | Value of `--uri`                 | Masked collection MongoDB URI                         |
| `--masked-db`           | No       | Value of `--database`            | Masked database name                                  |
| `--masked-collection`   | Yes      | -                                | Masked collection name                                |
| `--collection-type`     | Yes      | -                                | Collection type (e.g., Patients, Container)           |
| `--sample-size`         | No       | All documents                    | Limit number of documents to compare                  |
| `--report`              | No       | `reports/validation_report.json` | Path to save validation report                        |
| `--verbose`             | No       | False                            | Enable verbose output                                 |

## Typical Workflow

### Complete Testing Workflow

```bash
# 1. Export PHI-rich test data
python scripts/export_test_data.py \
    --collection Patients --count 10 \
    --source-uri mongodb://prod:27017 --source-db production \
    --dest-uri mongodb://localhost:27017 --dest-db test_db \
    --dest-collection test_Patients_unmasked \
    --drop-existing

# 2. Run masking on test data
python masking.py \
    --config config/config_rules/config_Patients.json \
    --env .env.test \
    --collection test_Patients_unmasked

# 3. Validate masking results
python scripts/validate_masking.py \
    --uri mongodb://localhost:27017 --database test_db \
    --original-collection test_Patients_unmasked \
    --masked-collection test_Patients_masked \
    --collection-type Patients \
    --report validation_patients_results.json

# 4. Review validation report
cat validation_patients_results.json | jq '.statistics'
```

### Investigating Issues

If validation reveals issues:

```bash
# Find documents with PHI fields not masked
cat validation_report.json | jq '.document_results[] | select(.phi_fields_unchanged > 0) | {_id, unchanged: .phi_field_details[] | select(.status == "UNCHANGED")}'

# Find documents with changed non-PHI fields
cat validation_report.json | jq '.document_results[] | select(.non_phi_fields_changed > 0) | {_id, issues: .non_phi_field_issues}'

# Get specific field details
cat validation_report.json | jq '.document_results[0].phi_field_details[] | select(.field == "FirstName")'
```

## Understanding Validation Results

### PHI Field Status

- **MASKED**: PHI field value changed from original (expected)
- **UNCHANGED**: PHI field value identical to original (issue!)
- **Missing**: PHI field doesn't exist in one or both documents

### Common Issues

#### PHI Fields Not Masked

**Symptom**: `phi_fields_unchanged > 0`

**Possible causes**:

- Masking rules not configured for that field
- Field path mismatch in `collection_rule_mapping.py`
- Masking rule failed to execute

**Solution**:

1. Check masking rules in `config/masking_rules/rules_{collection}.json`
1. Verify field paths in `config/collection_rule_mapping.py`
1. Review masking logs for errors

#### Non-PHI Fields Changed

**Symptom**: `non_phi_fields_changed > 0`

**Possible causes**:

- Field incorrectly classified as non-PHI
- Masking rule affecting unintended fields
- Data transformation side effects

**Solution**:

1. Verify field classification in `collection_rule_mapping.py`
1. Review masking rules for overly broad patterns
1. Check for nested PHI containers

#### Missing Documents

**Symptom**: `missing_in_masked > 0`

**Possible causes**:

- Masking process failed for some documents
- Incomplete masking run
- Query filters applied during masking

**Solution**:

1. Review masking logs for errors
1. Check masking checkpoint files
1. Verify source and destination collections

## Performance Considerations

- **Document Count**: Validation time scales linearly with document count
- **Sample Size**: Use `--sample-size` for large collections to reduce validation time
- **Network Latency**: Comparing collections on different MongoDB instances incurs network overhead
- **Memory Usage**: Document results are kept in memory for reporting

### Example Performance

| Documents | Collection | Duration | Memory |
| --------- | ---------- | -------- | ------ |
| 10        | Patients   | 2.3s     | 5 MB   |
| 100       | Patients   | 18.5s    | 45 MB  |
| 1,000     | Container  | 2.8m     | 380 MB |
| 10,000    | Tasks      | 24.2m    | 2.1 GB |

For very large collections (>10,000 documents), consider using `--sample-size` to validate a representative subset.

## Troubleshooting

### Connection Errors

```
Error: MongoServerSelectionTimeoutError
```

**Solution**: Verify MongoDB instances are running and URIs are correct:

```bash
mongosh mongodb://localhost:27017 --eval "db.adminCommand('ping')"
```

### Collection Type Not Found

```
Error: No PHI fields found for collection type 'XYZ'
```

**Solution**: Ensure collection type is defined in `config/collection_rule_mapping.py`:

```bash
grep -r "XYZ" config/collection_rule_mapping.py
```

### Document Count Mismatch

```
Warning: Document count mismatch: 100 vs 95
```

**Cause**: Masked collection has fewer documents than original.

**Investigation**:

1. Check masking logs for errors
1. Verify all documents were processed
1. Look for failed inserts in destination

### High Memory Usage

**Symptom**: Script runs slowly or crashes on large collections

**Solution**:

1. Use `--sample-size` to limit documents
1. Validate in batches (run multiple times with different sample ranges)
1. Increase system memory allocation

## Integration with Testing Infrastructure

The validation script is part of the comprehensive testing strategy:

```
Testing Workflow:
1. Generate test data        → scripts/generate_test_patients.py (synthetic data)
2. Export PHI-rich data     → scripts/export_test_data.py (real data subset)
3. Run masking              → masking.py
4. Validate results         → scripts/validate_masking.py ✓ (this script)
5. Analyze performance      → scripts/performance_analysis.py (future)
```

## Related Documentation

- [Test Data Export](TEST_DATA_EXPORT.md) - Exporting PHI-rich test data
- [Test Data Generation](TEST_DATA_GENERATION_PROPOSAL.md) - Generating synthetic test data
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Overall testing infrastructure
- [Testing Environments](TESTING_ENVIRONMENTS.md) - Setting up test environments

## Supported Collections

Works with all collections defined in `config/collection_rule_mapping.py` (70+ collections across 8 categories).

## Best Practices

1. **Always Validate**: Run validation after every masking operation
1. **Use Representative Data**: Export PHI-rich documents for comprehensive testing
1. **Check Reports**: Review validation reports to identify systematic issues
1. **Monitor Trends**: Track masking success rates over time
1. **Investigate Issues**: Don't ignore validation warnings - they indicate real problems
1. **Test Edge Cases**: Include documents with missing fields, nulls, and nested structures
1. **Document Failures**: When validation fails, document the root cause and fix

## Automation

### CI/CD Integration

```yaml
# .github/workflows/masking-validation.yml
- name: Validate Masking
  run: |
    python scripts/export_test_data.py --collection Patients --count 50 \
        --source-uri ${{ secrets.PROD_MONGO_URI }} --source-db prod \
        --dest-uri mongodb://localhost:27017 --dest-db ci_test

    python masking.py --config config/config_rules/config_Patients.json --env .env.test

    python scripts/validate_masking.py \
        --uri mongodb://localhost:27017 --database ci_test \
        --original-collection test_Patients_unmasked \
        --masked-collection test_Patients_masked \
        --collection-type Patients

    # Fail build if validation status is not EXCELLENT or GOOD
    status=$(cat reports/validation_report.json | jq -r '.statistics.overall_status')
    if [[ "$status" != "EXCELLENT" && "$status" != "GOOD" ]]; then
        echo "Validation failed with status: $status"
        exit 1
    fi
```

### Scheduled Validation

```bash
#!/bin/bash
# daily_validation.sh - Run daily masking validation

collections=("Patients" "Container" "Tasks" "StaffAvailability")

for collection in "${collections[@]}"; do
    echo "Validating $collection..."

    python scripts/validate_masking.py \
        --uri mongodb://localhost:27017 --database test_db \
        --original-collection "test_${collection}_unmasked" \
        --masked-collection "test_${collection}_masked" \
        --collection-type "$collection" \
        --report "reports/daily/${collection}_$(date +%Y%m%d).json"

    # Send alert if validation fails
    status=$(cat "reports/daily/${collection}_$(date +%Y%m%d).json" | jq -r '.statistics.overall_status')
    if [[ "$status" == "FAILED" || "$status" == "NEEDS_IMPROVEMENT" ]]; then
        echo "ALERT: $collection validation status: $status" | mail -s "Masking Validation Alert" team@example.com
    fi
done
```

## Next Steps

After validation:

1. **Review Results**: Analyze validation reports to understand masking effectiveness
1. **Fix Issues**: Address any PHI fields that weren't masked or non-PHI fields that changed
1. **Update Rules**: Refine masking rules based on validation findings
1. **Document Patterns**: Identify common validation issues and document solutions
1. **Automate**: Integrate validation into CI/CD pipelines
1. **Monitor**: Track validation metrics over time to ensure quality
