#!/usr/bin/env bash
# state_tracking.sh - Operation state tracking and resume capability
# Provides state persistence for resumable MongoDB operations

# Prevent multiple sourcing
[[ -n "${STATE_TRACKING_SH_SOURCED:-}" ]] && return 0
readonly STATE_TRACKING_SH_SOURCED=1

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./logging.sh
source "$SCRIPT_DIR/logging.sh"
# shellcheck source=./error_handling.sh
source "$SCRIPT_DIR/error_handling.sh"

# State file directory (default to temp/)
: "${STATE_DIR:="../../../../../../temp"}"

#######################################
# Initialize state tracking
# Arguments:
#   $1 - Operation name (dump, restore, etc.)
#   $2 - Operation ID (optional, auto-generated if not provided)
# Returns:
#   STATE_FILE path
#######################################
init_state_tracking() {
    local operation="$1"
    local operation_id="${2:-$(date +%Y%m%d_%H%M%S)}"

    # Create state directory if it doesn't exist
    local state_dir
    state_dir="$(cd "$SCRIPT_DIR" && cd "$STATE_DIR" && pwd)"
    mkdir -p "$state_dir"

    # Set state file path
    STATE_FILE="$state_dir/${operation}_${operation_id}.state"

    log_debug "State file: $STATE_FILE"

    # Initialize state file
    if [[ ! -f "$STATE_FILE" ]]; then
        cat > "$STATE_FILE" <<EOF
{
  "operation": "$operation",
  "operation_id": "$operation_id",
  "start_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "in_progress",
  "completed_items": [],
  "failed_items": [],
  "total_items": 0,
  "current_item": ""
}
EOF
        log_debug "Created new state file"
    else
        log_info "Resuming from existing state file"
    fi

    echo "$STATE_FILE"
}

#######################################
# Update state file
# Arguments:
#   $1 - Key to update
#   $2 - Value
#######################################
update_state() {
    local key="$1"
    local value="$2"

    if [[ ! -f "$STATE_FILE" ]]; then
        log_warn "State file not found: $STATE_FILE"
        return 1
    fi

    # Use jq if available for proper JSON manipulation
    if command_exists jq; then
        local temp_file
        temp_file="$(mktemp)"
        jq ".$key = \"$value\"" "$STATE_FILE" > "$temp_file"
        mv "$temp_file" "$STATE_FILE"
    else
        # Fallback: simple sed replacement (works for simple values)
        sed -i.bak "s/\"$key\": \"[^\"]*\"/\"$key\": \"$value\"/" "$STATE_FILE"
        rm -f "${STATE_FILE}.bak"
    fi

    log_debug "Updated state: $key = $value"
}

#######################################
# Get state value
# Arguments:
#   $1 - Key to retrieve
# Outputs:
#   Value for the key
#######################################
get_state() {
    local key="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        log_warn "State file not found: $STATE_FILE"
        return 1
    fi

    if command_exists jq; then
        jq -r ".$key" "$STATE_FILE"
    else
        # Fallback: grep and sed
        grep "\"$key\"" "$STATE_FILE" | sed 's/.*: "\(.*\)".*/\1/'
    fi
}

#######################################
# Add completed item
# Arguments:
#   $1 - Item name
#######################################
add_completed_item() {
    local item="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        log_warn "State file not found: $STATE_FILE"
        return 1
    fi

    if command_exists jq; then
        local temp_file
        temp_file="$(mktemp)"
        jq ".completed_items += [\"$item\"]" "$STATE_FILE" > "$temp_file"
        mv "$temp_file" "$STATE_FILE"
    else
        # Simple append (not valid JSON but trackable)
        log_debug "Completed: $item" >> "${STATE_FILE}.log"
    fi

    log_debug "Marked as completed: $item"
}

#######################################
# Add failed item
# Arguments:
#   $1 - Item name
#   $2 - Error message
#######################################
add_failed_item() {
    local item="$1"
    local error="${2:-Unknown error}"

    if [[ ! -f "$STATE_FILE" ]]; then
        log_warn "State file not found: $STATE_FILE"
        return 1
    fi

    if command_exists jq; then
        local temp_file
        temp_file="$(mktemp)"
        jq ".failed_items += [{\"item\": \"$item\", \"error\": \"$error\"}]" "$STATE_FILE" > "$temp_file"
        mv "$temp_file" "$STATE_FILE"
    else
        # Simple append
        log_debug "Failed: $item - $error" >> "${STATE_FILE}.log"
    fi

    log_warn "Marked as failed: $item - $error"
}

#######################################
# Check if item is completed
# Arguments:
#   $1 - Item name
# Returns:
#   0 if completed, 1 otherwise
#######################################
is_item_completed() {
    local item="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    if command_exists jq; then
        jq -e ".completed_items | index(\"$item\")" "$STATE_FILE" >/dev/null 2>&1
        return $?
    else
        grep -q "Completed: $item" "${STATE_FILE}.log" 2>/dev/null
        return $?
    fi
}

#######################################
# Mark operation as complete
# Arguments:
#   $1 - Optional status (default: completed)
#######################################
complete_operation() {
    local status="${1:-completed}"

    update_state "status" "$status"
    update_state "end_time" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    log_success "Operation marked as: $status"
}

#######################################
# Clean up state file
#######################################
cleanup_state() {
    if [[ -f "$STATE_FILE" ]]; then
        log_debug "Cleaning up state file: $STATE_FILE"
        rm -f "$STATE_FILE" "${STATE_FILE}.log" "${STATE_FILE}.bak"
    fi
}

#######################################
# Print state summary
#######################################
print_state_summary() {
    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    log_section "Operation State Summary"

    if command_exists jq; then
        local status completed_count failed_count
        status=$(jq -r '.status' "$STATE_FILE")
        completed_count=$(jq -r '.completed_items | length' "$STATE_FILE")
        failed_count=$(jq -r '.failed_items | length' "$STATE_FILE")

        log_info "Status: $status"
        log_info "Completed items: $completed_count"
        if [[ $failed_count -gt 0 ]]; then
            log_warn "Failed items: $failed_count"
        fi
    else
        log_info "State file: $STATE_FILE"
        if [[ -f "${STATE_FILE}.log" ]]; then
            local completed_count failed_count
            completed_count=$(grep -c "Completed:" "${STATE_FILE}.log" 2>/dev/null || echo 0)
            failed_count=$(grep -c "Failed:" "${STATE_FILE}.log" 2>/dev/null || echo 0)

            log_info "Completed items: $completed_count"
            if [[ $failed_count -gt 0 ]]; then
                log_warn "Failed items: $failed_count"
            fi
        fi
    fi
}
