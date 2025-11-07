#!/usr/bin/env python3
"""
Test Fax Field Masking Rules

This script tests the masking rules specifically for the 11 new fax field types
without requiring an actual database connection.
"""

import logging
import os
import sys

# Add the project directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fax_masking_test")

# Targeted fax fields to be masked
FAX_FIELDS = [
    "Fax",
    "Fax2",
    "MRRFax",
    "FaxNumber",
    "FaxNumber2",
    "MRRFaxNumber",
    "PrimaryFaxNumber",
    "SecondaryFaxNumber",
    "PCPFaxNumber",
    "PCPMRRFaxNumber",
    "PcpSecondaryFaxNumber",
]

# Sample fax values to test with
SAMPLE_FAX_VALUES = [
    "1234567890",
    "123-456-7890",
    "123.456.7890",
    "(123) 456-7890",
    "123 456 7890",
    "+1 123 456 7890",
    "12345678901",
    "1234567890123",
    "555-555-5555",
]


def create_test_documents():
    """Create sample documents with fax fields for testing."""
    test_documents = []

    # Generate documents with different combinations of fax fields
    for i in range(3):
        doc = {
            "_id": f"test_doc_{i}",
            "PatientId": f"PT{10000 + i}",
            "Name": f"Test Patient {i}",
        }

        # Add a subset of fax fields to each document
        for j, field in enumerate(FAX_FIELDS):
            if j % 3 == i % 3:  # Distribute fields across documents
                doc[field] = SAMPLE_FAX_VALUES[j % len(SAMPLE_FAX_VALUES)]

        test_documents.append(doc)

    # Add a document with all fax fields
    all_fields_doc = {"_id": "test_doc_all_fields", "PatientId": "PT99999", "Name": "Test Patient All Fields"}

    for i, field in enumerate(FAX_FIELDS):
        all_fields_doc[field] = SAMPLE_FAX_VALUES[i % len(SAMPLE_FAX_VALUES)]

    test_documents.append(all_fields_doc)

    return test_documents


def get_masking_rule_for_fax_fields():
    """Create a masking rule for fax fields."""
    from src.models.masking_rule import MaskingRule

    # Create a constant replacement rule for fax fields
    rules = []
    for field in FAX_FIELDS:
        rule = MaskingRule(
            field=field,
            rule_type="constant_replacement",
            params={"replacement_value": "1111111111111"},
            description=f"Replace {field} with constant value",
        )
        rules.append(rule)

    return rules


def test_fax_field_masking():
    """Test the masking rules for fax fields."""
    from src.models.masking_rule import RuleEngine

    logger.info("====== Testing Fax Field Masking ======")

    # Create test documents
    documents = create_test_documents()
    logger.info(f"Created {len(documents)} test documents")

    # Get masking rules for fax fields
    rules = get_masking_rule_for_fax_fields()
    logger.info(f"Created masking rules for {len(FAX_FIELDS)} fax fields")

    # Create rule engine
    rule_engine = RuleEngine(rules)

    # Track results
    success_count = 0
    failure_count = 0
    tested_fields = set()

    # Test each document
    for idx, doc in enumerate(documents):
        logger.info(f"Testing document {idx+1}/{len(documents)}")

        # Find fax fields in this document
        doc_fax_fields = [field for field in FAX_FIELDS if field in doc]

        if not doc_fax_fields:
            logger.warning(f"Document {idx+1} has no fax fields, skipping")
            continue

        logger.info(f"Document has {len(doc_fax_fields)} fax fields: {', '.join(doc_fax_fields)}")

        # Apply masking
        masked_doc = rule_engine.apply_rules(doc)

        # Verify masking results
        for field in doc_fax_fields:
            tested_fields.add(field)
            orig_value = doc[field]
            masked_value = masked_doc[field]

            logger.info(f"Field: {field}")
            logger.info(f"  Original: {orig_value}")
            logger.info(f"  Masked: {masked_value}")

            # Check if correctly masked
            if masked_value == "1111111111111":
                logger.info("  ✓ Correctly masked")
                success_count += 1
            else:
                logger.error("  ✗ Incorrectly masked")
                failure_count += 1

    # Summarize results
    logger.info("===== Test Results =====")
    logger.info(f"Tested {len(tested_fields)}/{len(FAX_FIELDS)} unique fax fields")
    logger.info(f"Successfully masked: {success_count}")
    logger.info(f"Failed to mask: {failure_count}")

    # Check for untested fields
    untested_fields = set(FAX_FIELDS) - tested_fields
    if untested_fields:
        logger.warning(f"These fax fields were not tested: {', '.join(untested_fields)}")

    return failure_count == 0


def main():
    """Main entry point for the script."""
    try:
        success = test_fax_field_masking()

        if success:
            logger.info("All fax field masking tests passed!")
            return 0
        else:
            logger.error("Some fax field masking tests failed")
            return 1

    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
