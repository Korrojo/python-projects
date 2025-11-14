#!/usr/bin/env bash
# mongodump.sh - Enhanced MongoDB dump wrapper with resume capability
# Provides robust backup functionality with state tracking and error handling

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBS_DIR="$(cd "$SCRIPT_DIR/../libs" && pwd)"

# Source libraries
# shellcheck source=../libs/logging.sh
source "$LIBS_DIR/logging.sh"
# shellcheck source=../libs/error_handling.sh
source "$LIBS_DIR/error_handling.sh"
# shellcheck source=../libs/state_tracking.sh
source "$LIBS_DIR/state_tracking.sh"
# shellcheck source=../libs/config_parser.sh
source "$LIBS_DIR/config_parser.sh"
# shellcheck source=../libs/filename_utils.sh
source "$LIBS_DIR/filename_utils.sh"

# Script version
readonly VERSION="1.0.0"

# Default values
PARALLEL_JOBS=4
USE_GZIP=true
DRY_RUN=false
RESUME=false
VERBOSE=false
QUIET=false

#######################################
# Show help message
#######################################
show_help() {
    cat <<EOF
MongoDB Dump Wrapper - Enhanced backup with resume capability

Usage: $(basename "$0") [OPTIONS]

Required Options:
  --uri URI                MongoDB connection string
  --db DATABASE            Database name to backup

Output Options:
  --output DIR             Output directory for backups (default: ./backups)
  --archive FILE           Create a single archive file instead of directory

Backup Options:
  --collection NAME        Backup specific collection (can be specified multiple times)
  --query JSON             Filter documents with query
  --gzip                   Compress output with gzip (default: enabled)
  --no-gzip                Disable gzip compression
  -j, --parallel N         Number of parallel collections (default: 4)

Operation Options:
  --resume                 Resume from previous interrupted backup
  --dry-run                Show what would be backed up without doing it
  -v, --verbose            Enable verbose logging
  -q, --quiet              Suppress all output except errors

Connection Options:
  --host HOST              MongoDB host (default: localhost)
  --port PORT              MongoDB port (default: 27017)
  -u, --username USER      Authentication username
  -p, --password PASS      Authentication password
  --authdb DATABASE        Authentication database (default: admin)

Other:
  -h, --help               Show this help message
  --version                Show version information

Examples:
  # Backup entire database
  $(basename "$0") --uri mongodb://localhost:27017 --db MyDB --output /backups

  # Backup specific collections with compression
  $(basename "$0") --db MyDB --collection Users --collection Orders --gzip

  # Resume interrupted backup
  $(basename "$0") --db MyDB --resume

  # Backup with query filter
  $(basename "$0") --db MyDB --collection Users --query '{"active": true}'

EOF
}

#######################################
# Show version
#######################################
show_version() {
    echo "mongodump wrapper version $VERSION"
}

#######################################
# Get list of collections in database
# Arguments:
#   $1 - MongoDB URI
#   $2 - Database name
# Outputs:
#   List of collection names
#######################################
get_collections() {
    local uri="$1"
    local db="$2"

    log_debug "Getting collections for database: $db"

    if ! command_exists mongosh && ! command_exists mongo; then
        log_error "Neither mongosh nor mongo CLI found"
        return 1
    fi

    local mongo_cmd
    if command_exists mongosh; then
        mongo_cmd="mongosh"
    else
        mongo_cmd="mongo"
    fi

    # Get collection names
    $mongo_cmd "$uri/$db" --quiet --eval "db.getCollectionNames().join('\n')" 2>/dev/null || {
        log_error "Failed to list collections"
        return 1
    }
}

#######################################
# Backup single collection
# Arguments:
#   $1 - MongoDB URI
#   $2 - Database name
#   $3 - Collection name
#   $4 - Output directory
#######################################
backup_collection() {
    local uri="$1"
    local db="$2"
    local collection="$3"
    local output_dir="$4"

    # Check if already completed (for resume functionality)
    if [[ "$RESUME" == "true" ]] && is_item_completed "${db}.${collection}"; then
        log_info "Skipping already backed up collection: ${db}.${collection}"
        return 0
    fi

    log_info "Backing up collection: ${db}.${collection}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would backup: ${db}.${collection}"
        add_completed_item "${db}.${collection}"
        return 0
    fi

    # Build mongodump command
    local cmd="mongodump"
    cmd="$cmd --uri=\"$uri\""
    cmd="$cmd --db=\"$db\""
    cmd="$cmd --collection=\"$collection\""
    cmd="$cmd --out=\"$output_dir\""

    if [[ "$USE_GZIP" == "true" ]]; then
        cmd="$cmd --gzip"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    fi

    # Add query filter if specified
    if [[ -n "${QUERY:-}" ]]; then
        cmd="$cmd --query='$QUERY'"
    fi

    # Add authentication mechanism if specified
    if [[ -n "${AUTH_MECHANISM:-}" ]]; then
        cmd="$cmd --authenticationMechanism=\"$AUTH_MECHANISM\""
    fi

    # Add TLS/SSL options
    if [[ "${USE_TLS:-false}" == "true" ]]; then
        cmd="$cmd --tls"
    fi

    if [[ -n "${TLS_CERT_KEY_FILE:-}" ]]; then
        cmd="$cmd --tlsCertificateKeyFile=\"$TLS_CERT_KEY_FILE\""
    fi

    if [[ -n "${TLS_CA_FILE:-}" ]]; then
        cmd="$cmd --tlsCAFile=\"$TLS_CA_FILE\""
    fi

    if [[ -n "${TLS_CERT_KEY_PASSWORD:-}" ]]; then
        cmd="$cmd --tlsCertificateKeyFilePassword=\"$TLS_CERT_KEY_PASSWORD\""
    fi

    if [[ "${TLS_ALLOW_INVALID_CERTS:-false}" == "true" ]]; then
        cmd="$cmd --tlsAllowInvalidCertificates"
    fi

    if [[ "${TLS_ALLOW_INVALID_HOSTNAMES:-false}" == "true" ]]; then
        cmd="$cmd --tlsAllowInvalidHostnames"
    fi

    # Add connection options
    if [[ -n "${READ_PREFERENCE:-}" ]]; then
        cmd="$cmd --readPreference=\"$READ_PREFERENCE\""
    fi

    if [[ -n "${REPLICA_SET_NAME:-}" ]]; then
        cmd="$cmd --replicaSet=\"$REPLICA_SET_NAME\""
    fi

    if [[ -n "${CONNECT_TIMEOUT:-}" ]]; then
        cmd="$cmd --dial-timeout=\"${CONNECT_TIMEOUT}ms\""
    fi

    if [[ -n "${SOCKET_TIMEOUT:-}" ]]; then
        cmd="$cmd --socket-timeout=\"${SOCKET_TIMEOUT}ms\""
    fi

    # Execute mongodump
    log_debug "Executing: $cmd"

    if eval "$cmd" 2>&1 | while IFS= read -r line; do
        log_debug "$line"
    done; then
        add_completed_item "${db}.${collection}"
        log_success "Successfully backed up: ${db}.${collection}"
        return 0
    else
        local exit_code=$?
        add_failed_item "${db}.${collection}" "mongodump failed with exit code $exit_code"
        log_error "Failed to backup: ${db}.${collection}"
        return 1
    fi
}

#######################################
# Main backup function
#######################################
main() {
    log_section "MongoDB Backup - Starting"

    # Check prerequisites
    require_command mongodump "mongodump is required. Install MongoDB Database Tools."

    # Load default configuration
    load_default_config

    # Parse command-line arguments
    parse_args "$@"

    # Validate required parameters
    if [[ -z "${MONGO_DB:-}" ]]; then
        log_error "Database name is required (--db)"
        show_help
        exit "$EXIT_INVALID_ARGS"
    fi

    # Build MongoDB URI
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"

    # Validate MongoDB URI
    if ! validate_mongo_uri "$mongo_uri"; then
        exit "$EXIT_INVALID_ARGS"
    fi

    # Set output directory
    OUTPUT_DIR="${OUTPUT_DIR:-./backups}"
    OUTPUT_DIR="$(get_absolute_path "$OUTPUT_DIR")"
    ensure_directory "$OUTPUT_DIR" || exit "$EXIT_GENERAL_ERROR"

    log_info "Database: $MONGO_DB"
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Connection: $(sanitize_uri "$mongo_uri")"

    # Initialize state tracking if resume is enabled
    if [[ "$RESUME" == "true" ]]; then
        STATE_FILE=$(init_state_tracking "dump" "${MONGO_DB}")
        log_info "State tracking enabled: $STATE_FILE"
    fi

    # Get collections to backup
    local collections=()
    if [[ -n "${MONGO_COLLECTION:-}" ]]; then
        # Specific collection(s) provided
        collections=("$MONGO_COLLECTION")
    else
        # Get all collections
        log_info "Getting list of collections..."
        mapfile -t collections < <(get_collections "$mongo_uri" "$MONGO_DB")

        if [[ ${#collections[@]} -eq 0 ]]; then
            log_error "No collections found in database: $MONGO_DB"
            exit "$EXIT_OPERATION_FAILED"
        fi

        log_info "Found ${#collections[@]} collections"
    fi

    # Backup collections
    local success_count=0
    local fail_count=0
    local total=${#collections[@]}

    log_section "Backing up collections"

    for i in "${!collections[@]}"; do
        local collection="${collections[$i]}"
        local current=$((i + 1))

        log_progress "$current" "$total" "Processing: $collection"

        if backup_collection "$mongo_uri" "$MONGO_DB" "$collection" "$OUTPUT_DIR"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done

    # Mark operation as complete if using state tracking
    if [[ "$RESUME" == "true" ]]; then
        if [[ $fail_count -eq 0 ]]; then
            complete_operation "completed"
        else
            complete_operation "completed_with_errors"
        fi
        print_state_summary
    fi

    # Print summary
    log_section "Backup Summary"
    log_info "Total collections: $total"
    log_success "Successfully backed up: $success_count"

    if [[ $fail_count -gt 0 ]]; then
        log_error "Failed: $fail_count"
        exit "$EXIT_OPERATION_FAILED"
    fi

    # Calculate backup size
    local backup_size
    backup_size="$(get_dir_size "$OUTPUT_DIR")"
    log_info "Total backup size: $backup_size"

    log_success "Backup completed successfully!"
}

# Run main function
main "$@"
