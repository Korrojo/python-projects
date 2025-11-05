#!/bin/bash
###############################################################################
# MongoDB PHI Masking - End-to-End Workflow Orchestrator
#
# This script orchestrates the complete PHI masking workflow:
#   Step 1: Generate test data in LOCAL (simulates production)
#   Step 2: Backup from LOCAL
#   Step 3: Restore to DEV
#   Step 4: Mask data in-situ in DEV
#   Step 5: Backup masked data from DEV
#   Step 6: Restore masked data to LOCAL (final destination)
#
# Usage:
#   ./scripts/workflow_orchestrator.sh --collection Patients --size 10000
#   ./scripts/workflow_orchestrator.sh --collection Patients --size 10000 --automated
#   ./scripts/workflow_orchestrator.sh --collection Patients --size 50000 --interactive
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
COLLECTION=""
DATA_SIZE=10000
MODE="interactive"  # interactive or automated
CONFIG_FILE=""
START_TIME=$(date +%s)

# Function to print colored messages
print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}======================================================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}======================================================================${NC}"
}

print_step() {
    echo ""
    echo -e "${BOLD}${BLUE}▶ Step $1: $2${NC}"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
MongoDB PHI Masking - End-to-End Workflow Orchestrator

Usage:
    $0 --collection COLLECTION --size SIZE [OPTIONS]

Required Arguments:
    --collection COLL      Collection name to process (e.g., Patients)
    --size N               Number of documents to generate (e.g., 10000)

Optional Arguments:
    --config FILE          Path to masking configuration file
                          (default: config/config_rules/config_{collection}.json)
    --interactive          Run in interactive mode (prompt at each step) [DEFAULT]
    --automated            Run in automated mode (no prompts)
    --help                 Show this help message

Workflow Steps:
    1. Generate test data in LOCL (localdb-unmasked)
    2. Backup from LOCL (localdb-unmasked)
    3. Restore to DEV (devdb)
    4. Mask data in-situ in DEV (devdb)
    5. Backup masked data from DEV (devdb)
    6. Restore to LOCL (localdb-masked)

Examples:
    # Interactive mode (default) - prompts before each step
    $0 --collection Patients --size 10000

    # Automated mode - runs all steps without prompts
    $0 --collection Patients --size 50000 --automated

    # With custom config file
    $0 --collection Patients --size 10000 --config config/custom.json

Environment Configuration:
    Loads from shared_config/.env:
      - MONGODB_URI_LOCL / DATABASE_NAME_LOCL
      - MONGODB_URI_DEV / DATABASE_NAME_DEV

EOF
}

# Function to prompt user in interactive mode
prompt_continue() {
    if [ "$MODE" = "interactive" ]; then
        echo ""
        read -p "Continue to next step? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_warning "Workflow cancelled by user"
            exit 0
        fi
    fi
}

# Function to validate document count
validate_count() {
    local env=$1
    local db=$2
    local collection=$3
    local expected=$4
    local description=$5

    print_info "Validating document count in $env/$db.$collection..."

    # Get MongoDB URI from environment
    local uri_var="MONGODB_URI_${env}"
    local mongodb_uri="${!uri_var}"

    # Use mongosh to count documents
    local actual=$(mongosh "$mongodb_uri" --quiet --eval "db = db.getSiblingDB('$db'); db.$collection.countDocuments({})" 2>/dev/null || echo "0")

    if [ "$actual" -eq "$expected" ]; then
        print_success "$description: $actual documents (✓ matches expected)"
        return 0
    else
        print_warning "$description: $actual documents (expected: $expected)"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --collection)
            COLLECTION="$2"
            shift 2
            ;;
        --size)
            DATA_SIZE="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --interactive)
            MODE="interactive"
            shift
            ;;
        --automated)
            MODE="automated"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$COLLECTION" ] || [ -z "$DATA_SIZE" ]; then
    print_error "Missing required arguments"
    show_usage
    exit 1
fi

# Set config file if not provided
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="config/config_rules/config_${COLLECTION}.json"
fi

# Load environment configuration
SHARED_CONFIG="../shared_config/.env"
if [ ! -f "$SHARED_CONFIG" ]; then
    print_error "shared_config/.env not found at $SHARED_CONFIG"
    exit 1
fi

set -a  # Export all variables
source "$SHARED_CONFIG"
set +a

# Main workflow
print_header "MongoDB PHI Masking - End-to-End Workflow"
echo ""
print_info "Collection: $COLLECTION"
print_info "Data Size: $DATA_SIZE documents"
print_info "Config File: $CONFIG_FILE"
print_info "Mode: $MODE"
print_info "Start Time: $(date)"
echo ""

# Validate config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Config file not found: $CONFIG_FILE"
    exit 1
fi

# Database names
LOCL_DB_UNMASKED="${DATABASE_NAME_LOCL}"
LOCL_DB_MASKED="${LOCL_DB_UNMASKED}-masked"
DEV_DB="${DATABASE_NAME_DEV}"

print_info "LOCL Unmasked DB: $LOCL_DB_UNMASKED"
print_info "DEV DB: $DEV_DB"
print_info "LOCL Masked DB: $LOCL_DB_MASKED"
echo ""

if [ "$MODE" = "interactive" ]; then
    print_warning "Running in INTERACTIVE mode - you will be prompted before each step"
    read -p "Press Enter to begin..."
else
    print_info "Running in AUTOMATED mode - all steps will execute without prompts"
    sleep 2
fi

###############################################################################
# STEP 1: Generate Test Data in LOCL
###############################################################################
print_step "1/6" "Generate $DATA_SIZE test documents in LOCL ($LOCL_DB_UNMASKED)"
prompt_continue

python scripts/generate_test_data.py \
    --collection "$COLLECTION" \
    --size "$DATA_SIZE" \
    --env LOCL \
    --db "$LOCL_DB_UNMASKED"

if [ $? -eq 0 ]; then
    print_success "Step 1 complete: Test data generated"
    validate_count "LOCL" "$LOCL_DB_UNMASKED" "$COLLECTION" "$DATA_SIZE" "Generated data"
else
    print_error "Step 1 failed: Data generation failed"
    exit 1
fi

###############################################################################
# STEP 2: Backup from LOCL
###############################################################################
print_step "2/6" "Backup from LOCL ($LOCL_DB_UNMASKED.$COLLECTION)"
prompt_continue

./scripts/backup_collection.sh \
    --env LOCL \
    --db "$LOCL_DB_UNMASKED" \
    --collection "$COLLECTION" \
    --compress

if [ $? -eq 0 ]; then
    # Find the most recent backup directory
    BACKUP_DIR_1=$(ls -td backup/*_${LOCL_DB_UNMASKED}_${COLLECTION} 2>/dev/null | head -n 1)
    print_success "Step 2 complete: Backup created at $BACKUP_DIR_1"
else
    print_error "Step 2 failed: Backup failed"
    exit 1
fi

###############################################################################
# STEP 3: Restore to DEV
###############################################################################
print_step "3/6" "Restore to DEV ($DEV_DB.$COLLECTION)"
prompt_continue

./scripts/restore_collection.sh \
    --env DEV \
    --db "$DEV_DB" \
    --backup-dir "$BACKUP_DIR_1" \
    --drop

if [ $? -eq 0 ]; then
    print_success "Step 3 complete: Data restored to DEV"
    validate_count "DEV" "$DEV_DB" "$COLLECTION" "$DATA_SIZE" "Restored data"
else
    print_error "Step 3 failed: Restore failed"
    exit 1
fi

###############################################################################
# STEP 4: Mask Data in DEV (in-situ)
###############################################################################
print_step "4/6" "Mask data in-situ in DEV ($DEV_DB.$COLLECTION)"
prompt_continue

python masking.py \
    --config "$CONFIG_FILE" \
    --src-env DEV \
    --dst-env DEV \
    --src-db "$DEV_DB" \
    --dst-db "$DEV_DB" \
    --collection "$COLLECTION" \
    --in-situ

if [ $? -eq 0 ]; then
    print_success "Step 4 complete: Data masked"
    validate_count "DEV" "$DEV_DB" "$COLLECTION" "$DATA_SIZE" "Masked data"
else
    print_error "Step 4 failed: Masking failed"
    exit 1
fi

###############################################################################
# STEP 5: Backup Masked Data from DEV
###############################################################################
print_step "5/6" "Backup masked data from DEV ($DEV_DB.$COLLECTION)"
prompt_continue

./scripts/backup_collection.sh \
    --env DEV \
    --db "$DEV_DB" \
    --collection "$COLLECTION" \
    --compress

if [ $? -eq 0 ]; then
    # Find the most recent backup directory
    BACKUP_DIR_2=$(ls -td backup/*_${DEV_DB}_${COLLECTION} 2>/dev/null | head -n 1)
    print_success "Step 5 complete: Masked backup created at $BACKUP_DIR_2"
else
    print_error "Step 5 failed: Backup failed"
    exit 1
fi

###############################################################################
# STEP 6: Restore to LOCL Masked DB
###############################################################################
print_step "6/6" "Restore masked data to LOCL ($LOCL_DB_MASKED.$COLLECTION)"
prompt_continue

./scripts/restore_collection.sh \
    --env LOCL \
    --db "$LOCL_DB_MASKED" \
    --backup-dir "$BACKUP_DIR_2" \
    --drop

if [ $? -eq 0 ]; then
    print_success "Step 6 complete: Masked data restored to LOCL"
    validate_count "LOCL" "$LOCL_DB_MASKED" "$COLLECTION" "$DATA_SIZE" "Final masked data"
else
    print_error "Step 6 failed: Restore failed"
    exit 1
fi

###############################################################################
# WORKFLOW COMPLETE
###############################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

print_header "WORKFLOW COMPLETE!"
echo ""
print_success "All 6 steps executed successfully"
echo ""
print_info "Summary:"
print_info "  Collection: $COLLECTION"
print_info "  Documents: $DATA_SIZE"
print_info "  Duration: ${MINUTES}m ${SECONDS}s"
echo ""
print_info "Backups created:"
print_info "  Unmasked: $BACKUP_DIR_1"
print_info "  Masked:   $BACKUP_DIR_2"
echo ""
print_info "Final data locations:"
print_info "  Unmasked: LOCL / $LOCL_DB_UNMASKED.$COLLECTION"
print_info "  Masked (DEV): DEV / $DEV_DB.$COLLECTION"
print_info "  Masked (LOCL): LOCL / $LOCL_DB_MASKED.$COLLECTION"
echo ""
print_header "Next Steps"
echo ""
print_info "Verify masking results:"
echo "  python scripts/compare_masking.py --src-env LOCL --src-db $LOCL_DB_UNMASKED --dst-env LOCL --dst-db $LOCL_DB_MASKED --collection $COLLECTION"
echo ""
print_info "End Time: $(date)"
print_header "======================================================================"

exit 0
