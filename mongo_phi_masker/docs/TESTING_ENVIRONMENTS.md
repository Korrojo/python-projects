# Testing mongo_phi_masker with LOCAL and DEV Environments

This guide shows how to test the PHI masker using LOCAL as source and DEV as destination.

## Quick Start

### 1. Create Environment Files

Create separate `.env` files for different test scenarios:

#### `.env.local-to-dev` - Test LOCAL → DEV

```bash
# Source: LOCAL MongoDB
MONGO_SOURCE_HOST=localhost
MONGO_SOURCE_PORT=27017
MONGO_SOURCE_USER=local_user
MONGO_SOURCE_PASSWORD=local_password
MONGO_SOURCE_DB=local_test_db
MONGO_SOURCE_COLL=Patients
MONGO_SOURCE_AUTH_DB=admin
MONGO_SOURCE_USE_SSL=false
MONGO_SOURCE_USE_SRV=false

# Destination: DEV MongoDB
MONGO_DEST_HOST=dev-mongo.example.com
MONGO_DEST_PORT=27017
MONGO_DEST_USER=dev_user
MONGO_DEST_PASSWORD=dev_password
MONGO_DEST_DB=dev_test_db
MONGO_DEST_COLL=Patients_Masked
MONGO_DEST_AUTH_DB=admin
MONGO_DEST_USE_SSL=true
MONGO_DEST_USE_SRV=false

# Processing Configuration
BATCH_SIZE=50
PROCESSING_DOC_LIMIT=100

# Email Alerts (optional)
EMAIL_ENABLED=false

# Logging
MONGO_PHI_LOG_LEVEL=DEBUG
```

#### `.env.dev-to-dev` - Test DEV → DEV (same environment)

```bash
# Source: DEV MongoDB
MONGO_SOURCE_HOST=dev-mongo.example.com
MONGO_SOURCE_PORT=27017
MONGO_SOURCE_USER=dev_user
MONGO_SOURCE_PASSWORD=dev_password
MONGO_SOURCE_DB=dev_source_db
MONGO_SOURCE_COLL=Patients
MONGO_SOURCE_AUTH_DB=admin
MONGO_SOURCE_USE_SSL=true
MONGO_SOURCE_USE_SRV=false

# Destination: DEV MongoDB (different collection)
MONGO_DEST_HOST=dev-mongo.example.com
MONGO_DEST_PORT=27017
MONGO_DEST_USER=dev_user
MONGO_DEST_PASSWORD=dev_password
MONGO_DEST_DB=dev_test_db
MONGO_DEST_COLL=Patients_Masked
MONGO_DEST_AUTH_DB=admin
MONGO_DEST_USE_SSL=true
MONGO_DEST_USE_SRV=false

# Processing Configuration
BATCH_SIZE=100
PROCESSING_DOC_LIMIT=1000

# Email Alerts
EMAIL_ENABLED=true
EMAIL_SENDER=alerts@example.com
EMAIL_PASSWORD=app_password_here
EMAIL_RECIPIENT=dev-team@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Logging
MONGO_PHI_LOG_LEVEL=INFO
```

#### `.env.local-atlas` - Test LOCAL → MongoDB Atlas

```bash
# Source: LOCAL MongoDB
MONGO_SOURCE_HOST=localhost
MONGO_SOURCE_PORT=27017
MONGO_SOURCE_USER=
MONGO_SOURCE_PASSWORD=
MONGO_SOURCE_DB=local_db
MONGO_SOURCE_COLL=TestPatients
MONGO_SOURCE_AUTH_DB=admin
MONGO_SOURCE_USE_SSL=false
MONGO_SOURCE_USE_SRV=false

# Destination: MongoDB Atlas
MONGO_DEST_HOST=cluster0.xxxxx.mongodb.net
MONGO_DEST_PORT=27017
MONGO_DEST_USER=atlas_user
MONGO_DEST_PASSWORD=atlas_password
MONGO_DEST_DB=masked_data
MONGO_DEST_COLL=Patients_Masked
MONGO_DEST_AUTH_DB=admin
MONGO_DEST_USE_SSL=true
MONGO_DEST_USE_SRV=true

# Processing Configuration
BATCH_SIZE=100
PROCESSING_DOC_LIMIT=500

# Logging
MONGO_PHI_LOG_LEVEL=INFO
```

### 2. Create Test Configuration

Create a minimal test config for your specific collection:

#### `config/test/config_local_dev_test.json`

```json
{
    "mongodb": {
        "source": {
            "uri": "${MONGO_SOURCE_URI}",
            "database": "${MONGO_SOURCE_DB}",
            "collection": "${MONGO_SOURCE_COLL}"
        },
        "destination": {
            "uri": "${MONGO_DEST_URI}",
            "database": "${MONGO_DEST_DB}",
            "collection": "${MONGO_DEST_COLL}"
        }
    },
    "processing": {
        "masking_mode": "separate",
        "batch_size": {
            "initial": 50,
            "min": 10,
            "max": 200
        }
    },
    "masking": {
        "rules_path": "config/masking_rules/rules_Patients.json",
        "default_rules": "config/masking_rules/rules_Patients.json",
        "collection_groups": {
            "0": ["Patients"]
        }
    },
    "validation": {
        "enabled": true,
        "max_retries": 3
    },
    "connection": {
        "timeout_ms": 30000,
        "retry_writes": true,
        "retry_reads": true,
        "max_pool_size": 50,
        "min_pool_size": 5
    },
    "phi_collections": ["Patients"]
}
```

## Running Tests

### Option 1: Using Typer CLI (Recommended)

```bash
# Test with LOCAL → DEV
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# Test with limited documents (dry run)
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# Check CLI info
python run.py info
```

### Option 2: Using Legacy Script

```bash
# Test with LOCAL → DEV
python masking.py \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# Test with document limit
python masking.py \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients \
  --limit 100
```

## Verification

### 1. Quick Verification Script

Create a test verification script:

```bash
# Create .env.verify for verification
cat > .env.verify <<EOF
MONGO_VERIFY_URI=mongodb://dev_user:dev_password@dev-mongo.example.com:27017/dev_test_db?authSource=admin&ssl=true
EOF

# Run verification
python scripts/simple_verify.py
```

### 2. Check Results

```python
# Connect to destination and verify
from pymongo import MongoClient

client = MongoClient("mongodb://dev_user:dev_password@dev-mongo.example.com:27017/")
db = client["dev_test_db"]
coll = db["Patients_Masked"]

# Check count
print(f"Masked documents: {coll.count_documents({})}")

# Sample masked document
doc = coll.find_one()
print(f"Sample: {doc}")

# Verify PHI fields are masked
if doc:
    print(f"PatientName: {doc.get('PatientName')}")  # Should be masked
    print(f"Email: {doc.get('Email')}")  # Should be masked
```

## Testing Scenarios

### Scenario 1: Small Dataset Test (Recommended First)

```bash
# Limit to 10 documents for quick test
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients
```

Edit `.env.local-to-dev` to add:

```bash
PROCESSING_DOC_LIMIT=10
```

### Scenario 2: In-Situ Masking Test (Destructive!)

**⚠️ WARNING: This modifies the source database directly!**

```bash
# Only use on TEST data!
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients \
  --in-situ
```

### Scenario 3: Resume from Checkpoint

```bash
# First run (interrupts)
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# Resume (continues from checkpoint)
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# Reset checkpoint and start fresh
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients \
  --reset-checkpoint
```

## Troubleshooting

### Connection Issues

```bash
# Test MongoDB connections
python scripts/test_mongo_connection.py

# Set environment variables
export $(cat .env.local-to-dev | xargs)

# Test source connection
mongosh "mongodb://localhost:27017/local_test_db" --eval "db.Patients.count()"

# Test destination connection
mongosh "mongodb://dev-mongo.example.com:27017/dev_test_db" --authenticationDatabase admin -u dev_user -p
```

### View Logs

```bash
# Check logs
tail -f logs/*/masking_*.log

# Check latest log
ls -lt logs/*/ | head -5
```

### Debug Mode

Enable debug logging:

```bash
# In your .env file
MONGO_PHI_LOG_LEVEL=DEBUG

# Run with debug output
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients \
  --log-file logs/debug_test.log
```

## Best Practices

1. **Start Small**: Test with 10-100 documents first
1. **Use Separate Collections**: Never mask production data directly
1. **Verify Results**: Always run verification scripts after masking
1. **Monitor Logs**: Check logs for errors and performance metrics
1. **Test Masking Rules**: Verify each PHI field type is properly masked
1. **Checkpoint Management**: Use checkpoints for resumability
1. **Environment Isolation**: Keep LOCAL, DEV, and PROD .env files separate

## Example Test Workflow

```bash
# 1. Set up test data in LOCAL
mongoimport --db local_test_db --collection Patients \
  --file sample_data.json --jsonArray

# 2. Test masking (small batch)
python run.py mask \
  --config config/test/config_local_dev_test.json \
  --env .env.local-to-dev \
  --collection Patients

# 3. Verify results in DEV
python scripts/simple_verify.py

# 4. Check masked data quality
python scripts/verify_masking.py

# 5. Review logs
cat logs/*/masking_*.log
```

## Security Notes

- ✅ Never commit `.env` files to git (only `.env.example`)
- ✅ Use strong passwords for all MongoDB connections
- ✅ Enable SSL/TLS for production connections
- ✅ Restrict database user permissions (read on source, write on destination)
- ✅ Use environment-specific credentials
- ✅ Enable email alerts for production runs
- ✅ Regularly rotate credentials

## Performance Tuning

For large datasets, adjust these parameters in your `.env`:

```bash
# Increase batch size for better throughput
BATCH_SIZE=500

# Increase connection pool
# (Edit config JSON)
"max_pool_size": 200

# Disable validation for speed (not recommended)
# (Edit config JSON)
"validation": {"enabled": false}
```
