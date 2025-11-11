#!/usr/bin/env bash
# mongoexport.sh - Enhanced MongoDB export wrapper
# Provides robust export functionality with query filtering and multiple formats

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
EXPORT_FORMAT="json"
PRETTY_PRINT=false
DRY_RUN=false
VERBOSE=false
QUIET=false

#######################################
# Show help message
#######################################
show_help() {
    cat <<EOF
MongoDB Export Wrapper - Enhanced export with query filtering

Usage: $(basename "$0") [OPTIONS]

Required Options:
  --db DATABASE            Database name
  --collection NAME        Collection name to export

Output Options:
  --output FILE            Output file (default: auto-generated)
  --type FORMAT            Export format: json or csv (default: json)
  --fields FIELDS          Fields to export (comma-separated, required for CSV)
  --pretty                 Pretty-print JSON output

Query Options:
  --query JSON             Query filter (e.g., '{"status": "active"}')
  --sort JSON              Sort specification (e.g., '{"date": -1}')
  --limit N                Limit number of documents
  --skip N                 Skip N documents

Operation Options:
  --dry-run                Show what would be exported without doing it
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
  # Export entire collection to JSON
  $(basename "$0") --db MyDB --collection Users --output users.json

  # Export to CSV with specific fields
  $(basename "$0") --db MyDB --collection Users --type csv --fields "name,email,created"

  # Export with query filter
  $(basename "$0") --db MyDB --collection Orders --query '{"status": "pending"}'

  # Export with sort and limit
  $(basename "$0") --db MyDB --collection Logs --sort '{"timestamp": -1}' --limit 1000

EOF
}

#######################################
# Show version
#######################################
show_version() {
    echo "mongoexport wrapper version $VERSION"
}

#######################################
# Parse export-specific arguments
#######################################
parse_export_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --type|--format)
                EXPORT_FORMAT="$2"
                shift 2
                ;;
            --fields)
                EXPORT_FIELDS="$2"
                shift 2
                ;;
            --pretty)
                PRETTY_PRINT=true
                shift
                ;;
            --query)
                QUERY="$2"
                shift 2
                ;;
            --sort)
                SORT="$2"
                shift 2
                ;;
            --limit)
                LIMIT="$2"
                shift 2
                ;;
            --skip)
                SKIP="$2"
                shift 2
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
# Validate export parameters
#######################################
validate_export_params() {
    # Database and collection are required
    require_var MONGO_DB "Database name is required (--db)"
    require_var MONGO_COLLECTION "Collection name is required (--collection)"

    # Validate export format
    if [[ "$EXPORT_FORMAT" != "json" && "$EXPORT_FORMAT" != "csv" ]]; then
        log_error "Invalid export format: $EXPORT_FORMAT (must be json or csv)"
        exit "$EXIT_INVALID_ARGS"
    fi

    # CSV requires fields
    if [[ "$EXPORT_FORMAT" == "csv" && -z "${EXPORT_FIELDS:-}" ]]; then
        log_error "CSV export requires --fields parameter"
        exit "$EXIT_INVALID_ARGS"
    fi

    # Validate JSON if provided
    if [[ -n "${QUERY:-}" ]]; then
        if command_exists jq; then
            if ! echo "$QUERY" | jq empty 2>/dev/null; then
                log_error "Invalid JSON in query: $QUERY"
                exit "$EXIT_INVALID_ARGS"
            fi
        fi
    fi

    if [[ -n "${SORT:-}" ]]; then
        if command_exists jq; then
            if ! echo "$SORT" | jq empty 2>/dev/null; then
                log_error "Invalid JSON in sort: $SORT"
                exit "$EXIT_INVALID_ARGS"
            fi
        fi
    fi
}

#######################################
# Build mongoexport command
# Outputs:
#   Complete mongoexport command
#######################################
build_export_command() {
    local cmd="mongoexport"

    # Connection
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"
    cmd="$cmd --uri=\"$mongo_uri\""

    # Database and collection
    cmd="$cmd --db=\"$MONGO_DB\""
    cmd="$cmd --collection=\"$MONGO_COLLECTION\""

    # Output file
    local output_file="${OUTPUT_FILE:-}"
    if [[ -z "$output_file" ]]; then
        output_file="$(generate_export_filename "$MONGO_DB" "$MONGO_COLLECTION" "$EXPORT_FORMAT")"
    fi

    cmd="$cmd --out=\"$output_file\""

    # Export format
    cmd="$cmd --type=$EXPORT_FORMAT"

    # Fields (for CSV)
    if [[ -n "${EXPORT_FIELDS:-}" ]]; then
        cmd="$cmd --fields=\"$EXPORT_FIELDS\""
    fi

    # Pretty print (for JSON)
    if [[ "$PRETTY_PRINT" == "true" && "$EXPORT_FORMAT" == "json" ]]; then
        cmd="$cmd --jsonArray --pretty"
    fi

    # Query filter
    if [[ -n "${QUERY:-}" ]]; then
        cmd="$cmd --query='$QUERY'"
    fi

    # Sort
    if [[ -n "${SORT:-}" ]]; then
        cmd="$cmd --sort='$SORT'"
    fi

    # Limit
    if [[ -n "${LIMIT:-}" ]]; then
        cmd="$cmd --limit=$LIMIT"
    fi

    # Skip
    if [[ -n "${SKIP:-}" ]]; then
        cmd="$cmd --skip=$SKIP"
    fi

    echo "$cmd"
}

#######################################
# Execute export operation
#######################################
execute_export() {
    local cmd
    cmd="$(build_export_command)"

    # Extract output file from command
    local output_file
    output_file=$(echo "$cmd" | grep -o -- '--out="[^"]*"' | sed 's/--out="\(.*\)"/\1/')

    log_debug "Executing: $cmd"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_section "Dry Run - Command to be executed"
        log_info "$cmd"
        log_info "Output file: $output_file"
        return 0
    fi

    # Execute mongoexport
    local exit_code=0
    local doc_count=0

    eval "$cmd" 2>&1 | while IFS= read -r line; do
        # Parse mongoexport output
        if [[ "$line" =~ error|Error|ERROR ]]; then
            log_error "$line"
        elif [[ "$line" =~ warning|Warning|WARN ]]; then
            log_warn "$line"
        elif [[ "$line" =~ exported\ ([0-9]+)\ record ]]; then
            # Extract document count
            doc_count=$(echo "$line" | grep -o '[0-9]\+')
            log_info "$line"
        elif [[ "$VERBOSE" == "true" ]]; then
            log_debug "$line"
        fi
    done || exit_code=$?

    # Check if output file was created
    if [[ -f "$output_file" ]]; then
        local file_size
        file_size="$(get_file_size "$output_file")"
        log_info "Created: $output_file ($file_size)"
    else
        log_error "Output file was not created: $output_file"
        exit_code=1
    fi

    return $exit_code
}

#######################################
# Main export function
#######################################
main() {
    log_section "MongoDB Export - Starting"

    # Check prerequisites
    require_command mongoexport "mongoexport is required. Install MongoDB Database Tools."

    # Load default configuration
    load_default_config

    # Parse command-line arguments
    parse_export_args "$@"

    # Validate parameters
    validate_export_params

    # Build MongoDB URI
    local mongo_uri
    mongo_uri="$(build_mongo_uri)"

    # Validate MongoDB URI
    if ! validate_mongo_uri "$mongo_uri"; then
        exit "$EXIT_INVALID_ARGS"
    fi

    # Log export details
    log_info "Connection: $(sanitize_uri "$mongo_uri")"
    log_info "Database: $MONGO_DB"
    log_info "Collection: $MONGO_COLLECTION"
    log_info "Format: $EXPORT_FORMAT"

    if [[ -n "${QUERY:-}" ]]; then
        log_info "Query: $QUERY"
    fi

    if [[ -n "${SORT:-}" ]]; then
        log_info "Sort: $SORT"
    fi

    if [[ -n "${LIMIT:-}" ]]; then
        log_info "Limit: $LIMIT"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry-run mode: No actual export will be performed"
    fi

    # Execute export
    log_section "Executing Export"

    local start_time
    start_time=$(date +%s)

    if execute_export; then
        local end_time duration
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        log_section "Export Summary"
        log_success "Export completed successfully!"
        log_info "Duration: ${duration}s"
    else
        local exit_code=$?
        log_section "Export Summary"
        log_error "Export failed with exit code: $exit_code"
        exit "$EXIT_OPERATION_FAILED"
    fi
}

# Run main function
main "$@"
