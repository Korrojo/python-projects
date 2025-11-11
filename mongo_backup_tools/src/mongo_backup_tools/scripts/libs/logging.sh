#!/usr/bin/env bash
# logging.sh - Centralized logging utilities for MongoDB backup tools
# Provides consistent logging across all shell scripts

# Prevent multiple sourcing
[[ -n "${LOGGING_SH_SOURCED:-}" ]] && return 0
readonly LOGGING_SH_SOURCED=1

# Color codes for terminal output
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_NC='\033[0m' # No Color

# Log levels
readonly LOG_LEVEL_DEBUG=0
readonly LOG_LEVEL_INFO=1
readonly LOG_LEVEL_WARN=2
readonly LOG_LEVEL_ERROR=3
readonly LOG_LEVEL_FATAL=4

# Default log level (INFO)
: "${LOG_LEVEL:=$LOG_LEVEL_INFO}"

# Log file (can be set by caller)
: "${LOG_FILE:=""}"

# Timestamp format
readonly TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"

#######################################
# Get current timestamp
# Outputs:
#   Timestamp string
#######################################
get_timestamp() {
    date "$TIMESTAMP_FORMAT"
}

#######################################
# Log a message with specified level
# Arguments:
#   $1 - Log level
#   $2 - Message
# Outputs:
#   Formatted log message
#######################################
log_message() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(get_timestamp)"

    local log_entry="[$timestamp] [$level] $message"

    # Write to log file if specified
    if [[ -n "$LOG_FILE" ]]; then
        echo "$log_entry" >> "$LOG_FILE"
    fi

    # Output to stderr
    echo "$log_entry" >&2
}

#######################################
# Log debug message
# Arguments:
#   $* - Message
#######################################
log_debug() {
    if [[ $LOG_LEVEL -le $LOG_LEVEL_DEBUG ]]; then
        log_message "DEBUG" "$@"
    fi
}

#######################################
# Log info message
# Arguments:
#   $* - Message
#######################################
log_info() {
    if [[ $LOG_LEVEL -le $LOG_LEVEL_INFO ]]; then
        echo -e "${COLOR_CYAN}[INFO]${COLOR_NC} $*" >&2
        if [[ -n "$LOG_FILE" ]]; then
            log_message "INFO" "$@" 2>/dev/null
        fi
    fi
}

#######################################
# Log success message
# Arguments:
#   $* - Message
#######################################
log_success() {
    if [[ $LOG_LEVEL -le $LOG_LEVEL_INFO ]]; then
        echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_NC} $*" >&2
        if [[ -n "$LOG_FILE" ]]; then
            log_message "SUCCESS" "$@" 2>/dev/null
        fi
    fi
}

#######################################
# Log warning message
# Arguments:
#   $* - Message
#######################################
log_warn() {
    if [[ $LOG_LEVEL -le $LOG_LEVEL_WARN ]]; then
        echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $*" >&2
        if [[ -n "$LOG_FILE" ]]; then
            log_message "WARN" "$@" 2>/dev/null
        fi
    fi
}

#######################################
# Log error message
# Arguments:
#   $* - Message
#######################################
log_error() {
    if [[ $LOG_LEVEL -le $LOG_LEVEL_ERROR ]]; then
        echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $*" >&2
        if [[ -n "$LOG_FILE" ]]; then
            log_message "ERROR" "$@" 2>/dev/null
        fi
    fi
}

#######################################
# Log fatal error and exit
# Arguments:
#   $1 - Exit code
#   $* - Message
#######################################
log_fatal() {
    local exit_code="${1:-1}"
    shift
    echo -e "${COLOR_RED}[FATAL]${COLOR_NC} $*" >&2
    if [[ -n "$LOG_FILE" ]]; then
        log_message "FATAL" "$@" 2>/dev/null
    fi
    exit "$exit_code"
}

#######################################
# Log section header
# Arguments:
#   $* - Header text
#######################################
log_section() {
    local header="$*"
    local separator
    separator=$(printf '=%.0s' {1..80})

    log_info ""
    log_info "$separator"
    log_info "$header"
    log_info "$separator"
}

#######################################
# Log progress indicator
# Arguments:
#   $1 - Current step
#   $2 - Total steps
#   $3 - Message
#######################################
log_progress() {
    local current="$1"
    local total="$2"
    local message="$3"

    echo -e "${COLOR_BLUE}[${current}/${total}]${COLOR_NC} $message" >&2
}
