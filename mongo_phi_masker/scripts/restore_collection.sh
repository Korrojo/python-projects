#!/bin/bash
###############################################################################
# MongoDB Collection Restore Script
#
# Restores a MongoDB collection from backup with environment support.
# Integrates with shared_config environment presets.
#
# Usage:
#   ./scripts/restore_collection.sh --env DEV --backup-dir backup/20251105_120000_localdb_Patients
#   ./scripts/restore_collection.sh --env LOCL --db localdb-masked --backup-dir backup/...
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
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
MongoDB Collection Restore Script

Usage:
    $0 --env ENV --backup-dir BACKUP_DIR [OPTIONS]

Required Arguments:
    --env ENV              Target environment (LOCL, DEV, STG, PROD, etc.)
    --backup-dir DIR       Backup directory to restore from

Optional Arguments:
    --db DATABASE          Database name override
    --drop                 Drop collection before restoring
    --help                 Show this help message

Examples:
    # Restore to DEV environment
    $0 --env DEV --backup-dir backup/20251105_120000_localdb_Patients

    # Restore with custom database and drop existing
    $0 --env LOCL --db localdb-masked --backup-dir backup/... --drop

    # Restore specific backup
    $0 --env DEV --backup-dir backup/20251105_120000_devdb_Patients

Environment Configuration:
    Loads MongoDB URI and database from shared_config/.env
    Environment variables used:
      - MONGODB_URI_{ENV}
      - DATABASE_NAME_{ENV}

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENV="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --db)
            DATABASE_OVERRIDE="$2"
            shift 2
            ;;
        --drop)
            DROP=true
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
if [ -z "$ENV" ] || [ -z "$BACKUP_DIR" ]; then
    print_error "Missing required arguments"
    show_usage
    exit 1
fi

# Validate backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Header
echo "======================================================================"
echo "MongoDB Collection Restore"
echo "======================================================================"
print_info "Environment: $ENV"
print_info "Backup directory: $BACKUP_DIR"
echo ""

# Load environment configuration from shared_config/.env
SHARED_CONFIG="../shared_config/.env"
if [ ! -f "$SHARED_CONFIG" ]; then
    print_error "shared_config/.env not found at $SHARED_CONFIG"
    exit 1
fi

# Source the shared config
set -a  # Export all variables
source "$SHARED_CONFIG"
set +a

# Get MongoDB URI and database from environment
URI_VAR="MONGODB_URI_${ENV}"
DB_VAR="DATABASE_NAME_${ENV}"

MONGODB_URI="${!URI_VAR}"
DATABASE="${DATABASE_OVERRIDE:-${!DB_VAR}}"

if [ -z "$MONGODB_URI" ]; then
    print_error "MongoDB URI not configured for $ENV environment"
    print_error "Please set $URI_VAR in shared_config/.env"
    exit 1
fi

if [ -z "$DATABASE" ]; then
    print_error "Database name not configured for $ENV environment"
    print_error "Please set $DB_VAR in shared_config/.env or use --db option"
    exit 1
fi

print_info "Target database: $DATABASE"
print_info "URI: ${MONGODB_URI%%@*}@***"  # Mask credentials
echo ""

# Detect source database and collection from backup directory structure
# Backup dir structure: backup_dir/source_database/collection.bson
SOURCE_DB=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1 | xargs basename)
if [ -z "$SOURCE_DB" ]; then
    print_error "Cannot detect source database from backup directory"
    exit 1
fi

print_info "Source database (from backup): $SOURCE_DB"

# List collections in backup
COLLECTIONS=$(find "$BACKUP_DIR/$SOURCE_DB" -name "*.bson" -o -name "*.bson.gz" | xargs -n1 basename | sed 's/\.bson.*$//' | sort -u)
COLLECTION_COUNT=$(echo "$COLLECTIONS" | wc -l | tr -d ' ')

print_info "Collections in backup: $COLLECTION_COUNT"
for coll in $COLLECTIONS; do
    print_info "  - $coll"
done
echo ""

# Build mongorestore command
MONGORESTORE_CMD="mongorestore --uri=\"$MONGODB_URI\" --db=\"$DATABASE\""

if [ "$DROP" = true ]; then
    MONGORESTORE_CMD="$MONGORESTORE_CMD --drop"
    print_warning "Drop mode: Existing collection(s) will be dropped"
fi

# Add specific directory to restore from
MONGORESTORE_CMD="$MONGORESTORE_CMD --dir=\"$BACKUP_DIR/$SOURCE_DB\""

# Check for gzip compression
if ls "$BACKUP_DIR/$SOURCE_DB"/*.bson.gz 1> /dev/null 2>&1; then
    MONGORESTORE_CMD="$MONGORESTORE_CMD --gzip"
    print_info "Compression detected: Enabled"
fi

# Confirmation prompt
echo ""
print_warning "About to restore backup to: $ENV / $DATABASE"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Restore cancelled"
    exit 0
fi

# Execute restore
print_info "Starting restore..."
echo ""

START_TIME=$(date +%s)

if eval $MONGORESTORE_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    print_success "Restore completed successfully!"
    print_info "Duration: ${DURATION}s"

    echo ""
    echo "======================================================================"
    print_success "Data restored to: $ENV / $DATABASE"
    echo "======================================================================"

    exit 0
else
    print_error "Restore failed!"
    exit 1
fi
