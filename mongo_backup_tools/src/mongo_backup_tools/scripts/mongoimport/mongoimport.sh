#!/usr/bin/env bash
# mongoimport.sh - Enhanced MongoDB import wrapper
# Provides robust import functionality with upsert and validation

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBS_DIR="$(cd "$SCRIPT_DIR/../libs" && pwd)"

# Source libraries
# shellcheck source=../libs/logging.sh
source "$LIBS_DIR/logging.sh"
# shellcheck source=../libs/error_handling.sh
source "$LIBS_DIR/error_handling.sh"
# shellcheck source=../libs/config_parser.sh
source "$LIBS_DIR/config_parser.sh"
# shellcheck source=../libs/filename_utils.sh
source "$LIBS_DIR/filename_utils.sh"

# Script version
readonly VERSION="1.0.0"

# Default values
IMPORT_FORMAT="json"
IMPORT_MODE="insert"
DROP_EXISTING=false
STOP_ON_ERROR=true
DRY_RUN=false
VERBOSE=false
QUIET=false

#######################################
# Show help message
#######################################
show_help() {
    cat <<EOF
MongoDB Import Wrapper - Enhanced import with upsert modes

Usage: $(basename "$0") [OPTIONS]

Required Options:
  --db DATABASE            Database name
  --collection NAME        Collection name to import into
  --file FILE              Input file to import

Input Options:
  --type FORMAT            Import format: json or csv (default: json)
  --fields FIELDS          Field names (comma-separated, required for CSV)
  --headerline             Use first line as field names (CSV only)
  --jsonArray              Input is JSON array

Import Options:
  --mode MODE              Import mode: insert, upsert, or merge (default: insert)
  --upsertFields FIELDS    Fields to use for upsert matching (comma-separated)
  --drop                   Drop collection before importing
  --stopOnError            Stop on first error (default: true)
  --ignoreBlanks           Ignore blank fields in CSV

Operation Options:
  --dry-run                Validate file without importing
  -v, --verbose            Enable verbose logging
  -q, --quiet              Suppress all output except errors

Connection Options:
  --uri URI                MongoDB connection string
  --host HOST              MongoDB host (default: localhost)
  --port PORT              MongoDB port (default: 27017)
  -u, --username USER      Authentication username
  -p, --password PASS      Authentication password
  --authdb DATABASE        Authentication database (default: admin)

Other:
  -h, --help               Show this help message
  --version                Show version information

Examples:
  # Import JSON file
  $(basename "$0") --db MyDB --collection Users --file users.json

  # Import CSV with headers
  $(basename "$0") --db MyDB --collection Users --file users.csv --type csv --headerline

  # Import with upsert on email field
  $(basename "$0") --db MyDB --collection Users --file users.json --mode upsert --upsertFields email

  # Drop and import
  $(basename "$0") --db MyDB --collection Users --file users.json --drop

EOF
}

#######################################
# Show version
#######################################
show_version() {
    echo "mongoimport wrapper version $VERSION"
}

#######################################
# Parse import-specific arguments
#######################################
parse_import_args() {
    local remaining_args=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --file)
                INPUT_FILE="$2"
                shift 2
                ;;
            --type|--format)
                IMPORT_FORMAT="$2"
                shift 2
                ;;
            --fields)
                IMPORT_FIELDS="$2"
                shift 2
                ;;
            --headerline)
                HEADERLINE=true
                shift
                ;;
            --jsonArray)
                JSON_ARRAY=true
                shift
                ;;
            --mode)
                IMPORT_MODE="$2"
                shift 2
                ;;
            --upsertFields)
                UPSERT_FIELDS="$2"
                shift 2
                ;;
            --drop)
                DROP_EXISTING=true
                shift
                ;;
            --stopOnError)
                STOP_ON_ERROR=true
                shift
                ;;
            --ignoreBlanks)
                IGNORE_BLANKS=true
                shift
                ;;
            --version)
                show_version
                exit 0
                ;;
            *)
                # Save unrecognized arguments for config_parser
                remaining_args+=("$1")
                # If this looks like an option with a value, save both
                if [[ "$1" == --* ]] && [[ $# -gt 1 ]] && [[ "$2" != --* ]]; then
                    remaining_args+=("$2")
                    shift 2
                else
                    shift
                fi
                ;;
        esac
    done

    # Parse remaining arguments with common parser
    parse_args "${remaining_args[@]}"
}

#######################################
# Validate import parameters
#######################################
validate_import_params() {
    # Required parameters
    require_var MONGO_DB "Database name is required (--db)"
    require_var MONGO_COLLECTION "Collection name is required (--collection)"
    require_var INPUT_FILE "Input file is required (--file)"

    # Validate input file exists
    require_file "$INPUT_FILE" "Input file not found: $INPUT_FILE"

    # Validate import format
    if [[ "$IMPORT_FORMAT" != "json" && "$IMPORT_FORMAT" != "csv" ]]; then
        log_error "Invalid import format: $IMPORT_FORMAT (must be json or csv)"
        exit "$EXIT_INVALID_ARGS"
    fi

    # CSV requirements
    if [[ "$IMPORT_FORMAT" == "csv" ]]; then
        if [[ -z "${IMPORT_FIELDS:-}" && "${HEADERLINE:-false}" != "true" ]]; then
            log_error "CSV import requires either --fields or --headerline"
            exit "$EXIT_INVALID_ARGS"
        fi
    fi

    # Validate import mode
    case "$IMPORT_MODE" in
        insert|upsert|merge)
            ;;
        *)
            log_error "Invalid import mode: $IMPORT_MODE (must be insert, upsert, or merge)"
            exit "$EXIT_INVALID_ARGS"
            ;;
    esac

    # Upsert mode requires upsert fields
    if [[ "$IMPORT_MODE" == "upsert" && -z "${UPSERT_FIELDS:-}" ]]; then
        log_error "Upsert mode requires --upsertFields parameter"
        exit "$EXIT_INVALID_ARGS"
    fi
}

#######################################
# Count documents in input file
# Arguments:
#   $1 - File path
#   $2 - Format (json/csv)
# Outputs:
#   Document count
#######################################
count_documents() {
    local file="$1"
    local format="$2"

    case "$format" in
        json)
            if command_exists jq; then
                if [[ "${JSON_ARRAY:-false}" == "true" ]]; then
                    jq 'length' "$file" 2>/dev/null || echo "unknown"
                else
                    grep -c '^{' "$file" 2>/dev/null || echo "unknown"
                fi
            else
                grep -c '^{' "$file" 2>/dev/null || echo "unknown"
            fi
            ;;
        csv)
            local count
            count=$(wc -l < "$file" | tr -d ' ')
            if [[ "${HEADERLINE:-false}" == "true" ]]; then
                echo $((count - 1))
            else
                echo "$count"
            fi
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

#######################################
# Build mongoimport command
# Outputs:
#   Complete mongoimport command
#######################################
build_import_command() {
    local cmd="mongoimport"

    # Connection
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"
    cmd="$cmd --uri=\"$mongo_uri\""

    # Database and collection
    cmd="$cmd --db=\"$MONGO_DB\""
    cmd="$cmd --collection=\"$MONGO_COLLECTION\""

    # Input file
    cmd="$cmd --file=\"$INPUT_FILE\""

    # Import format
    cmd="$cmd --type=$IMPORT_FORMAT"

    # Fields (for CSV)
    if [[ -n "${IMPORT_FIELDS:-}" ]]; then
        cmd="$cmd --fields=\"$IMPORT_FIELDS\""
    fi

    # Headerline (for CSV)
    if [[ "${HEADERLINE:-false}" == "true" ]]; then
        cmd="$cmd --headerline"
    fi

    # JSON array
    if [[ "${JSON_ARRAY:-false}" == "true" ]]; then
        cmd="$cmd --jsonArray"
    fi

    # Import mode
    case "$IMPORT_MODE" in
        upsert)
            cmd="$cmd --mode=upsert"
            if [[ -n "${UPSERT_FIELDS:-}" ]]; then
                cmd="$cmd --upsertFields=\"$UPSERT_FIELDS\""
            fi
            ;;
        merge)
            cmd="$cmd --mode=merge"
            ;;
        insert)
            # Default mode
            ;;
    esac

    # Drop collection
    if [[ "$DROP_EXISTING" == "true" ]]; then
        cmd="$cmd --drop"
    fi

    # Stop on error
    if [[ "$STOP_ON_ERROR" == "true" ]]; then
        cmd="$cmd --stopOnError"
    fi

    # Ignore blanks
    if [[ "${IGNORE_BLANKS:-false}" == "true" ]]; then
        cmd="$cmd --ignoreBlanks"
    fi

    echo "$cmd"
}

#######################################
# Execute import operation
#######################################
execute_import() {
    local cmd
    cmd="$(build_import_command)"

    log_debug "Executing: $cmd"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_section "Dry Run - Command to be executed"
        log_info "$cmd"

        # Validate file can be read
        if [[ -r "$INPUT_FILE" ]]; then
            log_success "Input file is readable"

            local doc_count
            doc_count=$(count_documents "$INPUT_FILE" "$IMPORT_FORMAT")
            log_info "Documents to import: $doc_count"
        else
            log_error "Input file is not readable"
            return 1
        fi

        return 0
    fi

    # Execute mongoimport
    local exit_code=0
    local imported_count=0

    eval "$cmd" 2>&1 | while IFS= read -r line; do
        # Parse mongoimport output
        if [[ "$line" =~ error|Error|ERROR ]]; then
            log_error "$line"
        elif [[ "$line" =~ warning|Warning|WARN ]]; then
            log_warn "$line"
        elif [[ "$line" =~ imported\ ([0-9]+)\ document ]]; then
            # Extract document count
            imported_count=$(echo "$line" | grep -o '[0-9]\+' | head -1)
            log_info "$line"
        elif [[ "$VERBOSE" == "true" ]]; then
            log_debug "$line"
        fi
    done || exit_code=$?

    return $exit_code
}

#######################################
# Main import function
#######################################
main() {
    log_section "MongoDB Import - Starting"

    # Check prerequisites
    require_command mongoimport "mongoimport is required. Install MongoDB Database Tools."

    # Load default configuration
    load_default_config

    # Parse command-line arguments
    parse_import_args "$@"

    # Validate parameters
    validate_import_params

    # Build MongoDB URI
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"

    # Validate MongoDB URI
    if ! validate_mongo_uri "$mongo_uri"; then
        exit "$EXIT_INVALID_ARGS"
    fi

    # Log import details
    log_info "Connection: $(sanitize_uri "$mongo_uri")"
    log_info "Database: $MONGO_DB"
    log_info "Collection: $MONGO_COLLECTION"

    local file_size
    file_size="$(get_file_size "$INPUT_FILE")"
    log_info "Input file: $INPUT_FILE ($file_size)"
    log_info "Format: $IMPORT_FORMAT"
    log_info "Mode: $IMPORT_MODE"

    if [[ "$DROP_EXISTING" == "true" ]]; then
        log_warn "Drop mode: Collection will be dropped before import"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry-run mode: Validating without importing"
    fi

    # Execute import
    log_section "Executing Import"

    local start_time
    start_time=$(date +%s)

    if execute_import; then
        local end_time duration
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        log_section "Import Summary"
        log_success "Import completed successfully!"
        log_info "Duration: ${duration}s"
    else
        local exit_code=$?
        log_section "Import Summary"
        log_error "Import failed with exit code: $exit_code"
        exit "$EXIT_OPERATION_FAILED"
    fi
}

# Run main function
main "$@"
