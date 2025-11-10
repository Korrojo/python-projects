#!/bin/bash
# Automated virtual environment installer
# Detects OS, finds Python installations, and creates venv with selected version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Python Virtual Environment Installer ===${NC}"
echo ""

# Detect OS
OS_TYPE=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS_TYPE="Windows"
else
    echo -e "${YELLOW}Warning: Unknown OS type: $OSTYPE${NC}"
    echo "Attempting to detect Python anyway..."
fi

echo -e "${BLUE}Detected OS: ${OS_TYPE}${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version from executable
get_python_version() {
    local py_cmd="$1"
    if command_exists "$py_cmd"; then
        # macOS compatible: use sed instead of grep -P
        "$py_cmd" --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' || echo "unknown"
    else
        echo ""
    fi
}

# Find all Python installations
declare -a PYTHON_VERSIONS=()
declare -a PYTHON_PATHS=()

echo -e "${YELLOW}Searching for Python installations...${NC}"
echo ""

# Common Python command patterns to check
if [[ "$OS_TYPE" == "Windows" ]]; then
    # Windows: Check py launcher and common paths
    if command_exists py; then
        echo -e "${GREEN}✓ Found py launcher (Windows)${NC}"
        # Get list of available versions via py launcher
        PY_LIST=$(py -0 2>&1 || true)

        # Parse py launcher output for versions
        while IFS= read -r line; do
            if [[ $line =~ -([0-9]+\.[0-9]+) ]]; then
                version="${BASH_REMATCH[1]}"
                full_version=$(get_python_version "py -$version")
                if [[ -n "$full_version" && "$full_version" != "unknown" ]]; then
                    PYTHON_VERSIONS+=("$full_version")
                    PYTHON_PATHS+=("py -$version")
                    echo "  Found: Python $full_version (py -$version)"
                fi
            fi
        done <<< "$PY_LIST"
    fi

    # Check common Windows installation paths
    for py_path in "/c/Python3"*"/python.exe" "/c/Program Files/Python"*"/python.exe"; do
        if [[ -f "$py_path" ]]; then
            version=$(get_python_version "$py_path")
            if [[ -n "$version" && "$version" != "unknown" ]]; then
                # Check if not already added
                if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${version} " ]]; then
                    PYTHON_VERSIONS+=("$version")
                    PYTHON_PATHS+=("$py_path")
                    echo "  Found: Python $version ($py_path)"
                fi
            fi
        fi
    done
else
    # Linux/macOS: Check common commands
    for py_cmd in python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
        version=$(get_python_version "$py_cmd")
        if [[ -n "$version" && "$version" != "unknown" ]]; then
            # Check if not already added
            if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${version} " ]]; then
                py_path=$(command -v "$py_cmd" 2>/dev/null || echo "$py_cmd")
                PYTHON_VERSIONS+=("$version")
                PYTHON_PATHS+=("$py_path")
                echo "  Found: Python $version ($py_path)"
            fi
        fi
    done
fi

echo ""

# Check if any Python found
if [[ ${#PYTHON_VERSIONS[@]} -eq 0 ]]; then
    echo -e "${RED}ERROR: No Python installations found!${NC}"
    echo ""
    echo "Would you like to install Python 3.11 now?"
    echo ""

    if [[ "$OS_TYPE" == "macOS" ]]; then
        if command_exists brew; then
            read -p "Install Python 3.11 using Homebrew? (y/N): " install_confirm
            if [[ "$install_confirm" =~ ^[Yy]$ ]]; then
                echo ""
                echo -e "${YELLOW}Installing Python 3.11 via Homebrew...${NC}"
                brew install python@3.11
                echo ""
                echo -e "${GREEN}✓ Python 3.11 installed!${NC}"
                echo "Re-running detection..."
                exec "$0"
            fi
        else
            echo "Homebrew not found. Install from: https://brew.sh"
        fi
    elif [[ "$OS_TYPE" == "Windows" ]]; then
        if command_exists choco; then
            read -p "Install Python 3.11 using Chocolatey? (y/N): " install_confirm
            if [[ "$install_confirm" =~ ^[Yy]$ ]]; then
                echo ""
                echo -e "${YELLOW}Installing Python 3.11 via Chocolatey...${NC}"
                choco install python311 -y
                echo ""
                echo -e "${GREEN}✓ Python 3.11 installed!${NC}"
                echo "Re-running detection..."
                exec "$0"
            fi
        else
            echo "Chocolatey not found. Install from: https://chocolatey.org"
        fi
    fi

    echo ""
    echo "Manual installation options:"
    if [[ "$OS_TYPE" == "Windows" ]]; then
        echo "  https://www.python.org/downloads/windows/"
    elif [[ "$OS_TYPE" == "macOS" ]]; then
        echo "  https://www.python.org/downloads/macos/"
        echo "  Or use Homebrew: brew install python@3.11"
    else
        echo "  https://www.python.org/downloads/"
    fi
    echo ""
    echo "After installation, ensure Python is in your PATH and re-run this script."
    exit 1
fi

# Display found versions and prompt for selection
echo -e "${GREEN}Found ${#PYTHON_VERSIONS[@]} Python installation(s):${NC}"
echo ""

for i in "${!PYTHON_VERSIONS[@]}"; do
    idx=$((i + 1))
    version="${PYTHON_VERSIONS[$i]}"
    path="${PYTHON_PATHS[$i]}"

    # Highlight Python 3.11 (recommended)
    if [[ "$version" == 3.11.* ]]; then
        echo -e "  ${idx}) Python ${GREEN}${version}${NC} (RECOMMENDED) - $path"
    else
        echo "  ${idx}) Python ${version} - $path"
    fi
done

echo ""

# Prompt for selection
while true; do
    read -p "Select Python version (1-${#PYTHON_VERSIONS[@]}) [default: 1]: " selection
    selection=${selection:-1}

    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#PYTHON_VERSIONS[@]}" ]; then
        break
    else
        echo -e "${RED}Invalid selection. Please enter a number between 1 and ${#PYTHON_VERSIONS[@]}${NC}"
    fi
done

idx=$((selection - 1))
SELECTED_VERSION="${PYTHON_VERSIONS[$idx]}"
SELECTED_PATH="${PYTHON_PATHS[$idx]}"

echo ""
echo -e "${GREEN}Selected: Python $SELECTED_VERSION${NC}"
echo -e "${BLUE}Path: $SELECTED_PATH${NC}"
echo ""

# Determine venv directory name based on major.minor version
# macOS compatible: use sed instead of grep -P
VENV_VERSION=$(echo "$SELECTED_VERSION" | sed -n 's/^\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p')
VENV_DIR=".venv${VENV_VERSION//./}"

# Warn if different version already exists
if [[ -d "$VENV_DIR" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment '$VENV_DIR' already exists!${NC}"
    read -p "Do you want to remove it and recreate? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo "Removing existing venv..."
        rm -rf "$VENV_DIR"
    else
        echo "Installation cancelled."
        exit 0
    fi
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}Creating virtual environment: $VENV_DIR${NC}"
if [[ "$SELECTED_PATH" == py\ -* ]]; then
    # Use py launcher syntax
    $SELECTED_PATH -m venv "$VENV_DIR"
else
    # Direct Python path
    "$SELECTED_PATH" -m venv "$VENV_DIR"
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo -e "${RED}ERROR: Failed to create virtual environment!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment created successfully!${NC}"
echo ""

# Verify venv Python version
echo -e "${YELLOW}Verifying virtual environment...${NC}"
VENV_PYTHON=""
if [[ "$OS_TYPE" == "Windows" ]]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
else
    VENV_PYTHON="$VENV_DIR/bin/python"
fi

VENV_VERSION_CHECK=$("$VENV_PYTHON" --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' || echo "unknown")
echo -e "${GREEN}✓ Virtual environment Python version: $VENV_VERSION_CHECK${NC}"

# Check if version matches
if [[ "$VENV_VERSION_CHECK" == "$SELECTED_VERSION" ]]; then
    echo -e "${GREEN}✓ Version verified!${NC}"
else
    echo -e "${YELLOW}⚠ Warning: venv version ($VENV_VERSION_CHECK) differs from selected ($SELECTED_VERSION)${NC}"
fi

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo "Virtual environment created at: $VENV_DIR"
echo ""
echo "Next steps:"
echo ""
echo "1) Activate the virtual environment:"
if [[ "$OS_TYPE" == "Windows" ]]; then
    echo -e "   ${BLUE}source ./activate_venv.sh${NC}  (Git Bash)"
    echo -e "   ${BLUE}.\\activate_venv.ps1${NC}  (PowerShell)"
    echo -e "   ${BLUE}$VENV_DIR\\Scripts\\activate.bat${NC}  (CMD)"
else
    echo -e "   ${BLUE}source ./activate_venv.sh${NC}"
    echo -e "   Or: ${BLUE}source $VENV_DIR/bin/activate${NC}"
fi
echo ""
echo "2) Install dependencies:"
echo -e "   ${BLUE}pip install -r requirements.txt${NC}"
echo -e "   ${YELLOW}   (This automatically installs common_config in editable mode)${NC}"
echo ""
echo "3) Verify installation:"
echo -e "   ${BLUE}python --version${NC}"
echo -e "   ${BLUE}pip show common-config${NC}"
