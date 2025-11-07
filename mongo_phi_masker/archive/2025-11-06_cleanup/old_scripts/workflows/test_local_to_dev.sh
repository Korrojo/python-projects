#!/bin/bash
# Quick test script for LOCAL → DEV masking
# Usage: ./scripts/test_local_to_dev.sh [collection_name] [doc_limit]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
COLLECTION=${1:-Patients}
DOC_LIMIT=${2:-10}
ENV_FILE=".env.local-to-dev"
CONFIG_FILE="config/test/config_test.json"

echo -e "${GREEN}=== MongoDB PHI Masker: LOCAL → DEV Test ===${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: $ENV_FILE not found!${NC}"
    echo ""
    echo "Create it from the example:"
    echo "  cp .env.local-to-dev.example $ENV_FILE"
    echo "  # Edit $ENV_FILE with your credentials"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: $CONFIG_FILE not found!${NC}"
    exit 1
fi

# Set document limit
export PROCESSING_DOC_LIMIT=$DOC_LIMIT

echo -e "${YELLOW}Test Configuration:${NC}"
echo "  Collection: $COLLECTION"
echo "  Document Limit: $DOC_LIMIT"
echo "  Environment: $ENV_FILE"
echo "  Config: $CONFIG_FILE"
echo ""

# Test source connection
echo -e "${YELLOW}Step 1: Testing source connection...${NC}"
source $ENV_FILE
if python -c "
from pymongo import MongoClient
import os
try:
    client = MongoClient(os.getenv('MONGO_SOURCE_HOST'), int(os.getenv('MONGO_SOURCE_PORT')), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Source connection successful')
except Exception as e:
    print(f'✗ Source connection failed: {e}')
    exit(1)
" ; then
    echo -e "${GREEN}✓ Source MongoDB accessible${NC}"
else
    echo -e "${RED}✗ Cannot connect to source MongoDB${NC}"
    exit 1
fi
echo ""

# Test destination connection
echo -e "${YELLOW}Step 2: Testing destination connection...${NC}"
if python -c "
from pymongo import MongoClient
import os
try:
    host = os.getenv('MONGO_DEST_HOST')
    port = int(os.getenv('MONGO_DEST_PORT'))
    user = os.getenv('MONGO_DEST_USER')
    password = os.getenv('MONGO_DEST_PASSWORD')

    if user and password:
        uri = f'mongodb://{user}:{password}@{host}:{port}/?authSource=admin'
    else:
        uri = f'mongodb://{host}:{port}'

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Destination connection successful')
except Exception as e:
    print(f'✗ Destination connection failed: {e}')
    exit(1)
" ; then
    echo -e "${GREEN}✓ Destination MongoDB accessible${NC}"
else
    echo -e "${RED}✗ Cannot connect to destination MongoDB${NC}"
    exit 1
fi
echo ""

# Check source collection exists and has data
echo -e "${YELLOW}Step 3: Checking source collection...${NC}"
SOURCE_COUNT=$(python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGO_SOURCE_HOST'), int(os.getenv('MONGO_SOURCE_PORT')))
db = client[os.getenv('MONGO_SOURCE_DB')]
coll = db[os.getenv('MONGO_SOURCE_COLL')]
print(coll.count_documents({}))
")

if [ "$SOURCE_COUNT" -eq 0 ]; then
    echo -e "${RED}✗ Source collection is empty!${NC}"
    echo "  Database: $MONGO_SOURCE_DB"
    echo "  Collection: $MONGO_SOURCE_COLL"
    exit 1
fi

echo -e "${GREEN}✓ Source collection has $SOURCE_COUNT documents${NC}"
echo ""

# Run masking
echo -e "${YELLOW}Step 4: Running masking...${NC}"
echo ""

python run.py mask \
    --config "$CONFIG_FILE" \
    --env "$ENV_FILE" \
    --collection "$COLLECTION"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Masking Completed Successfully! ===${NC}"
    echo ""

    # Show results
    echo -e "${YELLOW}Step 5: Checking results...${NC}"
    DEST_COUNT=$(python -c "
from pymongo import MongoClient
import os
host = os.getenv('MONGO_DEST_HOST')
port = int(os.getenv('MONGO_DEST_PORT'))
user = os.getenv('MONGO_DEST_USER')
password = os.getenv('MONGO_DEST_PASSWORD')

if user and password:
    uri = f'mongodb://{user}:{password}@{host}:{port}/?authSource=admin'
else:
    uri = f'mongodb://{host}:{port}'

client = MongoClient(uri)
db = client[os.getenv('MONGO_DEST_DB')]
coll = db[os.getenv('MONGO_DEST_COLL')]
print(coll.count_documents({}))
    ")

    echo -e "${GREEN}✓ Destination collection now has $DEST_COUNT masked documents${NC}"
    echo ""

    # Show sample masked document
    echo -e "${YELLOW}Sample masked document:${NC}"
    python -c "
from pymongo import MongoClient
import os
import json

host = os.getenv('MONGO_DEST_HOST')
port = int(os.getenv('MONGO_DEST_PORT'))
user = os.getenv('MONGO_DEST_USER')
password = os.getenv('MONGO_DEST_PASSWORD')

if user and password:
    uri = f'mongodb://{user}:{password}@{host}:{port}/?authSource=admin'
else:
    uri = f'mongodb://{host}:{port}'

client = MongoClient(uri)
db = client[os.getenv('MONGO_DEST_DB')]
coll = db[os.getenv('MONGO_DEST_COLL')]

doc = coll.find_one({}, {'_id': 0})
if doc:
    print(json.dumps(doc, indent=2, default=str))
else:
    print('No documents found')
    "

    echo ""
    echo -e "${GREEN}✓ Test complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review logs in logs/ directory"
    echo "  2. Run verification: python scripts/simple_verify.py"
    echo "  3. Compare source vs masked: python scripts/compare_masking.py"
else
    echo ""
    echo -e "${RED}✗ Masking failed with exit code $EXIT_CODE${NC}"
    echo ""
    echo "Check logs for details:"
    echo "  tail -100 logs/*/masking_*.log"
    exit $EXIT_CODE
fi
