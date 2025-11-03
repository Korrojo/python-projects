#!/usr/bin/env python3
"""
Verification utilities for MongoDB PHI Masking Tool.

This module provides functionality for verifying that PHI data has been
properly masked in MongoDB documents.
"""

import logging
from typing import Dict, Any, List, Optional, Set

from src.core.connector import MongoConnector

# Setup logger
logger = logging.getLogger(__name__)


class MaskingVerifier:
    """Class for verifying masking results.

    This class is responsible for verifying that PHI data has been properly
    masked in MongoDB documents.

    Attributes:
        source_connector: Connector to source MongoDB database
        dest_connector: Connector to destination MongoDB database
        phi_fields: List of field names considered PHI
        non_phi_fields: List of field names not considered PHI
    """

    def __init__(
        self,
        source_connector: MongoConnector,
        dest_connector: MongoConnector,
        phi_fields: Optional[List[str]] = None,
        non_phi_fields: Optional[List[str]] = None,
    ):
        """Initialize the masking verifier.

        Args:
            source_connector: Connector to source MongoDB database
            dest_connector: Connector to destination MongoDB database
            phi_fields: List of field names considered PHI
            non_phi_fields: List of field names not considered PHI
        """
        self.source_connector = source_connector
        self.dest_connector = dest_connector

        # Default PHI fields if not provided
        self.phi_fields = phi_fields or [
            # Basic PHI fields
            "FirstName",
            "LastName",
            "MiddleName",
            "FirstNameLower",
            "LastNameLower",
            "MiddleNameLower",
            "Email",
            "Dob",
            "HealthPlanMemberId",
            # Address fields
            "Address_City",
            "Address_StateCode",
            "Address_StateName",
            "Address_Street1",
            "Address_Street2",
            "Address_Zip5",
            # Phone fields
            "Phones_PhoneNumber",
            "PatientCallLog_PhoneNumber",
            "Insurance_PhoneNumber",
            # Name fields in nested structures
            "DocuSign_UserName",
            "PatientCallLog_PatientName",
            "Insurance_PrimaryMemberName",
            # Notes fields that might contain PHI
            "Allergies_Notes",
            "PatientCallLog_Notes",
            "PatientDat_Notes",
            "Phones_Notes",
            # Visit address
            "PatientCallLog_VisitAddress",
        ]

        # Default non-PHI fields if not provided
        self.non_phi_fields = non_phi_fields or [
            "Gender",
            "SubscriberId",
            "HealthPlanName",
        ]

        logger.debug(
            f"MaskingVerifier initialized with {len(self.phi_fields)} PHI fields"
        )

    def verify_masking(
        self, sample_size: int = 5, log_level: str = "INFO"
    ) -> Dict[str, Any]:
        """Verify that PHI data has been properly masked.

        Args:
            sample_size: Number of documents to sample for verification
            log_level: Logging level for verification

        Returns:
            Verification results dictionary
        """
        set_log_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(set_log_level)

        logger.info("Starting verification process...")

        # Check connection to databases
        self.source_connector.ensure_connected()
        self.dest_connector.ensure_connected()

        # Get document counts
        source_count = self.source_connector.count_documents({})
        dest_count = self.dest_connector.count_documents({})

        logger.info(f"Source count: {source_count}, Masked count: {dest_count}")

        # Check if counts match
        count_match = source_count == dest_count

        # Use a smaller sample size if there are fewer documents
        actual_sample_size = min(sample_size, source_count)

        # Get a sample of source documents
        source_docs = list(
            self.source_connector.find_documents(limit=actual_sample_size)
        )

        # Track verification results
        phi_fields_masked = True
        non_phi_fields_preserved = True

        # Track which fields were successfully masked and which weren't
        masked_fields: Set[str] = set()
        unmasked_fields: Set[str] = set()

        # Verify each document
        for source_doc in source_docs:
            doc_id = source_doc.get("_id")
            logger.info(f"Checking document with ID: {doc_id}")

            # Find corresponding masked document
            masked_doc = self.dest_connector.find_one({"_id": doc_id})

            if not masked_doc:
                logger.warning(f"No masked document found for ID: {doc_id}")
                continue

            logger.info("Found corresponding masked document")

            # Verify PHI fields are masked
            for field in self.phi_fields:
                if field in source_doc:
                    source_value = source_doc.get(field)
                    masked_value = masked_doc.get(field)

                    logger.debug(
                        f"Checking PHI field {field}: Source={source_value}, Masked={masked_value}"
                    )

                    # Skip null values
                    if source_value is None:
                        continue

                    # Check if field was masked
                    field_masked = self._verify_field_masked(
                        field, source_value, masked_value
                    )

                    if field_masked:
                        masked_fields.add(field)
                    else:
                        unmasked_fields.add(field)
                        phi_fields_masked = False

            # Verify non-PHI fields are preserved
            for field in self.non_phi_fields:
                if field in source_doc:
                    source_value = source_doc.get(field)
                    masked_value = masked_doc.get(field)

                    logger.debug(
                        f"Checking non-PHI field {field}: Source={source_value}, Masked={masked_value}"
                    )

                    # Skip null values
                    if source_value is None:
                        continue

                    # Check if values match
                    if self._compare_values(source_value, masked_value) is False:
                        logger.warning(
                            f"Non-PHI field {field} was not preserved: {source_value} != {masked_value}"
                        )
                        non_phi_fields_preserved = False

        # Prepare verification results
        results = {
            "source_count": source_count,
            "masked_count": dest_count,
            "count_match": count_match,
            "phi_fields_masked": phi_fields_masked,
            "non_phi_fields_preserved": non_phi_fields_preserved,
            "masked_fields": list(masked_fields),
            "unmasked_fields": list(unmasked_fields),
        }

        # Log summary
        logger.info(
            f"Successfully masked fields: {', '.join(masked_fields) if masked_fields else 'None'}"
        )
        logger.info(
            f"Fields not properly masked: {', '.join(unmasked_fields) if unmasked_fields else 'None'}"
        )

        logger.info(
            f"Verification results: count_match={count_match}, "
            f"phi_fields_masked={phi_fields_masked}, "
            f"non_phi_fields_preserved={non_phi_fields_preserved}"
        )

        return results

    def _verify_field_masked(
        self, field_name: str, source_value: Any, masked_value: Any
    ) -> bool:
        """Verify that a field was properly masked.

        Args:
            field_name: Name of the field
            source_value: Value in the source document
            masked_value: Value in the masked document

        Returns:
            True if field was properly masked, False otherwise
        """
        # Handle lists (array fields)
        if isinstance(source_value, list) and isinstance(masked_value, list):
            # If lists are different lengths, consider it masked
            if len(source_value) != len(masked_value):
                return True

            # Check each item in the array
            for i, (src_item, masked_item) in enumerate(
                zip(source_value, masked_value)
            ):
                if src_item is None or masked_item is None:
                    continue

                # Handle nested lists
                if isinstance(src_item, list) and isinstance(masked_item, list):
                    for j, (src_subitem, masked_subitem) in enumerate(
                        zip(src_item, masked_item)
                    ):
                        if src_subitem is None or masked_subitem is None:
                            continue

                        if self._compare_values(src_subitem, masked_subitem):
                            logger.warning(
                                f"PHI field {field_name}[{i}][{j}] was not masked: {src_subitem}"
                            )
                            return False
                # Regular array items
                elif self._compare_values(src_item, masked_item):
                    logger.warning(
                        f"PHI field {field_name}[{i}] was not masked: {src_item}"
                    )
                    return False

            return True

        # For all other fields, check if values are different
        if self._compare_values(source_value, masked_value):
            logger.warning(f"PHI field {field_name} was not masked: {source_value}")
            return False

        return True

    def _compare_values(self, value1: Any, value2: Any) -> bool:
        """Compare two values for equality, handling different types.

        Args:
            value1: First value
            value2: Second value

        Returns:
            True if values are equal, False otherwise
        """
        # Handle None values
        if value1 is None or value2 is None:
            return value1 is value2

        # Handle empty strings
        if (isinstance(value1, str) and not value1.strip()) or (
            isinstance(value2, str) and not value2.strip()
        ):
            return (isinstance(value1, str) and not value1.strip()) == (
                isinstance(value2, str) and not value2.strip()
            )

        # Handle different types
        if type(value1) != type(value2):
            return False

        # Handle string comparisons with more flexibility
        if isinstance(value1, str) and isinstance(value2, str):
            # If strings are identical, they are equal
            if value1 == value2:
                return True

            # If one is empty and the other is not, they are not equal
            if not value1.strip() or not value2.strip():
                return False

            # Otherwise, consider them different (which is good for masked fields)
            return False

        # Default comparison
        return value1 == value2
