#!/bin/bash
# Git Branch Cleanup Script
# Safely cleans up merged branches and provides reports on unmerged branches

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Git Branch Cleanup Tool ===${NC}\n"

# Function to delete merged branches
delete_merged_branches() {
    echo -e "${YELLOW}Checking for branches merged into main...${NC}"

    MERGED_BRANCHES=$(git branch --merged main | grep -v "^\*" | grep -v "  main$" || true)

    if [ -z "$MERGED_BRANCHES" ]; then
        echo -e "${GREEN}✓ No merged branches to delete${NC}\n"
        return
    fi

    echo -e "${GREEN}Found merged branches:${NC}"
    echo "$MERGED_BRANCHES"
    echo ""

    read -p "Delete these merged branches? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$MERGED_BRANCHES" | xargs -n 1 git branch -d
        echo -e "${GREEN}✓ Deleted merged branches${NC}\n"
    else
        echo -e "${YELLOW}Skipped deletion${NC}\n"
    fi
}

# Function to report unmerged branches
report_unmerged_branches() {
    echo -e "${YELLOW}Unmerged branches (sorted by date):${NC}\n"

    git for-each-ref --sort=-committerdate refs/heads/ \
        --format='%(refname:short)|%(committerdate:short)|%(authorname)' \
        --no-merged=main | while IFS='|' read -r branch date author; do
        echo -e "  📌 ${GREEN}$branch${NC} (${BLUE}$date${NC}) - $author"
    done
    echo ""
}

# Function to delete remote merged branches
delete_remote_merged_branches() {
    echo -e "${YELLOW}Checking for remote branches merged into origin/main...${NC}"

    git fetch --prune origin

    REMOTE_MERGED=$(git branch -r --merged origin/main | \
        grep "origin/" | \
        grep -v "origin/main" | \
        grep -v "origin/HEAD" | \
        sed 's/origin\///' || true)

    if [ -z "$REMOTE_MERGED" ]; then
        echo -e "${GREEN}✓ No remote merged branches to delete${NC}\n"
        return
    fi

    echo -e "${GREEN}Found remote merged branches:${NC}"
    echo "$REMOTE_MERGED"
    echo ""

    read -p "Delete these remote branches? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$REMOTE_MERGED" | xargs -I {} git push origin --delete {}
        echo -e "${GREEN}✓ Deleted remote merged branches${NC}\n"
    else
        echo -e "${YELLOW}Skipped remote deletion${NC}\n"
    fi
}

# Function to show stale branches (older than N days)
show_stale_branches() {
    local DAYS=${1:-30}
    echo -e "${YELLOW}Branches older than $DAYS days:${NC}\n"

    CUTOFF_DATE=$(date -v-${DAYS}d +%Y-%m-%d 2>/dev/null || date -d "$DAYS days ago" +%Y-%m-%d 2>/dev/null)

    git for-each-ref --sort=committerdate refs/heads/ \
        --format='%(refname:short)|%(committerdate:short)' | \
        while IFS='|' read -r branch date; do
            if [[ "$date" < "$CUTOFF_DATE" ]] && [[ "$branch" != "main" ]]; then
                echo -e "  🕐 ${RED}$branch${NC} - last updated $date"
            fi
        done
    echo ""
}

# Main menu
case "${1:-menu}" in
    "merged")
        delete_merged_branches
        ;;
    "remote")
        delete_remote_merged_branches
        ;;
    "report")
        report_unmerged_branches
        ;;
    "stale")
        show_stale_branches "${2:-30}"
        ;;
    "all")
        delete_merged_branches
        delete_remote_merged_branches
        report_unmerged_branches
        ;;
    "menu"|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  merged   - Delete local branches already merged to main"
        echo "  remote   - Delete remote branches already merged to origin/main"
        echo "  report   - Show all unmerged branches"
        echo "  stale    - Show branches older than N days (default: 30)"
        echo "  all      - Run all cleanup operations"
        echo ""
        echo "Examples:"
        echo "  $0 merged"
        echo "  $0 remote"
        echo "  $0 stale 60"
        echo "  $0 all"
        ;;
esac
