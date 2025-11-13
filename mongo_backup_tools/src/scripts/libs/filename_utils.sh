#!/usr/bin/env bash
# filename_utils.sh - Filename and path manipulation utilities
# Provides consistent naming conventions for backup files

# Prevent multiple sourcing
[[ -n "${FILENAME_UTILS_SH_SOURCED:-}" ]] && return 0
readonly FILENAME_UTILS_SH_SOURCED=1

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./logging.sh
source "$SCRIPT_DIR/logging.sh"

#######################################
# Generate timestamp for filenames
# Outputs:
#   Timestamp string in format YYYYMMDD_HHMMSS
#######################################
generate_timestamp() {
    date +"%Y%m%d_%H%M%S"
}

#######################################
# Generate backup filename
# Arguments:
#   $1 - Database name
#   $2 - Optional collection name
#   $3 - Optional extension (default: .gz)
# Outputs:
#   Generated filename
#######################################
generate_backup_filename() {
    local db="$1"
    local collection="${2:-}"
    local extension="${3:-.gz}"
    local timestamp
    timestamp="$(generate_timestamp)"

    local filename="${db}_${timestamp}"

    if [[ -n "$collection" ]]; then
        filename="${filename}_${collection}"
    fi

    filename="${filename}${extension}"

    echo "$filename"
}

#######################################
# Generate export filename
# Arguments:
#   $1 - Database name
#   $2 - Collection name
#   $3 - Format (json/csv)
# Outputs:
#   Generated filename
#######################################
generate_export_filename() {
    local db="$1"
    local collection="$2"
    local format="${3:-json}"
    local timestamp
    timestamp="$(generate_timestamp)"

    local filename="${db}_${collection}_${timestamp}.${format}"

    echo "$filename"
}

#######################################
# Sanitize filename (remove invalid characters)
# Arguments:
#   $1 - Filename
# Outputs:
#   Sanitized filename
#######################################
sanitize_filename() {
    local filename="$1"

    # Replace invalid characters with underscores
    filename="${filename//[^a-zA-Z0-9._-]/_}"

    # Remove multiple consecutive underscores
    filename="${filename//__/_}"

    echo "$filename"
}

#######################################
# Get file extension
# Arguments:
#   $1 - Filename
# Outputs:
#   File extension (without dot)
#######################################
get_extension() {
    local filename="$1"

    if [[ "$filename" == *.* ]]; then
        echo "${filename##*.}"
    else
        echo ""
    fi
}

#######################################
# Get filename without extension
# Arguments:
#   $1 - Filename
# Outputs:
#   Filename without extension
#######################################
get_basename_no_ext() {
    local filename="$1"
    local basename
    basename="$(basename "$filename")"

    if [[ "$basename" == *.* ]]; then
        echo "${basename%.*}"
    else
        echo "$basename"
    fi
}

#######################################
# Ensure directory exists
# Arguments:
#   $1 - Directory path
# Returns:
#   0 on success, 1 on failure
#######################################
ensure_directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        log_debug "Creating directory: $dir"
        if mkdir -p "$dir" 2>/dev/null; then
            return 0
        else
            log_error "Failed to create directory: $dir"
            return 1
        fi
    fi

    return 0
}

#######################################
# Get absolute path
# Arguments:
#   $1 - Path (relative or absolute)
# Outputs:
#   Absolute path
#######################################
get_absolute_path() {
    local path="$1"

    if [[ -d "$path" ]]; then
        (cd "$path" && pwd)
    elif [[ -f "$path" ]]; then
        echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
    else
        # Path doesn't exist, try to resolve anyway
        if [[ "$path" = /* ]]; then
            echo "$path"
        else
            echo "$(pwd)/$path"
        fi
    fi
}

#######################################
# Get file size in human-readable format
# Arguments:
#   $1 - File path
# Outputs:
#   File size (e.g., "1.5G", "234M")
#######################################
get_file_size() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        echo "0"
        return 1
    fi

    if command -v numfmt >/dev/null 2>&1; then
        # Use numfmt if available (GNU coreutils)
        local size
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        numfmt --to=iec-i --suffix=B "$size"
    else
        # Fallback to ls
        ls -lh "$file" | awk '{print $5}'
    fi
}

#######################################
# Check if file is compressed
# Arguments:
#   $1 - File path
# Returns:
#   0 if compressed, 1 otherwise
#######################################
is_compressed() {
    local file="$1"
    local extension
    extension="$(get_extension "$file")"

    case "$extension" in
        gz|gzip|bz2|bzip2|xz|zip|tgz)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

#######################################
# Generate unique filename if file exists
# Arguments:
#   $1 - Desired filename
# Outputs:
#   Unique filename (original or with suffix)
#######################################
get_unique_filename() {
    local filename="$1"
    local base ext counter

    if [[ ! -e "$filename" ]]; then
        echo "$filename"
        return 0
    fi

    # File exists, append counter
    base="$(get_basename_no_ext "$filename")"
    ext="$(get_extension "$filename")"

    counter=1
    while [[ -e "${base}_${counter}.${ext}" ]]; do
        ((counter++))
    done

    if [[ -n "$ext" ]]; then
        echo "${base}_${counter}.${ext}"
    else
        echo "${base}_${counter}"
    fi
}

#######################################
# Calculate directory size
# Arguments:
#   $1 - Directory path
# Outputs:
#   Directory size in human-readable format
#######################################
get_dir_size() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        echo "0"
        return 1
    fi

    du -sh "$dir" 2>/dev/null | awk '{print $1}'
}

#######################################
# List files in directory with filter
# Arguments:
#   $1 - Directory path
#   $2 - Pattern (glob)
# Outputs:
#   List of matching files
#######################################
list_files() {
    local dir="$1"
    local pattern="${2:-*}"

    if [[ ! -d "$dir" ]]; then
        return 1
    fi

    find "$dir" -maxdepth 1 -type f -name "$pattern" 2>/dev/null
}
