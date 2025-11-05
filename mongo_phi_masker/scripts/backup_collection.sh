#!/bin/bash
###############################################################################
# MongoDB Collection Backup Script
#
# Backs up a MongoDB collection with timestamp naming convention.
# Integrates with shared_config environment presets.
#
# Usage:
#   ./scripts/backup_collection.sh --env LOCL --collection Patients
#   ./scripts/backup_collection.sh --env DEV --db devdb --collection Patients --output-dir custom/path
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKUP_BASE_DIR="backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
MongoDB Collection Backup Script

Usage:
    $0 --env ENV --collection COLLECTION [OPTIONS]

Required Arguments:
    --env ENV              Environment (LOCL, DEV, STG, PROD, etc.)
    --collection COLL      Collection name to backup

Optional Arguments:
    --db DATABASE          Database name override
    --output-dir DIR       Output directory (default: backup/)
    --compress             Enable compression (gzip)
    --help                 Show this help message

Examples:
    # Backup Patients from LOCL environment
    $0 --env LOCL --collection Patients

    # Backup with custom database and compression
    $0 --env DEV --db devdb --collection Patients --compress

    # Custom output directory
    $0 --env LOCL --collection Patients --output-dir /path/to/backups

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
        --collection)
            COLLECTION="$2"
            shift 2
            ;;
        --db)
            DATABASE_OVERRIDE="$2"
            shift 2
            ;;
        --output-dir)
            BACKUP_BASE_DIR="$2"
            shift 2
            ;;
        --compress)
            COMPRESS=true
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
if [ -z "$ENV" ] || [ -z "$COLLECTION" ]; then
    print_error "Missing required arguments"
    show_usage
    exit 1
fi

# Header
echo "======================================================================"
echo "MongoDB Collection Backup"
echo "======================================================================"
print_info "Environment: $ENV"
print_info "Collection: $COLLECTION"
print_info "Timestamp: $TIMESTAMP"
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

print_info "Database: $DATABASE"
print_info "URI: ${MONGODB_URI%%@*}@***"  # Mask credentials
echo ""

# Create backup directory with timestamp
BACKUP_DIR="${BACKUP_BASE_DIR}/${TIMESTAMP}_${DATABASE}_${COLLECTION}"
mkdir -p "$BACKUP_DIR"

print_info "Backup directory: $BACKUP_DIR"
echo ""

# Build mongodump command
MONGODUMP_CMD="mongodump --uri=\"$MONGODB_URI\" --db=\"$DATABASE\" --collection=\"$COLLECTION\" --out=\"$BACKUP_DIR\""

if [ "$COMPRESS" = true ]; then
    MONGODUMP_CMD="$MONGODUMP_CMD --gzip"
    print_info "Compression: Enabled"
fi

# Execute backup
print_info "Starting backup..."
echo ""

START_TIME=$(date +%s)

if eval $MONGODUMP_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    print_success "Backup completed successfully!"
    print_info "Duration: ${DURATION}s"

    # Show backup size
    if command -v du &> /dev/null; then
        BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
        print_info "Backup size: $BACKUP_SIZE"
    fi

    echo ""
    echo "======================================================================"
    print_success "Backup saved to: $BACKUP_DIR"
    echo "======================================================================"

    exit 0
else
    print_error "Backup failed!"
    exit 1
fi
