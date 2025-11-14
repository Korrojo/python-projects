#!/usr/bin/env bash
# config_parser.sh - Configuration file parsing utilities
# Supports loading configuration from JSON and environment files

# Prevent multiple sourcing
[[ -n "${CONFIG_PARSER_SH_SOURCED:-}" ]] && return 0
readonly CONFIG_PARSER_SH_SOURCED=1

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./logging.sh
source "$SCRIPT_DIR/logging.sh"
# shellcheck source=./error_handling.sh
source "$SCRIPT_DIR/error_handling.sh"

# Configuration file paths
: "${CONFIG_DIR:="../../../../../../config"}"

#######################################
# Load configuration from JSON file
# Arguments:
#   $1 - Config file path
# Returns:
#   0 on success, 1 on failure
#######################################
load_config_file() {
    local config_file="$1"

    if [[ ! -f "$config_file" ]]; then
        log_warn "Config file not found: $config_file"
        return 1
    fi

    log_debug "Loading configuration from: $config_file"

    # Check if file is valid JSON
    if command_exists jq; then
        if ! jq empty "$config_file" 2>/dev/null; then
            log_error "Invalid JSON in config file: $config_file"
            return 1
        fi
    fi

    return 0
}

#######################################
# Get config value from JSON
# Arguments:
#   $1 - Config file path
#   $2 - JSON path (e.g., .database.host)
# Outputs:
#   Config value
#######################################
get_config_value() {
    local config_file="$1"
    local json_path="$2"

    if [[ ! -f "$config_file" ]]; then
        log_warn "Config file not found: $config_file"
        return 1
    fi

    if command_exists jq; then
        jq -r "$json_path" "$config_file" 2>/dev/null
    else
        log_warn "jq not available, cannot parse JSON config"
        return 1
    fi
}

#######################################
# Load environment variables from .env file
# Arguments:
#   $1 - .env file path
# Returns:
#   0 on success, 1 on failure
#######################################
load_env_file() {
    local env_file="$1"

    if [[ ! -f "$env_file" ]]; then
        log_warn "Environment file not found: $env_file"
        return 1
    fi

    log_debug "Loading environment from: $env_file"

    # Export variables from .env file
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$env_file" | grep -v '^$' | xargs)

    return 0
}

#######################################
# Parse command-line arguments
# Arguments:
#   $@ - Command-line arguments
# Sets global variables based on arguments
#######################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --host)
                MONGO_HOST="$2"
                shift 2
                ;;
            --port)
                MONGO_PORT="$2"
                shift 2
                ;;
            --username|-u)
                MONGO_USERNAME="$2"
                shift 2
                ;;
            --password|-p)
                MONGO_PASSWORD="$2"
                shift 2
                ;;
            --authdb|--auth-database)
                MONGO_AUTH_DB="$2"
                shift 2
                ;;
            --auth-mechanism)
                AUTH_MECHANISM="$2"
                shift 2
                ;;
            --tls|--ssl)
                USE_TLS=true
                shift
                ;;
            --tls-certificate-key-file)
                TLS_CERT_KEY_FILE="$2"
                shift 2
                ;;
            --tls-ca-file)
                TLS_CA_FILE="$2"
                shift 2
                ;;
            --tls-certificate-key-file-password)
                TLS_CERT_KEY_PASSWORD="$2"
                shift 2
                ;;
            --tls-allow-invalid-certificates)
                TLS_ALLOW_INVALID_CERTS=true
                shift
                ;;
            --tls-allow-invalid-hostnames)
                TLS_ALLOW_INVALID_HOSTNAMES=true
                shift
                ;;
            --read-preference)
                READ_PREFERENCE="$2"
                shift 2
                ;;
            --replica-set-name)
                REPLICA_SET_NAME="$2"
                shift 2
                ;;
            --connect-timeout)
                CONNECT_TIMEOUT="$2"
                shift 2
                ;;
            --socket-timeout)
                SOCKET_TIMEOUT="$2"
                shift 2
                ;;
            --db|-d)
                MONGO_DB="$2"
                shift 2
                ;;
            --collection|-c)
                MONGO_COLLECTION="$2"
                shift 2
                ;;
            --uri)
                MONGO_URI="$2"
                shift 2
                ;;
            --output|-o)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            --file|-f)
                FILE_PATH="$2"
                shift 2
                ;;
            --type|-t)
                EXPORT_TYPE="$2"
                shift 2
                ;;
            --mode)
                IMPORT_MODE="$2"
                shift 2
                ;;
            --fields)
                FIELDS="$2"
                shift 2
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
            --upsertFields)
                UPSERT_FIELDS="$2"
                shift 2
                ;;
            --pretty)
                PRETTY=true
                shift
                ;;
            --headerline)
                HEADERLINE=true
                shift
                ;;
            --jsonArray)
                JSON_ARRAY=true
                shift
                ;;
            --drop)
                DROP=true
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
            --archive)
                ARCHIVE_FILE="$2"
                shift 2
                ;;
            --gzip)
                USE_GZIP=true
                shift
                ;;
            --no-gzip)
                USE_GZIP=false
                shift
                ;;
            --parallel|-j)
                PARALLEL_JOBS="$2"
                shift 2
                ;;
            --verbose|-v)
                VERBOSE=true
                LOG_LEVEL=$LOG_LEVEL_DEBUG
                shift
                ;;
            --quiet|-q)
                QUIET=true
                LOG_LEVEL=$LOG_LEVEL_ERROR
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --resume)
                RESUME=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                show_help
                exit "$EXIT_INVALID_ARGS"
                ;;
        esac
    done
}

#######################################
# Build MongoDB connection string
# Globals:
#   MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, MONGO_AUTH_DB, MONGO_URI
# Outputs:
#   MongoDB connection string
#######################################
build_mongo_uri() {
    # If URI is provided, use it directly
    if [[ -n "${MONGO_URI:-}" ]]; then
        echo "$MONGO_URI"
        return 0
    fi

    # Build URI from components
    local uri="mongodb://"

    # Add credentials if provided
    if [[ -n "${MONGO_USERNAME:-}" ]]; then
        uri="${uri}${MONGO_USERNAME}"
        if [[ -n "${MONGO_PASSWORD:-}" ]]; then
            uri="${uri}:${MONGO_PASSWORD}"
        fi
        uri="${uri}@"
    fi

    # Add host and port
    local host="${MONGO_HOST:-localhost}"
    local port="${MONGO_PORT:-27017}"
    uri="${uri}${host}:${port}"

    # Add auth database if provided
    if [[ -n "${MONGO_AUTH_DB:-}" ]]; then
        uri="${uri}/?authSource=${MONGO_AUTH_DB}"
    fi

    echo "$uri"
}

#######################################
# Sanitize connection string for logging
# Arguments:
#   $1 - Connection string
# Outputs:
#   Sanitized connection string (password masked)
#######################################
sanitize_uri() {
    local uri="$1"

    # Mask password in URI
    echo "$uri" | sed -E 's/(mongodb:\/\/[^:]+:)[^@]+(@)/\1***\2/'
}

#######################################
# Load default configuration
# Looks for config files in standard locations
#######################################
load_default_config() {
    local config_dir
    config_dir="$(cd "$SCRIPT_DIR" && cd "$CONFIG_DIR" && pwd 2>/dev/null || echo "")"

    if [[ -n "$config_dir" && -d "$config_dir" ]]; then
        # Try to load .env file
        if [[ -f "$config_dir/.env" ]]; then
            load_env_file "$config_dir/.env"
        fi

        # Try to load config.json
        if [[ -f "$config_dir/config.json" ]]; then
            load_config_file "$config_dir/config.json"
        fi
    else
        log_debug "Config directory not found, using command-line args only"
    fi
}

#######################################
# Validate required parameters
# Arguments:
#   $@ - List of required variable names
# Returns:
#   0 if all set, exits otherwise
#######################################
validate_required_params() {
    local missing=()

    for param in "$@"; do
        if ! is_set "$param"; then
            missing+=("$param")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required parameters: ${missing[*]}"
        log_info "Use --help for usage information"
        exit "$EXIT_INVALID_ARGS"
    fi
}
