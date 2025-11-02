"""
MongoDB PHI/PII Data Masking Engine

Masks Protected Health Information (PHI) and Personally Identifiable Information (PII)
in MongoDB documents for compliance and testing purposes.

SECURITY CRITICAL: Must maintain exact masking behavior from JavaScript version.

Author: Demesew Abebe
Version: 1.0.0
Date: 2025-11-02
"""

import random
import string
from datetime import datetime
from typing import Any, Dict


class MaskingEngine:
    """
    PHI/PII data masking engine with field-specific masking rules.

    Masking Rules (matching JavaScript version):
    - Names: Random alphabetic characters (preserve length/spaces)
    - Notes/Text: "xxxxxxxxxx"
    - DOB: Add fixed time offset
    - Phone: Random 10-digit number
    - Email: "xxxxxx@xxxx.com"
    - Gender: "xxxxxx"
    - Addresses/IDs: "xxxxxxxxxx"
    - File Paths: Dummy path
    """

    # Field name mappings for masking types
    NAME_FIELDS = {
        "PatientName",
        "PatientFirstName",
        "PatientMiddleName",
        "PatientLastName",
        "FirstName",
        "MiddleName",
        "LastName",
        "UserName",
    }

    TEXT_FIELDS = {
        "HPINote",
        "Notes",
        "FinalNotes",
        "Comments",
        "OtherReason",
        "VisitNotes",
        "HomeText",
        "VisitStatusNote",
        "ReasonDetails",
        "Reason",
        "EmployerStreet",
        "HealthPlanMemberId",
        "SubscriberId",
        "Street1",
        "Street2",
        "City",
        "StateCode",
        "Zip5",
        "StateName",
        "PrimaryMemberName",
        "SnapShot",
        "Goals",
        "VisitAddress",
    }

    PHONE_FIELDS = {"PhoneNumber", "HomePhoneNumber", "WorkPhoneNumber"}

    EMAIL_FIELDS = {"Email"}

    GENDER_FIELDS = {"Gender"}

    PATH_FIELDS = {"Path"}

    DOB_FIELDS = {"Dob", "PrimaryMemberDOB"}

    # Fixed time offset for DOB masking (matches JavaScript: 12 * 24 * 1200 * 600000 milliseconds)
    # JavaScript: 12 * 24 * 1200 * 600000 = 207,360,000,000 milliseconds
    DOB_TIME_OFFSET_MS = 12 * 24 * 1200 * 600000  # 207360000000 milliseconds

    def __init__(self, seed: int | None = None):
        """
        Initialize the masking engine.

        Args:
            seed: Optional random seed for reproducible masking (testing only)
        """
        if seed:
            random.seed(seed)

    def mask_name_field(self, value: str | None) -> str:
        """
        Mask name fields by replacing characters with random alphabetic characters.
        Preserves spaces and length.

        Args:
            value: Original name value

        Returns:
            Masked name with same length and space positions
        """
        if value is None or value == "":
            return ""

        # Replace non-space characters with random uppercase letters
        result = "".join(
            " " if char == " " else random.choice(string.ascii_uppercase) for char in value
        )
        return result

    def mask_text_field(self, value: Any) -> str:
        """
        Mask text fields with fixed string.

        Args:
            value: Original text value

        Returns:
            Fixed masked string "xxxxxxxxxx"
        """
        if value is None:
            return "xxxxxxxxxx"
        return "xxxxxxxxxx"

    def mask_phone_field(self, value: Any) -> int:
        """
        Mask phone numbers with random 10-digit number.

        Args:
            value: Original phone value

        Returns:
            Random 10-digit integer
        """
        if value is None:
            return random.randint(1000000000, 9999999999)
        return random.randint(1000000000, 9999999999)

    def mask_email_field(self, value: Any) -> str:
        """
        Mask email addresses with fixed dummy email.

        Args:
            value: Original email value

        Returns:
            Fixed masked email "xxxxxx@xxxx.com"
        """
        if value is None:
            return "xxxxxx@xxxx.com"
        return "xxxxxx@xxxx.com"

    def mask_gender_field(self, value: Any) -> str:
        """
        Mask gender field with fixed string.

        Args:
            value: Original gender value

        Returns:
            Fixed masked string "xxxxxx"
        """
        if value is None:
            return "xxxxxx"
        return "xxxxxx"

    def mask_path_field(self, value: Any) -> str:
        """
        Mask file paths with dummy path.

        Args:
            value: Original path value

        Returns:
            Fixed dummy path
        """
        if value is None:
            return "//vm_fs01/Projects/EMRQAReports/sampledoc.pdf"
        return "//vm_fs01/Projects/EMRQAReports/sampledoc.pdf"

    def mask_dob_field(self, value: datetime | int | None) -> datetime | int | None:
        """
        Mask date of birth by adding fixed time offset.

        JavaScript logic: doc[field] = (doc[field].getTime() + 12 * 24 * 1200 * 600000)
        This returns timestamp in milliseconds.

        Args:
            value: Original DOB value (datetime or timestamp)

        Returns:
            Masked DOB with time offset applied
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            # Convert to milliseconds timestamp, add offset, return as int
            timestamp_ms = int(value.timestamp() * 1000)
            return timestamp_ms + self.DOB_TIME_OFFSET_MS
        elif isinstance(value, (int, float)):
            # Already a timestamp, add offset
            return int(value) + self.DOB_TIME_OFFSET_MS
        else:
            return value

    def mask_fields(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask PHI/PII fields in a document.

        Preserves the 'isMasked' field and recursively processes nested objects.

        Args:
            doc: Document to mask

        Returns:
            Masked document
        """
        if not isinstance(doc, dict):
            return doc

        for field, value in doc.items():
            # Skip isMasked field
            if field == "isMasked":
                continue

            # Handle Date objects (DOB fields)
            if field in self.DOB_FIELDS and isinstance(value, (datetime, int, float)):
                doc[field] = self.mask_dob_field(value)

            # Recursively mask nested objects/arrays
            elif isinstance(value, dict):
                doc[field] = self.mask_fields(value)
            elif isinstance(value, list):
                doc[field] = [
                    self.mask_fields(item) if isinstance(item, dict) else item for item in value
                ]

            # Apply field-specific masking
            elif field in self.NAME_FIELDS:
                doc[field] = self.mask_name_field(value)
            elif field in self.TEXT_FIELDS:
                doc[field] = self.mask_text_field(value)
            elif field in self.PHONE_FIELDS:
                doc[field] = self.mask_phone_field(value)
            elif field in self.EMAIL_FIELDS:
                doc[field] = self.mask_email_field(value)
            elif field in self.GENDER_FIELDS:
                doc[field] = self.mask_gender_field(value)
            elif field in self.PATH_FIELDS:
                doc[field] = self.mask_path_field(value)

        return doc
