#!/usr/bin/env python
"""
Test DOB Masking with ISO Format

This script tests if DOB masking correctly adds milliseconds while preserving date format.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.masking_rule import MaskingRule, RuleEngine

def test_dob_masking():
    """Test DOB masking with ISO format."""
    print("\n=== Testing DOB Masking ===\n")
    
    # Create sample documents with different DOB formats
    test_docs = [
        {"_id": "1", "Dob": "1930-01-14T00:00:00.000Z"},
        {"_id": "2", "Dob": "1985-05-15"},
        {"_id": "3", "Dob": "1990/01/01"},
        {"_id": "4", "Dob": datetime(1980, 1, 1)}
    ]
    
    # Create rule
    milliseconds_to_add = 62208000000  # ~720 days
    rule = MaskingRule(field="Dob", rule_type="add_milliseconds", params=milliseconds_to_add)
    
    # Create rule engine with this rule
    rule_engine = RuleEngine([rule])
    
    # Mask each document and show results
    for doc in test_docs:
        original_value = doc["Dob"]
        original_type = type(original_value)
        
        # Calculate expected result for verification
        if isinstance(original_value, str):
            try:
                # For ISO format date strings
                if "T" in original_value:
                    dt = datetime.fromisoformat(original_value.replace("Z", "+00:00"))
                    days_to_add = milliseconds_to_add / (1000 * 60 * 60 * 24)
                    expected_dt = dt + timedelta(days=days_to_add)
                    expected = expected_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                # For simple date strings
                elif "-" in original_value:
                    dt = datetime.strptime(original_value, "%Y-%m-%d")
                    days_to_add = milliseconds_to_add / (1000 * 60 * 60 * 24)
                    expected_dt = dt + timedelta(days=days_to_add)
                    expected = expected_dt.strftime("%Y-%m-%d")
                # For date strings with forward slash
                elif "/" in original_value:
                    dt = datetime.strptime(original_value, "%Y/%m/%d")
                    days_to_add = milliseconds_to_add / (1000 * 60 * 60 * 24)
                    expected_dt = dt + timedelta(days=days_to_add)
                    expected = expected_dt.strftime("%Y/%m/%d")
                else:
                    expected = "Unable to parse"
            except:
                expected = "Unable to parse"
        else:
            # For datetime objects
            days_to_add = milliseconds_to_add / (1000 * 60 * 60 * 24)
            expected = original_value + timedelta(days=days_to_add)
        
        # Mask the document
        masked_doc = rule_engine.apply_rules(doc.copy())
        masked_value = masked_doc["Dob"]
        
        # Display results
        print(f"Original ({original_type.__name__}): {original_value}")
        print(f"Masked   ({type(masked_value).__name__}): {masked_value}")
        
        # Verify if milliseconds were added correctly
        if isinstance(expected, datetime):
            print(f"Expected ({type(expected).__name__}): {expected}")
            days_diff = (masked_value - original_value).days
            expected_days = milliseconds_to_add / (1000 * 60 * 60 * 24)
            print(f"Days added: {days_diff} (Expected ~{expected_days})")
        else:
            print(f"Expected: {expected}")
        
        # Check if format is preserved
        if isinstance(original_value, str) and isinstance(masked_value, str):
            format_preserved = (
                ("T" in original_value and "T" in masked_value) or
                ("-" in original_value and "-" in masked_value and "T" not in original_value) or
                ("/" in original_value and "/" in masked_value)
            )
            print(f"Format preserved: {format_preserved}")
            
            # Specifically for ISO format
            if "T" in original_value and ".000Z" in original_value:
                print(f"ISO format with Z suffix preserved: {'.000Z' in masked_value}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_dob_masking()
