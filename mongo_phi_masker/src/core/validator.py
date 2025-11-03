"""
Data validation module for PHI masking pipeline.

This module provides validation capabilities for masked MongoDB documents.
"""

import logging
import re
from typing import Any


class MaskingValidator:
    """Validates masked documents to ensure PHI removal."""

    def __init__(
        self,
        fields_to_validate: list[str] = None,
        patterns_to_detect: dict[str, str] = None,
        logger: logging.Logger = None,
    ):
        """Initialize the masking validator.

        Args:
            fields_to_validate: List of field names to validate
            patterns_to_detect: Dictionary of patterns to detect (name -> regex)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.fields_to_validate = set(fields_to_validate or [])

        # Compile regex patterns for detection
        self.patterns = {}
        if patterns_to_detect:
            for name, pattern in patterns_to_detect.items():
                try:
                    self.patterns[name] = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    self.logger.error(f"Invalid regex pattern '{name}': {str(e)}")

    def validate_document(
        self, masked_doc: dict[str, Any], original_doc: dict[str, Any] = None
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Validate a masked document.

        Args:
            masked_doc: The masked document to validate
            original_doc: Optional original document for comparison

        Returns:
            Tuple of (is_valid, list of validation issues)
        """
        if not masked_doc:
            return False, [{"field": None, "issue": "Empty document"}]

        issues = []

        # Check if masked document has the same structure as original
        if original_doc:
            structure_issues = self._validate_structure(masked_doc, original_doc)
            issues.extend(structure_issues)

        # Check specific fields that should be masked
        field_issues = self._validate_fields(masked_doc)
        issues.extend(field_issues)

        # Check for pattern-based PHI
        pattern_issues = self._validate_patterns(masked_doc)
        issues.extend(pattern_issues)

        is_valid = len(issues) == 0
        return is_valid, issues

    def _validate_structure(
        self, masked_doc: dict[str, Any], original_doc: dict[str, Any], path: str = ""
    ) -> list[dict[str, Any]]:
        """Validate that masked document has the same structure as original.

        Args:
            masked_doc: The masked document
            original_doc: The original document
            path: Current path in the document (for nested fields)

        Returns:
            List of structure validation issues
        """
        issues = []

        # Check if masked document has all fields from original
        for key in original_doc:
            current_path = f"{path}.{key}" if path else key

            if key not in masked_doc:
                issues.append({"field": current_path, "issue": "Field missing in masked document"})
                continue

            # Recursively validate nested documents
            if isinstance(original_doc[key], dict) and isinstance(masked_doc[key], dict):
                nested_issues = self._validate_structure(masked_doc[key], original_doc[key], current_path)
                issues.extend(nested_issues)

            # Validate lists (check length and type)
            elif isinstance(original_doc[key], list) and isinstance(masked_doc[key], list):
                if len(original_doc[key]) != len(masked_doc[key]):
                    issues.append({"field": current_path, "issue": "List length mismatch"})

        # Check if masked document has extra fields
        for key in masked_doc:
            current_path = f"{path}.{key}" if path else key

            if key not in original_doc and not key.startswith("_"):
                issues.append({"field": current_path, "issue": "Extra field in masked document"})

        return issues

    def _validate_fields(self, doc: dict[str, Any], path: str = "") -> list[dict[str, Any]]:
        """Validate fields that require masking.

        Args:
            doc: The document to validate
            path: Current path in the document

        Returns:
            List of field validation issues
        """
        issues = []

        for key, value in doc.items():
            current_path = f"{path}.{key}" if path else key

            # Check if this field should be validated
            if current_path in self.fields_to_validate or key in self.fields_to_validate:
                # Validate string fields aren't unchanged from common PHI values
                if isinstance(value, str):
                    if self._is_potential_phi(value):
                        issues.append(
                            {"field": current_path, "issue": "Field may contain unmasked PHI", "value": value}
                        )

            # Recursively validate nested documents
            if isinstance(value, dict):
                nested_issues = self._validate_fields(value, current_path)
                issues.extend(nested_issues)

            # Validate items in lists
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_path = f"{current_path}[{i}]"
                        nested_issues = self._validate_fields(item, item_path)
                        issues.extend(nested_issues)

        return issues

    def _validate_patterns(self, doc: dict[str, Any], path: str = "") -> list[dict[str, Any]]:
        """Validate document doesn't contain pattern-based PHI.

        Args:
            doc: The document to validate
            path: Current path in the document

        Returns:
            List of pattern validation issues
        """
        issues = []

        for key, value in doc.items():
            current_path = f"{path}.{key}" if path else key

            # Check string values against regex patterns
            if isinstance(value, str):
                for pattern_name, pattern in self.patterns.items():
                    if pattern.search(value):
                        issues.append(
                            {
                                "field": current_path,
                                "issue": f"Field contains pattern '{pattern_name}'",
                                "pattern": pattern_name,
                                "value": value,
                            }
                        )

            # Recursively validate nested documents
            if isinstance(value, dict):
                nested_issues = self._validate_patterns(value, current_path)
                issues.extend(nested_issues)

            # Validate items in lists
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_path = f"{current_path}[{i}]"
                        nested_issues = self._validate_patterns(item, item_path)
                        issues.extend(nested_issues)
                    elif isinstance(item, str):
                        item_path = f"{current_path}[{i}]"
                        for pattern_name, pattern in self.patterns.items():
                            if pattern.search(item):
                                issues.append(
                                    {
                                        "field": item_path,
                                        "issue": f"Field contains pattern '{pattern_name}'",
                                        "pattern": pattern_name,
                                        "value": item,
                                    }
                                )

        return issues

    def _is_potential_phi(self, value: str) -> bool:
        """Check if a string value appears to be potential PHI.

        Args:
            value: String value to check

        Returns:
            True if the value appears to be potential PHI
        """
        # Skip empty values and common replacements
        if not value or value.strip() == "" or value == "xxxxxxxxxx":
            return False

        # Simple heuristics for PHI detection

        # Email pattern
        if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", value):
            return True

        # Phone number pattern (various formats)
        if re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", value):
            return True

        # SSN pattern
        if re.search(r"\d{3}-\d{2}-\d{4}", value):
            return True

        # Address-like pattern (number followed by text)
        if re.search(r"\d+\s+[A-Za-z]+", value):
            return True

        # Dates (various formats)
        if re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", value):
            return True

        return False


class ValidationProcessor:
    """Manages document validation workflow."""

    def __init__(
        self, fields_to_validate: list[str] = None, pattern_definitions_path: str = None, logger: logging.Logger = None
    ):
        """Initialize the validation processor.

        Args:
            fields_to_validate: List of fields that must be masked
            pattern_definitions_path: Path to pattern definitions file
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.fields_to_validate = fields_to_validate or []

        # Load patterns from file if specified
        self.patterns = {}
        if pattern_definitions_path:
            self._load_patterns(pattern_definitions_path)
        else:
            # Default patterns for common PHI
            self.patterns = {
                "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                "phone": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                "ssn": r"\d{3}-\d{2}-\d{4}",
                "address": r"\d+\s+[A-Za-z]+\s+[A-Za-z]+",
                "date": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            }

        # Create validator
        self.validator = MaskingValidator(
            fields_to_validate=self.fields_to_validate, patterns_to_detect=self.patterns, logger=self.logger
        )

    def _load_patterns(self, pattern_file_path: str) -> None:
        """Load pattern definitions from file.

        Args:
            pattern_file_path: Path to pattern definitions file
        """
        import json

        try:
            with open(pattern_file_path) as f:
                patterns_data = json.load(f)

                if isinstance(patterns_data, dict):
                    self.patterns = patterns_data
                elif isinstance(patterns_data, list):
                    # Handle list format [{"name": "...", "pattern": "..."}]
                    self.patterns = {item["name"]: item["pattern"] for item in patterns_data}

                self.logger.info(f"Loaded {len(self.patterns)} pattern definitions")
        except Exception as e:
            self.logger.error(f"Error loading pattern definitions: {str(e)}")
            # Fall back to empty patterns
            self.patterns = {}

    def validate_document(
        self, masked_doc: dict[str, Any], original_doc: dict[str, Any] = None
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Validate a masked document.

        Args:
            masked_doc: Masked document to validate
            original_doc: Optional original document for comparison

        Returns:
            Tuple of (is_valid, list of validation issues)
        """
        return self.validator.validate_document(masked_doc, original_doc)

    def validate_batch(
        self, masked_docs: list[dict[str, Any]], original_docs: list[dict[str, Any]] = None
    ) -> tuple[list[bool], list[list[dict[str, Any]]]]:
        """Validate a batch of masked documents.

        Args:
            masked_docs: List of masked documents to validate
            original_docs: Optional list of original documents for comparison

        Returns:
            Tuple of (list of validation results, list of validation issues)
        """
        results = []
        all_issues = []

        for i, masked_doc in enumerate(masked_docs):
            original_doc = original_docs[i] if original_docs and i < len(original_docs) else None
            is_valid, issues = self.validate_document(masked_doc, original_doc)

            results.append(is_valid)
            all_issues.append(issues)

        return results, all_issues
