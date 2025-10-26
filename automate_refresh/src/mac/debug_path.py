import glob
import os
import re
from datetime import datetime


def debug_file_search():
    """
    This script performs a step-by-step diagnosis of the file finding logic.
    """
    print("--- STARTING DEEP DIVE DIAGNOSIS ---")

    # --- 1. Hardcoded Values ---
    # Using the exact values from your logs and ls output.
    in_dir_raw = "~/Backups/local/export"
    collection = "Patients"
    expected_filename = "20251013_005928_export_Patients.json"

    print(f"[*] Using raw input directory: '{in_dir_raw}'")
    print(f"[*] Using collection: '{collection}'")

    # --- 2. Tilde Expansion ---
    # This is the most likely point of failure. Let's verify it.
    in_dir_expanded = os.path.expanduser(in_dir_raw)
    print("\n--- 2. Path Expansion ---")
    print(f"[+] Expanded path: '{in_dir_expanded}'")

    # --- 3. Path Existence and Contents ---
    # Let's see if Python can actually see the directory and its contents.
    print("\n--- 3. Directory Access ---")
    path_exists = os.path.exists(in_dir_expanded)
    print(f"[+] Does expanded path exist? {path_exists}")

    if not path_exists:
        print("[!] FAILURE: The expanded path does not exist. The script cannot find the directory.")
        return

    try:
        dir_contents = os.listdir(in_dir_expanded)
        print(f"[+] Directory contents: {dir_contents}")
        if not dir_contents:
            print("[!] WARNING: Directory is empty.")
    except Exception as e:
        print(f"[!] FAILURE: Could not read directory contents. Error: {e}")
        return

    # --- 4. Glob Pattern Matching ---
    # Let's test the glob patterns against the now-verified path.
    print("\n--- 4. Glob Pattern Matching ---")

    # Pattern 1: Day-specific
    ymd = datetime.now().strftime("%Y%m%d")
    pattern_day = os.path.join(in_dir_expanded, f"{ymd}_*_export_{collection}.json")
    day_files = glob.glob(pattern_day)
    print(f"[+] Day-specific pattern: '{pattern_day}'")
    print(f"    Matches: {day_files}")

    # Pattern 2: Any date in export dir
    pattern_any = os.path.join(in_dir_expanded, f"*_export_{collection}.json")
    any_files = glob.glob(pattern_any)
    print(f"[+] Any-date pattern: '{pattern_any}'")
    print(f"    Matches: {any_files}")

    # --- 5. Regex Filtering ---
    # If glob finds files, let's check if the regex filter is correct.
    print("\n--- 5. Regex Filtering ---")
    if not any_files:
        print("[+] Skipping regex check, glob found no files.")
    else:
        rx_full = re.compile(r"^(\d{8})_(\d{6})_export_" + re.escape(collection) + r"\.json$")
        rx_month = re.compile(r"^(\d{6})_(\d{6})_export_" + re.escape(collection) + r"\.json$")

        print(f"[+] Checking filename: '{expected_filename}'")
        print(f"    Regex (full date): {rx_full.pattern}")
        match_full = rx_full.search(expected_filename)
        print(f"    --> Match? {'YES' if match_full else 'NO'}")

        print(f"    Regex (month): {rx_month.pattern}")
        match_month = rx_month.search(expected_filename)
        print(f"    --> Match? {'YES' if match_month else 'NO'}")

    print("\n--- DIAGNOSIS COMPLETE ---")


if __name__ == "__main__":
    debug_file_search()
