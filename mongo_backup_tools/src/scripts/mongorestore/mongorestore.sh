#!/usr/bin/env bash
# mongorestore.sh - Enhanced MongoDB restore wrapper with namespace remapping
# Provides robust restore functionality with dry-run and state tracking

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
DRY_RUN=false
DROP_EXISTING=false
RESTORE_INDEXES=true
VERBOSE=false
QUIET=false

#######################################
# Show help message
#######################################
show_help() {
    cat <<EOF
MongoDB Restore Wrapper - Enhanced restore with namespace remapping

Usage: $(basename "$0") [OPTIONS]

Required Options:
  --uri URI                MongoDB connection string

Input Options:
  --archive FILE           Restore from archive file
  --dir DIRECTORY          Restore from backup directory (default: ./backups)

Restore Options:
  --db DATABASE            Target database name
  --collection NAME        Target collection name (requires --db)
  --nsFrom "db.coll"       Source namespace (database.collection)
  --nsTo "db.coll"         Destination namespace (database.collection)
  --drop                   Drop each collection before restore
  --noIndexRestore         Don't restore indexes
  -j, --parallel N         Number of parallel collections (default: 4)

Operation Options:
  --dry-run                Show what would be restored without doing it
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
  # Restore entire database
  $(basename "$0") --uri mongodb://localhost:27017 --archive mydb_backup.gz

  # Restore with namespace remapping
  $(basename "$0") --archive backup.gz --nsFrom "ProdDB.*" --nsTo "DevDB.*"

  # Restore specific collection with drop
  $(basename "$0") --dir ./backups --db MyDB --collection Users --drop

  # Dry-run to see what would be restored
  $(basename "$0") --archive backup.gz --dry-run

EOF
}

#######################################
# Show version
#######################################
show_version() {
    echo "mongorestore wrapper version $VERSION"
}

#######################################
# Parse restore-specific arguments
#######################################
parse_restore_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --archive)
                ARCHIVE_FILE="$2"
                shift 2
                ;;
            --dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            --nsFrom)
                NS_FROM="$2"
                shift 2
                ;;
            --nsTo)
                NS_TO="$2"
                shift 2
                ;;
            --drop)
                DROP_EXISTING=true
                shift
                ;;
            --noIndexRestore)
                RESTORE_INDEXES=false
                shift
                ;;
            --version)
                show_version
                exit 0
                ;;
            *)
                # Let config_parser handle common arguments
                break
                ;;
        esac
    done

    # Parse remaining arguments with common parser
    parse_args "$@"
}

#######################################
# Validate restore parameters
#######################################
validate_restore_params() {
    # Need either archive or directory
    if [[ -z "${ARCHIVE_FILE:-}" && -z "${BACKUP_DIR:-}" ]]; then
        log_error "Either --archive or --dir must be specified"
        show_help
        exit "$EXIT_INVALID_ARGS"
    fi

    # Validate archive file exists
    if [[ -n "${ARCHIVE_FILE:-}" ]]; then
        require_file "$ARCHIVE_FILE" "Archive file not found: $ARCHIVE_FILE"
    fi

    # Validate backup directory exists
    if [[ -n "${BACKUP_DIR:-}" ]]; then
        require_dir "$BACKUP_DIR" "Backup directory not found: $BACKUP_DIR"
    fi

    # Validate namespace remapping
    if [[ -n "${NS_FROM:-}" && -z "${NS_TO:-}" ]]; then
        log_error "--nsTo is required when --nsFrom is specified"
        exit "$EXIT_INVALID_ARGS"
    fi

    if [[ -z "${NS_FROM:-}" && -n "${NS_TO:-}" ]]; then
        log_error "--nsFrom is required when --nsTo is specified"
        exit "$EXIT_INVALID_ARGS"
    fi
}

#######################################
# Build mongorestore command
# Outputs:
#   Complete mongorestore command
#######################################
build_restore_command() {
    local cmd="mongorestore"

    # Connection
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"
    cmd="$cmd --uri=\"$mongo_uri\""

    # Input source
    if [[ -n "${ARCHIVE_FILE:-}" ]]; then
        cmd="$cmd --archive=\"$ARCHIVE_FILE\""

        # Detect if archive is gzipped
        if is_compressed "$ARCHIVE_FILE"; then
            cmd="$cmd --gzip"
        fi
    elif [[ -n "${BACKUP_DIR:-}" ]]; then
        cmd="$cmd --dir=\"$BACKUP_DIR\""
    fi

    # Target database/collection
    if [[ -n "${MONGO_DB:-}" ]]; then
        cmd="$cmd --db=\"$MONGO_DB\""
    fi

    if [[ -n "${MONGO_COLLECTION:-}" ]]; then
        cmd="$cmd --collection=\"$MONGO_COLLECTION\""
    fi

    # Namespace remapping
    if [[ -n "${NS_FROM:-}" && -n "${NS_TO:-}" ]]; then
        cmd="$cmd --nsFrom=\"$NS_FROM\""
        cmd="$cmd --nsTo=\"$NS_TO\""
    fi

    # Options
    if [[ "$DROP_EXISTING" == "true" ]]; then
        cmd="$cmd --drop"
    fi

    if [[ "$RESTORE_INDEXES" == "false" ]]; then
        cmd="$cmd --noIndexRestore"
    fi

    if [[ "$PARALLEL_JOBS" -gt 1 ]]; then
        cmd="$cmd --numParallelCollections=$PARALLEL_JOBS"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        cmd="$cmd --dryRun"
    fi

    echo "$cmd"
}

#######################################
# Execute restore operation
#######################################
execute_restore() {
    local cmd
    cmd="$(build_restore_command)"

    log_debug "Executing: $cmd"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_section "Dry Run - Command to be executed"
        log_info "$cmd"
        return 0
    fi

    # Execute mongorestore
    local exit_code=0
    eval "$cmd" 2>&1 | while IFS= read -r line; do
        # Parse mongorestore output
        if [[ "$line" =~ error|Error|ERROR ]]; then
            log_error "$line"
            ((ERROR_COUNT++))
        elif [[ "$line" =~ warning|Warning|WARN ]]; then
            log_warn "$line"
            ((WARNING_COUNT++))
        elif [[ "$VERBOSE" == "true" ]]; then
            log_debug "$line"
        else
            # Log progress lines
            if [[ "$line" =~ [0-9]+\ document ]]; then
                log_info "$line"
            fi
        fi
    done || exit_code=$?

    return $exit_code
}

#######################################
# Main restore function
#######################################
main() {
    log_section "MongoDB Restore - Starting"

    # Check prerequisites
    require_command mongorestore "mongorestore is required. Install MongoDB Database Tools."

    # Load default configuration
    load_default_config

    # Parse command-line arguments
    parse_restore_args "$@"

    # Validate parameters
    validate_restore_params

    # Build MongoDB URI
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"

    # Validate MongoDB URI
    if ! validate_mongo_uri "$mongo_uri"; then
        exit "$EXIT_INVALID_ARGS"
    fi

    # Log restore details
    log_info "Connection: $(sanitize_uri "$mongo_uri")"

    if [[ -n "${ARCHIVE_FILE:-}" ]]; then
        local archive_size
        archive_size="$(get_file_size "$ARCHIVE_FILE")"
        log_info "Archive: $ARCHIVE_FILE ($archive_size)"
    fi

    if [[ -n "${BACKUP_DIR:-}" ]]; then
        local dir_size
        dir_size="$(get_dir_size "$BACKUP_DIR")"
        log_info "Backup directory: $BACKUP_DIR ($dir_size)"
    fi

    if [[ -n "${MONGO_DB:-}" ]]; then
        log_info "Target database: $MONGO_DB"
    fi

    if [[ -n "${MONGO_COLLECTION:-}" ]]; then
        log_info "Target collection: $MONGO_COLLECTION"
    fi

    if [[ -n "${NS_FROM:-}" ]]; then
        log_info "Namespace remapping: $NS_FROM -> $NS_TO"
    fi

    if [[ "$DROP_EXISTING" == "true" ]]; then
        log_warn "Drop mode: Collections will be dropped before restore"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry-run mode: No actual changes will be made"
    fi

    # Execute restore
    log_section "Executing Restore"

    local start_time
    start_time=$(date +%s)

    if execute_restore; then
        local end_time duration
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        log_section "Restore Summary"
        log_success "Restore completed successfully!"
        log_info "Duration: ${duration}s"

        print_error_summary
    else
        local exit_code=$?
        log_section "Restore Summary"
        log_error "Restore failed with exit code: $exit_code"

        print_error_summary

        exit "$EXIT_OPERATION_FAILED"
    fi
}

# Run main function
main "$@"
