#!/bin/bash
###############################################################################
# Production PHI Masking Orchestration Script
#
# Orchestrates the complete masking workflow (Steps 0-6):
# 0. Validate collection configuration (automatic pre-flight check)
# 1. Backup source data
# 2. Restore to processing environment
# 3. Mask data in-situ
# 4. Backup masked data
# 5. Restore to destination
# 6. Verify masking results
#
# Usage:
#   ./scripts/orchestrate_masking.sh \
#     --src-env PROD \
#     --src-db prod-db \
#     --proc-env DEV \
#     --proc-db dev-phidb \
#     --dst-env PROD \
#     --dst-db prod-db-masked \
#     --collection Patients
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Setup logging
LOG_DIR="logs/orchestration"
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

log_step() {
    local step_num=$1
    local step_desc=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${timestamp} | STEP ${step_num} | ${step_desc}${NC}"
    echo -e "${CYAN}======================================================================${NC}"
}

# Function to send email notification
send_notification() {
    if [ "$ENABLE_EMAIL" = false ]; then
        return 0
    fi

    python scripts/send_notification.py "$@" || true
}

# Function to send failure notification and exit
send_failure_and_exit() {
    local step=$1
    local step_name=$2
    local error=$3

    log_error "$step_name"

    # Send failure notification
    send_notification failure \
        --collection "$COLLECTION" \
        --step "$step" \
        --step-name "$step_name" \
        --error "$error" \
        --log-file "$LOG_FILE" \
        --src-env "$SRC_ENV" \
        --proc-env "$PROC_ENV" \
        --dst-env "$DST_ENV"

    exit 1
}

# Function to show usage
show_usage() {
    cat << EOF
Production PHI Masking Orchestration Script

Usage:
    $0 [OPTIONS]

Required Arguments:
    --src-env ENV           Source environment (PROD, STG, etc.)
    --src-db DATABASE       Source database name
    --proc-env ENV          Processing environment (DEV, STG, etc.)
    --proc-db DATABASE      Processing database name
    --dst-env ENV           Destination environment (PROD, STG, etc.)
    --dst-db DATABASE       Destination database name
    --collection COLL       Collection to mask

Optional Arguments:
    --skip-backup-source    Skip Step 1 (backup source)
                            - Uses most recent existing backup instead
                            - Source database is NOT accessed/modified

    --skip-backup-masked    Skip Step 4 (backup masked data)
                            - No backup created from processing environment
                            - CASCADING EFFECT: Auto-skips Step 5 (restore to destination)
                            - Result: Masked data stays in processing environment ONLY
                            - Destination database is NEVER created/populated

    --skip-restore-dest     Skip Step 5 (restore to destination)
                            - Masked data not restored to destination
                            - Destination database is NEVER created/populated

    --skip-validation       Skip Step 0 (configuration validation)
                            - Bypasses pre-flight configuration checks
                            - Use only if you're confident config is valid

    --skip-verification     Skip Step 6 (verification)
                            - No masking verification performed

    --verify-samples N      Number of samples for verification (default: 5)

    --no-email              Disable email notifications for this run
                            - Overrides EMAIL_NOTIFICATIONS_ENABLED in .env

    --help                  Show this help message

Data Flow Based on Flags:
    NO FLAGS (Full Production):
        Source DB → Backup → Processing DB → Mask → Backup → Destination DB
        Result: Masked data in DESTINATION database

    --skip-backup-source --skip-backup-masked (Development/Testing):
        Existing Backup → Processing DB → Mask (stays in Processing DB)
        Result: Masked data in PROCESSING database ONLY
        Note: Source and Destination databases are NEVER touched

    --skip-backup-source (Use existing backup):
        Existing Backup → Processing DB → Mask → Backup → Destination DB
        Result: Masked data in DESTINATION database

Examples:
    # Example 1: Full Production Workflow (ALL steps run)
    # Creates: prod-phidb-masked with masked data
    # Source and destination are in PROD environment
    $0 \\
      --src-env PROD \\
      --src-db prod-phidb \\
      --proc-env DEV \\
      --proc-db dev-phidb \\
      --dst-env PROD \\
      --dst-db prod-phidb-masked \\
      --collection Patients

    # Example 2: Development/Testing (Skip backups)
    # Masked data stays in: DEV/dev-phidb ONLY
    # Local databases (local-phi-unmasked, local-phi-masked) are NEVER created
    # Use this when you only want to mask data in DEV for testing
    $0 \\
      --src-env LOCL \\
      --src-db local-phi-unmasked \\
      --proc-env DEV \\
      --proc-db dev-phidb \\
      --dst-env LOCL \\
      --dst-db local-phi-masked \\
      --collection Patients \\
      --skip-backup-source \\
      --skip-backup-masked

    # Example 3: Create Local Masked Database (Run ALL steps)
    # Requires: local-phi-unmasked exists (run Step 0 first)
    # Creates: local-phi-masked with masked data
    # This populates both local databases for local testing
    $0 \\
      --src-env LOCL \\
      --src-db local-phi-unmasked \\
      --proc-env DEV \\
      --proc-db dev-phidb \\
      --dst-env LOCL \\
      --dst-db local-phi-masked \\
      --collection Patients

Workflow Steps:
    Step 0: Validate collection configuration (automatic pre-flight check)
    Step 1: Backup source data
    Step 2: Restore to processing environment
    Step 3: Mask data in-situ
    Step 4: Backup masked data
    Step 5: Restore masked data to destination
    Step 6: Verify masking results

EOF
}

# Parse arguments
SKIP_VALIDATION=false
SKIP_BACKUP_SOURCE=false
SKIP_BACKUP_MASKED=false
SKIP_RESTORE_DEST=false
SKIP_VERIFICATION=false
VERIFY_SAMPLES=5
ENABLE_EMAIL=true  # Can be overridden by --no-email

while [[ $# -gt 0 ]]; do
    case $1 in
        --src-env)
            SRC_ENV="$2"
            shift 2
            ;;
        --src-db)
            SRC_DB="$2"
            shift 2
            ;;
        --proc-env)
            PROC_ENV="$2"
            shift 2
            ;;
        --proc-db)
            PROC_DB="$2"
            shift 2
            ;;
        --dst-env)
            DST_ENV="$2"
            shift 2
            ;;
        --dst-db)
            DST_DB="$2"
            shift 2
            ;;
        --collection)
            COLLECTION="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --skip-backup-source)
            SKIP_BACKUP_SOURCE=true
            shift
            ;;
        --skip-backup-masked)
            SKIP_BACKUP_MASKED=true
            shift
            ;;
        --skip-restore-dest)
            SKIP_RESTORE_DEST=true
            shift
            ;;
        --skip-verification)
            SKIP_VERIFICATION=true
            shift
            ;;
        --verify-samples)
            VERIFY_SAMPLES="$2"
            shift 2
            ;;
        --no-email)
            ENABLE_EMAIL=false
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
if [ -z "$SRC_ENV" ] || [ -z "$SRC_DB" ] || [ -z "$PROC_ENV" ] || [ -z "$PROC_DB" ] || [ -z "$DST_ENV" ] || [ -z "$DST_DB" ] || [ -z "$COLLECTION" ]; then
    log_error "Missing required arguments"
    show_usage
    exit 1
fi

# Setup main log file
LOG_FILE="${LOG_DIR}/${TIMESTAMP}_orchestrate_${COLLECTION}.log"
exec > >(tee >(sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"))
exec 2>&1

# Header
echo "======================================================================"
echo "PHI Masking Orchestration"
echo "======================================================================"
log_info "Collection: $COLLECTION"
log_info "Source: $SRC_ENV / $SRC_DB"
log_info "Processing: $PROC_ENV / $PROC_DB"
log_info "Destination: $DST_ENV / $DST_DB"
log_info "Log file: $LOG_FILE"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Variables for tracking
BACKUP_SOURCE_DIR=""
BACKUP_MASKED_DIR=""
START_TIME=$(date +%s)

###############################################################################
# Step 0: Validate Collection Configuration (Pre-flight Check)
###############################################################################
if [ "$SKIP_VALIDATION" = false ]; then
    log_step "0" "Validate Collection Configuration"

    log_info "Running pre-flight validation for collection: $COLLECTION"

    # Run validation script in quiet mode (only shows errors/warnings)
    if python scripts/validate_collection.py --collection "$COLLECTION" --quiet; then
        log_success "Step 0 complete: Configuration validated successfully"
        log_info "  - Config file: config/config_rules/config_${COLLECTION}.json"
        log_info "  - Rules file: Validated and exists"
    else
        send_failure_and_exit "0" "Configuration validation" "Collection '$COLLECTION' has invalid configuration. Run: python scripts/validate_collection.py --collection $COLLECTION for details."
    fi
else
    log_warning "Step 0 skipped: Configuration validation"
fi

###############################################################################
# Step 1: Backup Source Data
###############################################################################
if [ "$SKIP_BACKUP_SOURCE" = false ]; then
    log_step "1" "Backup Source Data from $SRC_ENV"

    if bash scripts/backup_collection.sh \
        --env "$SRC_ENV" \
        --db "$SRC_DB" \
        --collection "$COLLECTION" \
        --compress; then

        # Find the latest backup directory
        BACKUP_SOURCE_DIR=$(find backup -maxdepth 1 -type d -name "*_${SRC_DB}_${COLLECTION}" | sort -r | head -n 1)
        log_success "Step 1 complete: Backup created at $BACKUP_SOURCE_DIR"
    else
        send_failure_and_exit "1" "Backup of source data" "Failed to create backup from $SRC_ENV/$SRC_DB/$COLLECTION"
    fi
else
    log_warning "Step 1 skipped: Source backup"
    # Find the latest existing backup
    BACKUP_SOURCE_DIR=$(find backup -maxdepth 1 -type d -name "*_${SRC_DB}_${COLLECTION}" | sort -r | head -n 1)
    if [ -z "$BACKUP_SOURCE_DIR" ]; then
        send_failure_and_exit "1" "Find existing backup" "No existing backup found for ${SRC_DB}_${COLLECTION}"
    fi
    log_info "Using existing backup: $BACKUP_SOURCE_DIR"
fi

###############################################################################
# Step 2: Restore to Processing Environment
###############################################################################
log_step "2" "Restore to Processing Environment ($PROC_ENV)"

if echo "y" | bash scripts/restore_collection.sh \
    --env "$PROC_ENV" \
    --db "$PROC_DB" \
    --backup-dir "$BACKUP_SOURCE_DIR" \
    --drop; then

    log_success "Step 2 complete: Data restored to $PROC_ENV / $PROC_DB"
else
    send_failure_and_exit "2" "Restore to processing environment" "Failed to restore backup to $PROC_ENV/$PROC_DB from $BACKUP_SOURCE_DIR"
fi

###############################################################################
# Step 3: Mask Data In-Situ
###############################################################################
log_step "3" "Mask Data on $PROC_ENV (In-Situ)"

CONFIG_FILE="config/config_rules/config_${COLLECTION}.json"

if [ ! -f "$CONFIG_FILE" ]; then
    send_failure_and_exit "3" "Configuration validation" "Config file not found: $CONFIG_FILE"
fi

if python masking.py \
    --config "$CONFIG_FILE" \
    --collection "$COLLECTION" \
    --src-env "$PROC_ENV" \
    --dst-env "$PROC_ENV" \
    --src-db "$PROC_DB" \
    --dst-db "$PROC_DB" \
    --in-situ; then

    log_success "Step 3 complete: Data masked on $PROC_ENV"
else
    send_failure_and_exit "3" "Mask data in-situ" "Masking failed on $PROC_ENV/$PROC_DB/$COLLECTION. Check masking.py logs for details."
fi

###############################################################################
# Step 4: Backup Masked Data
###############################################################################
if [ "$SKIP_BACKUP_MASKED" = false ]; then
    log_step "4" "Backup Masked Data from $PROC_ENV"

    if bash scripts/backup_collection.sh \
        --env "$PROC_ENV" \
        --db "$PROC_DB" \
        --collection "$COLLECTION" \
        --compress; then

        # Find the latest backup directory
        BACKUP_MASKED_DIR=$(find backup -maxdepth 1 -type d -name "*_${PROC_DB}_${COLLECTION}" | sort -r | head -n 1)
        log_success "Step 4 complete: Masked backup created at $BACKUP_MASKED_DIR"
    else
        send_failure_and_exit "4" "Backup masked data" "Failed to create backup of masked data from $PROC_ENV/$PROC_DB/$COLLECTION"
    fi
else
    log_warning "Step 4 skipped: Masked data backup"
fi

###############################################################################
# Step 5: Restore Masked Data to Destination
###############################################################################
if [ "$SKIP_RESTORE_DEST" = false ]; then
    # Auto-skip if masked backup was skipped
    if [ "$SKIP_BACKUP_MASKED" = true ]; then
        log_warning "Step 5 auto-skipped: Masked backup was skipped (no backup to restore)"
        SKIP_RESTORE_DEST=true
    else
        log_step "5" "Restore Masked Data to Destination ($DST_ENV)"

        if [ -z "$BACKUP_MASKED_DIR" ]; then
            send_failure_and_exit "5" "Validate masked backup" "No masked backup directory available for restore"
        fi

        if echo "y" | bash scripts/restore_collection.sh \
            --env "$DST_ENV" \
            --db "$DST_DB" \
            --backup-dir "$BACKUP_MASKED_DIR" \
            --drop; then

            log_success "Step 5 complete: Masked data restored to $DST_ENV / $DST_DB"
        else
            send_failure_and_exit "5" "Restore to destination" "Failed to restore masked backup to $DST_ENV/$DST_DB from $BACKUP_MASKED_DIR"
        fi
    fi
else
    log_warning "Step 5 skipped: Restore to destination"
fi

###############################################################################
# Step 6: Verify Masking Results
###############################################################################
if [ "$SKIP_VERIFICATION" = false ]; then
    log_step "6" "Verify Masking Results"

    # Determine verification targets based on whether Step 5 ran
    if [ "$SKIP_RESTORE_DEST" = false ]; then
        # Normal case: verify source vs destination
        VERIFY_DST_ENV="$DST_ENV"
        VERIFY_DST_DB="$DST_DB"
        log_info "Verifying: $SRC_ENV/$SRC_DB vs $DST_ENV/$DST_DB"
    else
        # Step 5 was skipped: verify source vs processing environment
        VERIFY_DST_ENV="$PROC_ENV"
        VERIFY_DST_DB="$PROC_DB"
        log_info "Verifying: $SRC_ENV/$SRC_DB vs $PROC_ENV/$PROC_DB (Step 5 was skipped)"
    fi

    if python scripts/verify_masking.py \
        --src-env "$SRC_ENV" \
        --dst-env "$VERIFY_DST_ENV" \
        --src-db "$SRC_DB" \
        --dst-db "$VERIFY_DST_DB" \
        --collection "$COLLECTION" \
        --sample-size "$VERIFY_SAMPLES"; then

        log_success "Step 6 complete: Verification passed"
    else
        send_failure_and_exit "6" "Verify masking results" "Verification failed between $SRC_ENV/$SRC_DB and $VERIFY_DST_ENV/$VERIFY_DST_DB. Check verification logs for details."
    fi
else
    log_warning "Step 6 skipped: Verification"
fi

###############################################################################
# Summary
###############################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "======================================================================"
echo "Orchestration Complete!"
echo "======================================================================"
log_info "Collection: $COLLECTION"
log_info "Total duration: ${MINUTES}m ${SECONDS}s"
echo ""
log_info "Artifacts created:"
[ ! -z "$BACKUP_SOURCE_DIR" ] && log_info "  - Source backup: $BACKUP_SOURCE_DIR"
[ ! -z "$BACKUP_MASKED_DIR" ] && log_info "  - Masked backup: $BACKUP_MASKED_DIR"
log_info "  - Log file: $LOG_FILE"
echo ""
log_success "All steps completed successfully!"
echo "======================================================================"

# Send success notification email
ARTIFACTS_LIST=""
[ ! -z "$BACKUP_SOURCE_DIR" ] && ARTIFACTS_LIST="Source backup: $BACKUP_SOURCE_DIR"
[ ! -z "$BACKUP_MASKED_DIR" ] && ARTIFACTS_LIST="$ARTIFACTS_LIST,Masked backup: $BACKUP_MASKED_DIR"
ARTIFACTS_LIST="$ARTIFACTS_LIST,Log file: $LOG_FILE"

send_notification success \
    --collection "$COLLECTION" \
    --duration "${MINUTES}m ${SECONDS}s" \
    --src-env "$SRC_ENV" \
    --proc-env "$PROC_ENV" \
    --dst-env "$DST_ENV" \
    --artifacts "$ARTIFACTS_LIST" \
    --log-file "$LOG_FILE"
