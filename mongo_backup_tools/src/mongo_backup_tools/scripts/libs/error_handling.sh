#!/usr/bin/env bash
# error_handling.sh - Error handling and exit code management
# Provides consistent error handling across all shell scripts

# Prevent multiple sourcing
[[ -n "${ERROR_HANDLING_SH_SOURCED:-}" ]] && return 0
readonly ERROR_HANDLING_SH_SOURCED=1

# Source logging library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./logging.sh
source "$SCRIPT_DIR/logging.sh"

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_GENERAL_ERROR=1
readonly EXIT_INVALID_ARGS=2
readonly EXIT_CONNECTION_ERROR=3
readonly EXIT_AUTH_ERROR=4
readonly EXIT_FILE_NOT_FOUND=5
readonly EXIT_PERMISSION_DENIED=6
readonly EXIT_DISK_FULL=7
readonly EXIT_OPERATION_FAILED=8
readonly EXIT_INTERRUPTED=130

# Global error tracking
ERROR_COUNT=0
WARNING_COUNT=0

#######################################
# Set up error traps
# Globals:
#   None
#######################################
setup_error_traps() {
    # Exit on error, but allow error handling
    set -e
    set -o pipefail

    # Trap errors
    trap 'handle_error $? $LINENO' ERR
    trap 'handle_interrupt' INT TERM
}

#######################################
# Handle errors
# Arguments:
#   $1 - Exit code
#   $2 - Line number
#######################################
handle_error() {
    local exit_code="$1"
    local line_number="$2"

    log_error "Command failed with exit code $exit_code at line $line_number"
    ((ERROR_COUNT++))

    # Don't exit if we're in a subshell or specific error handling is in place
    if [[ "${BASH_SUBSHELL}" -eq 0 ]]; then
        cleanup_on_error
        exit "$exit_code"
    fi
}

#######################################
# Handle interrupt signals (Ctrl+C)
#######################################
handle_interrupt() {
    log_warn "Operation interrupted by user"
    cleanup_on_error
    exit "$EXIT_INTERRUPTED"
}

#######################################
# Cleanup function to be called on error
# Can be overridden by caller
#######################################
cleanup_on_error() {
    log_debug "Performing cleanup..."
    # Override this function in your script if needed
    :
}

#######################################
# Check if command exists
# Arguments:
#   $1 - Command name
# Returns:
#   0 if exists, 1 otherwise
#######################################
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

#######################################
# Require command to exist or exit
# Arguments:
#   $1 - Command name
#   $2 - Optional error message
#######################################
require_command() {
    local cmd="$1"
    local error_msg="${2:-Command '$cmd' is required but not found}"

    if ! command_exists "$cmd"; then
        log_fatal "$EXIT_GENERAL_ERROR" "$error_msg"
    fi
}

#######################################
# Check if file exists
# Arguments:
#   $1 - File path
# Returns:
#   0 if exists, 1 otherwise
#######################################
file_exists() {
    [[ -f "$1" ]]
}

#######################################
# Require file to exist or exit
# Arguments:
#   $1 - File path
#   $2 - Optional error message
#######################################
require_file() {
    local file="$1"
    local error_msg="${2:-Required file not found: $file}"

    if ! file_exists "$file"; then
        log_fatal "$EXIT_FILE_NOT_FOUND" "$error_msg"
    fi
}

#######################################
# Check if directory exists
# Arguments:
#   $1 - Directory path
# Returns:
#   0 if exists, 1 otherwise
#######################################
dir_exists() {
    [[ -d "$1" ]]
}

#######################################
# Require directory to exist or exit
# Arguments:
#   $1 - Directory path
#   $2 - Optional error message
#######################################
require_dir() {
    local dir="$1"
    local error_msg="${2:-Required directory not found: $dir}"

    if ! dir_exists "$dir"; then
        log_fatal "$EXIT_FILE_NOT_FOUND" "$error_msg"
    fi
}

#######################################
# Check if variable is set
# Arguments:
#   $1 - Variable name
# Returns:
#   0 if set, 1 otherwise
#######################################
is_set() {
    local var_name="$1"
    [[ -n "${!var_name:-}" ]]
}

#######################################
# Require variable to be set or exit
# Arguments:
#   $1 - Variable name
#   $2 - Optional error message
#######################################
require_var() {
    local var_name="$1"
    local error_msg="${2:-Required variable not set: $var_name}"

    if ! is_set "$var_name"; then
        log_fatal "$EXIT_INVALID_ARGS" "$error_msg"
    fi
}

#######################################
# Validate MongoDB connection string
# Arguments:
#   $1 - Connection string
# Returns:
#   0 if valid format, 1 otherwise
#######################################
validate_mongo_uri() {
    local uri="$1"

    # Basic validation - must start with mongodb:// or mongodb+srv://
    if [[ ! "$uri" =~ ^mongodb(\+srv)?:// ]]; then
        log_error "Invalid MongoDB connection string format"
        return 1
    fi

    return 0
}

#######################################
# Print error summary
#######################################
print_error_summary() {
    if [[ $ERROR_COUNT -gt 0 || $WARNING_COUNT -gt 0 ]]; then
        log_section "Operation Summary"

        if [[ $ERROR_COUNT -gt 0 ]]; then
            log_error "Total errors: $ERROR_COUNT"
        fi

        if [[ $WARNING_COUNT -gt 0 ]]; then
            log_warn "Total warnings: $WARNING_COUNT"
        fi
    fi
}
