#!/bin/bash
# Automated virtual environment activator
# Detects available venv and activates it based on OS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS_TYPE=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS_TYPE="Windows"
fi

# Find available virtual environments
declare -a VENV_DIRS=()
declare -a VENV_VERSIONS=()

for venv_dir in .venv*; do
    if [[ -d "$venv_dir" ]]; then
        # Check if it's a valid venv
        if [[ "$OS_TYPE" == "Windows" ]]; then
            if [[ -f "$venv_dir/Scripts/python.exe" ]]; then
                VENV_DIRS+=("$venv_dir")
                # Get Python version from venv
                version=$("$venv_dir/Scripts/python.exe" --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
                VENV_VERSIONS+=("$version")
            fi
        else
            if [[ -f "$venv_dir/bin/python" ]]; then
                VENV_DIRS+=("$venv_dir")
                # Get Python version from venv
                version=$("$venv_dir/bin/python" --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
                VENV_VERSIONS+=("$version")
            fi
        fi
    fi
done

# Check if any venv found
if [[ ${#VENV_DIRS[@]} -eq 0 ]]; then
    echo -e "${RED}ERROR: No virtual environments found!${NC}"
    echo ""
    echo "Create one first using:"
    echo -e "  ${BLUE}./install_venv.sh${NC}"
    exit 1
fi

# If only one venv, use it
if [[ ${#VENV_DIRS[@]} -eq 1 ]]; then
    SELECTED_VENV="${VENV_DIRS[0]}"
    SELECTED_VERSION="${VENV_VERSIONS[0]}"
else
    # Multiple venvs found, prompt for selection
    echo -e "${YELLOW}Multiple virtual environments found:${NC}"
    echo ""
    
    for i in "${!VENV_DIRS[@]}"; do
        idx=$((i + 1))
        venv="${VENV_DIRS[$i]}"
        version="${VENV_VERSIONS[$i]}"
        echo "  ${idx}) $venv (Python $version)"
    done
    
    echo ""
    
    while true; do
        read -p "Select virtual environment (1-${#VENV_DIRS[@]}) [default: 1]: " selection
        selection=${selection:-1}
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#VENV_DIRS[@]}" ]; then
            break
        else
            echo -e "${RED}Invalid selection. Please enter a number between 1 and ${#VENV_DIRS[@]}${NC}"
        fi
    done
    
    idx=$((selection - 1))
    SELECTED_VENV="${VENV_DIRS[$idx]}"
    SELECTED_VERSION="${VENV_VERSIONS[$idx]}"
fi

# Activate the selected venv
echo ""
echo -e "${GREEN}Activating: $SELECTED_VENV (Python $SELECTED_VERSION)${NC}"
echo ""

if [[ "$OS_TYPE" == "Windows" ]]; then
    ACTIVATE_SCRIPT="$SELECTED_VENV/Scripts/activate"
else
    ACTIVATE_SCRIPT="$SELECTED_VENV/bin/activate"
fi

if [[ ! -f "$ACTIVATE_SCRIPT" ]]; then
    echo -e "${RED}ERROR: Activation script not found: $ACTIVATE_SCRIPT${NC}"
    exit 1
fi

# Source the activation script
# Note: This must be sourced, not executed
source "$ACTIVATE_SCRIPT"

# Verify activation
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${RED}ERROR: Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated!${NC}"
echo ""
echo "Python version: $(python --version)"
echo "Python path: $(which python)"
echo ""
echo -e "${YELLOW}To deactivate, run:${NC} deactivate"
