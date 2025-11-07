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

# Setup logging
LOG_DIR="logs/restore"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Logging functions with consistent format: YYYY-MM-DD HH:MM:SS | LEVEL | message
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}${timestamp} | INFO | ${NC}$1"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}${timestamp} | SUCCESS | ${NC}$1"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}${timestamp} | ERROR | ${NC}$1"
}

log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}${timestamp} | WARNING | ${NC}$1"
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
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$ENV" ] || [ -z "$BACKUP_DIR" ]; then
    log_error "Missing required arguments"
    show_usage
    exit 1
fi

# Validate backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    log_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Setup log file - extract collection name from backup directory
# Backup dir format: YYYYMMDD_HHMMSS_database_collection
BACKUP_DIR_NAME=$(basename "$BACKUP_DIR")
COLLECTION_NAME=$(echo "$BACKUP_DIR_NAME" | rev | cut -d'_' -f1 | rev)
LOG_FILE="${LOG_DIR}/${TIMESTAMP}_restore_${COLLECTION_NAME}.log"

# Redirect all output to both console and log file (strip ANSI colors from log file)
exec > >(tee >(sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"))
exec 2>&1

# Header
echo "======================================================================"
echo "MongoDB Collection Restore"
echo "======================================================================"
log_info "Environment: $ENV"
log_info "Backup directory: $BACKUP_DIR"
log_info "Log file: $LOG_FILE"
echo ""

# Load environment configuration from shared_config/.env
# Get script directory to find shared_config relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SHARED_CONFIG="$(cd "$PROJECT_ROOT/.." && pwd)/shared_config/.env"

if [ ! -f "$SHARED_CONFIG" ]; then
    log_error "shared_config/.env not found at $SHARED_CONFIG"
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
    log_error "MongoDB URI not configured for $ENV environment"
    log_error "Please set $URI_VAR in shared_config/.env"
    exit 1
fi

if [ -z "$DATABASE" ]; then
    log_error "Database name not configured for $ENV environment"
    log_error "Please set $DB_VAR in shared_config/.env or use --db option"
    exit 1
fi

log_info "Target database: $DATABASE"
# Extract and mask URI - show only protocol and host, hide credentials completely
if [[ $MONGODB_URI =~ ^([^:]+://)([^@]+@)?(.+)$ ]]; then
    PROTOCOL="${BASH_REMATCH[1]}"
    HOST="${BASH_REMATCH[3]%%/*}"  # Get host before first /
    log_info "URI: ${PROTOCOL}***:***@${HOST}"
else
    log_info "URI: [REDACTED]"
fi
echo ""

# Detect source database and collection from backup directory structure
# Backup dir structure: backup_dir/source_database/collection.bson
SOURCE_DB=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1 | xargs basename)
if [ -z "$SOURCE_DB" ]; then
    log_error "Cannot detect source database from backup directory"
    exit 1
fi

log_info "Source database (from backup): $SOURCE_DB"

# List collections in backup
COLLECTIONS=$(find "$BACKUP_DIR/$SOURCE_DB" -name "*.bson" -o -name "*.bson.gz" | xargs -n1 basename | sed 's/\.bson.*$//' | sort -u)
COLLECTION_COUNT=$(echo "$COLLECTIONS" | wc -l | tr -d ' ')

log_info "Collections in backup: $COLLECTION_COUNT"
for coll in $COLLECTIONS; do
    log_info "  - $coll"
done
echo ""

# Build mongorestore command using modern --nsInclude instead of deprecated --db/--collection
MONGORESTORE_CMD="mongorestore --uri=\"$MONGODB_URI\""

if [ "$DROP" = true ]; then
    MONGORESTORE_CMD="$MONGORESTORE_CMD --drop"
    log_warning "Drop mode: Existing collection(s) will be dropped"
fi

# Use --nsInclude for modern MongoDB restore (avoids deprecation warning)
# Restore specific collection and remap to target database
MONGORESTORE_CMD="$MONGORESTORE_CMD --nsInclude=\"${SOURCE_DB}.${COLLECTION_NAME}\""
MONGORESTORE_CMD="$MONGORESTORE_CMD --nsFrom=\"${SOURCE_DB}.${COLLECTION_NAME}\""
MONGORESTORE_CMD="$MONGORESTORE_CMD --nsTo=\"${DATABASE}.${COLLECTION_NAME}\""

# Add specific directory to restore from
MONGORESTORE_CMD="$MONGORESTORE_CMD --dir=\"$BACKUP_DIR\""

# Check for gzip compression
if ls "$BACKUP_DIR/$SOURCE_DB"/*.bson.gz 1> /dev/null 2>&1; then
    MONGORESTORE_CMD="$MONGORESTORE_CMD --gzip"
    log_info "Compression detected: Enabled"
fi

# Confirmation prompt
echo ""
log_warning "About to restore backup to: $ENV / $DATABASE"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Restore cancelled"
    exit 0
fi

# Execute restore
log_info "Starting restore..."
echo ""

START_TIME=$(date +%s)

if eval $MONGORESTORE_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    log_success "Restore completed successfully!"
    log_info "Duration: ${DURATION}s"

    echo ""
    echo "======================================================================"
    log_success "Data restored to: $ENV / $DATABASE"
    echo "======================================================================"

    exit 0
else
    log_error "Restore failed!"
    exit 1
fi
