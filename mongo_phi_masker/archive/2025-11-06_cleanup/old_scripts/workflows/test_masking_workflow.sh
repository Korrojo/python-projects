#!/bin/bash
# Complete workflow to test data generation and masking
# This script demonstrates how to generate test data, load it, and mask it

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== MongoDB PHI Masker - Complete Test Workflow ===${NC}\n"

# Configuration
TEST_DB="phi_masker_test"
TEST_COLLECTION="Patients"
NUM_PATIENTS=100
MONGO_URI="mongodb://localhost:27017"

echo -e "${YELLOW}Configuration:${NC}"
echo "  MongoDB URI: $MONGO_URI"
echo "  Database: $TEST_DB"
echo "  Collection: $TEST_COLLECTION"
echo "  Test Patients: $NUM_PATIENTS"
echo ""

# Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    if [ -d ".venv311" ]; then
        source .venv311/bin/activate
    elif [ -d ".venv312" ]; then
        source .venv312/bin/activate
    else
        echo "Error: No virtual environment found"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Virtual environment: $VIRTUAL_ENV${NC}\n"

# Step 1: Generate test data
echo -e "${BLUE}Step 1: Generating $NUM_PATIENTS test patients...${NC}"
python scripts/generate_test_patients.py \
    --count $NUM_PATIENTS \
    --output test_patients_sample.json

if [ -f "test_patients_sample.json" ]; then
    GENERATED_COUNT=$(python -c "import json; data=json.load(open('test_patients_sample.json')); print(len(data))")
    echo -e "${GREEN}✅ Generated $GENERATED_COUNT patients to test_patients_sample.json${NC}\n"
else
    echo "Error: Failed to generate test data"
    exit 1
fi

# Step 2: Show sample of generated data
echo -e "${BLUE}Step 2: Sample generated patient (first patient):${NC}"
python -c "
import json
with open('test_patients_sample.json', 'r') as f:
    patients = json.load(f)
    if patients:
        patient = patients[0]
        print(json.dumps(patient, indent=2))
" | head -30
echo "  ... (truncated, see test_patients_sample.json for full data)"
echo ""

# Step 3: Load into MongoDB (if MongoDB is available)
echo -e "${BLUE}Step 3: Loading test data into MongoDB...${NC}"
echo "Running: python scripts/generate_test_patients.py --count $NUM_PATIENTS --mongo-uri \"$MONGO_URI\" --database \"$TEST_DB\" --collection \"$TEST_COLLECTION\""
echo ""

python scripts/generate_test_patients.py \
    --count $NUM_PATIENTS \
    --mongo-uri "$MONGO_URI" \
    --database "$TEST_DB" \
    --collection "$TEST_COLLECTION" 2>&1 && echo -e "${GREEN}✅ Successfully loaded $NUM_PATIENTS patients into MongoDB${NC}\n" || {
    echo -e "${YELLOW}⚠️  MongoDB not available or connection failed${NC}"
    echo -e "${YELLOW}   You can skip MongoDB steps and just inspect test_patients_sample.json${NC}\n"
}

# Step 4: Show PHI fields that will be masked
echo -e "${BLUE}Step 4: PHI fields that will be masked (from masking rules):${NC}"
if [ -f "config/masking_rules/rules_Patients.json" ]; then
    python -c "
import json
with open('config/masking_rules/rules_Patients.json', 'r') as f:
    rules = json.load(f)
    print('Total masking rules:', len(rules))
    print('\nSample rules:')
    for i, rule in enumerate(rules[:10]):
        print(f\"  {i+1}. {rule['field']} -> {rule['maskingType']}\")
    if len(rules) > 10:
        print(f'  ... and {len(rules) - 10} more rules')
"
    echo ""
else
    echo "  Masking rules file not found at config/masking_rules/rules_Patients.json"
fi

# Step 5: Instructions for running masker
echo -e "${BLUE}Step 5: How to run the masker:${NC}"
echo ""
echo "Option A: Using Python CLI directly"
echo "  python src/cli/test_cli.py mask \\"
echo "    --source-uri \"$MONGO_URI\" \\"
echo "    --source-db \"$TEST_DB\" \\"
echo "    --source-coll \"$TEST_COLLECTION\" \\"
echo "    --dest-uri \"$MONGO_URI\" \\"
echo "    --dest-db \"${TEST_DB}_masked\" \\"
echo "    --dest-coll \"${TEST_COLLECTION}_masked\" \\"
echo "    --rules-file config/masking_rules/rules_Patients.json \\"
echo "    --batch-size 10"
echo ""

echo "Option B: Using run.py wrapper"
echo "  python run.py \\"
echo "    --source-uri \"$MONGO_URI\" \\"
echo "    --source-db \"$TEST_DB\" \\"
echo "    --source-coll \"$TEST_COLLECTION\" \\"
echo "    --dest-uri \"$MONGO_URI\" \\"
echo "    --dest-db \"${TEST_DB}_masked\" \\"
echo "    --dest-coll \"${TEST_COLLECTION}_masked\" \\"
echo "    --rules config/masking_rules/rules_Patients.json \\"
echo "    --batch-size 10 \\"
echo "    --doc-limit 100"
echo ""

# Step 6: Verify masking (sample Python code)
echo -e "${BLUE}Step 6: Sample code to verify masking worked:${NC}"
cat << 'PYTHON_CODE'
python << EOF
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")

# Get original and masked collections
source_coll = client["phi_masker_test"]["Patients"]
dest_coll = client["phi_masker_test_masked"]["Patients_masked"]

# Get sample documents
source_doc = source_coll.find_one()
masked_doc = dest_coll.find_one()

if source_doc and masked_doc:
    print("\nOriginal Patient:")
    print(f"  FirstName: {source_doc.get('FirstName')}")
    print(f"  LastName: {source_doc.get('LastName')}")
    print(f"  Email: {source_doc.get('Email')}")
    print(f"  MedicareId: {source_doc.get('MedicareId')}")

    print("\nMasked Patient:")
    print(f"  FirstName: {masked_doc.get('FirstName')}")
    print(f"  LastName: {masked_doc.get('LastName')}")
    print(f"  Email: {masked_doc.get('Email')}")
    print(f"  MedicareId: {masked_doc.get('MedicareId')}")

    print("\nVerification:")
    print(f"  Names masked: {source_doc.get('FirstName') != masked_doc.get('FirstName')}")
    print(f"  Email masked: {source_doc.get('Email') != masked_doc.get('Email')}")
else:
    print("No documents found in source or destination collection")

client.close()
EOF
PYTHON_CODE

echo ""
echo -e "${GREEN}=== Test workflow complete! ===${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review generated test data: cat test_patients_sample.json | jq . | less"
echo "  2. Run the masker (see Step 5 above)"
echo "  3. Verify masking worked (see Step 6 above)"
echo "  4. Check logs in logs/ directory"
