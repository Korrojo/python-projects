# Quick Start: Testing Data Generation and Masking

This guide shows you how to test the complete workflow: generate test data → load into MongoDB → mask PHI data → verify
results.

## Prerequisites

- Python virtual environment activated
- MongoDB running locally (optional, can test without)
- All dependencies installed: `pip install -r requirements.txt`

## Quick Testing (No MongoDB Required)

### 1. Generate Sample Test Data

```bash
# Generate 10 test patients to a JSON file
python scripts/generate_test_data.py --count 10 --output test_patients.json

# View the generated data
cat test_patients.json | python -m json.tool | less
```

### 2. Inspect Generated PHI Fields

```bash
# View a single patient record
python -c "
import json
with open('test_patients.json') as f:
    patients = json.load(f)
    print(json.dumps(patients[0], indent=2))
" | less
```

**PHI fields included (34 total):**

- Personal: FirstName, LastName, Email, Dob, MedicareId
- Contact: PhoneNumber, HomePhoneNumber, WorkPhoneNumber
- Address: Street1, City, StateName, Zip5
- Clinical: Notes, Comments, FinalNotes, etc.

## Full Workflow Testing (With MongoDB)

### 1. Generate and Load Test Data

```bash
# Generate 100 patients directly into MongoDB
python scripts/generate_test_data.py \
  --count 100 \
  --mongo-uri "mongodb://localhost:27017" \
  --database phi_test_srcdb \
  --collection Patients
```

### 2. Run the Masker

Option A: Using the test helper script:

```bash
# Set up environment (if not already done)
cp .env.local-to-dev.example .env.local-to-dev
# Edit .env.local-to-dev with your MongoDB credentials

# Run masking test
./scripts/test_local_to_dev.sh Patients 100
```

Option B: Using Python CLI directly:

```bash
python src/cli/test_cli.py mask \
  --source-uri "mongodb://localhost:27017" \
  --source-db "phi_test_srcdb" \
  --source-coll "Patients" \
  --dest-uri "mongodb://localhost:27017" \
  --dest-db "phi_test_dstdb" \
  --dest-coll "Patients_masked" \
  --rules-file config/masking_rules/rules_Patients.json \
  --batch-size 10 \
  --doc-limit 100
```

### 3. Verify Masking Worked

```python
# Create a verification script
python << 'EOF'
from pymongo import MongoClient
import json

# Connect
client = MongoClient("mongodb://localhost:27017")
source = client["phi_test_srcdb"]["Patients"]
masked = client["phi_test_dstdb"]["Patients_masked"]

# Get first document from each
orig = source.find_one()
mask = masked.find_one()

if orig and mask:
    print("=" * 60)
    print("ORIGINAL PATIENT (PHI Exposed):")
    print("=" * 60)
    print(f"FirstName:   {orig.get('FirstName')}")
    print(f"LastName:    {orig.get('LastName')}")
    print(f"Email:       {orig.get('Email')}")
    print(f"MedicareId:  {orig.get('MedicareId')}")
    print(f"Address:     {orig.get('Address', {}).get('Street1')}")
    print(f"Phone:       {orig.get('Contacts', {}).get('HomePhoneNumber')}")

    print("\n" + "=" * 60)
    print("MASKED PATIENT (PHI Protected):")
    print("=" * 60)
    print(f"FirstName:   {mask.get('FirstName')}")
    print(f"LastName:    {mask.get('LastName')}")
    print(f"Email:       {mask.get('Email')}")
    print(f"MedicareId:  {mask.get('MedicareId')}")
    print(f"Address:     {mask.get('Address', {}).get('Street1')}")
    print(f"Phone:       {mask.get('Contacts', {}).get('HomePhoneNumber')}")

    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS:")
    print("=" * 60)
    name_masked = orig.get('FirstName') != mask.get('FirstName')
    email_masked = orig.get('Email') != mask.get('Email')
    phone_masked = orig.get('Contacts', {}).get('HomePhoneNumber') != mask.get('Contacts', {}).get('HomePhoneNumber')

    print(f"✓ FirstName masked: {name_masked}")
    print(f"✓ Email masked:     {email_masked}")
    print(f"✓ Phone masked:     {phone_masked}")

    if name_masked and email_masked:
        print("\n✅ SUCCESS: PHI fields are properly masked!")
    else:
        print("\n❌ WARNING: Some fields may not be masked")
else:
    print("❌ No documents found in collections")

client.close()
EOF
```

## Automated Test Workflow

Run the complete workflow automatically:

```bash
./scripts/test_masking_workflow.sh
```

This script will:

1. Generate 100 test patients
1. Show a sample of the generated data
1. Load data into MongoDB (if available)
1. Show masking rules
1. Provide commands to run masker
1. Provide verification code

## Common Commands

```bash
# Generate 1000 patients for load testing
python scripts/generate_test_data.py --count 1000 \
  --mongo-uri "mongodb://localhost:27017" \
  --database phi_test_load \
  --collection Patients

# Generate with custom seed (reproducible data)
python scripts/generate_test_data.py --count 50 \
  --seed 12345 \
  --output reproducible_test.json

# Quick sanity check: Generate 5 patients and view
python scripts/generate_test_data.py --count 5 --output quick_test.json && \
  cat quick_test.json | python -m json.tool
```

## Inspect Masking Rules

```bash
# View all masking rules for Patients collection
cat config/masking_rules/rules_Patients.json | python -m json.tool | less

# Count total rules
python -c "
import json
with open('config/masking_rules/rules_Patients.json') as f:
    rules = json.load(f)
    print(f'Total masking rules: {len(rules)}')

    # Group by masking type
    by_type = {}
    for rule in rules:
        mask_type = rule.get('maskingType', 'unknown')
        by_type[mask_type] = by_type.get(mask_type, 0) + 1

    print('\nRules by type:')
    for mask_type, count in sorted(by_type.items()):
        print(f'  {mask_type}: {count}')
"
```

## Cleanup Test Data

```bash
# Remove generated JSON files
rm -f test_patients*.json test_patients.json

# Drop test databases (MongoDB)
python << EOF
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
client.drop_database("phi_test_srcdb")
client.drop_database("phi_test_dstdb")
client.drop_database("phi_test_load")
print("✓ Test databases dropped")
EOF
```

## Troubleshooting

### MongoDB Connection Failed

If MongoDB is not running:

- **macOS**: `brew services start mongodb-community`
- **Linux**: `sudo systemctl start mongod`
- **Docker**: `docker run -d -p 27017:27017 mongo:latest`

Or skip MongoDB and just inspect the generated JSON files.

### "ModuleNotFoundError: No module named 'Faker'"

Install dependencies:

```bash
pip install -r requirements.txt
```

### "No module named 'pkg_resources'" (Python 3.12)

This should be fixed in requirements.txt, but if you see it:

```bash
pip install setuptools
```

## Next Steps

1. **Generate realistic test data** with varying sizes (10, 100, 1000, 10000 documents)
1. **Run performance tests** to measure masking throughput
1. **Test specific masking rules** by examining before/after documents
1. **Validate all PHI fields** are properly masked
1. **Review logs** in `logs/` directory for any issues

## More Information

- Full documentation: `docs/TEST_DATA_GENERATION_PROPOSAL.md`
- Testing environments: `docs/TESTING_ENVIRONMENTS.md`
- Masking rules: `config/masking_rules/rules_Patients.json`
- Schema documentation: `docs/schema/`
