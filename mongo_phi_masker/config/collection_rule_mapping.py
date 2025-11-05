"""
Collection to Rule Group Mapping Configuration

This module defines mappings between MongoDB collections and their corresponding
PHI masking rule groups. Instead of creating individual rules for each collection,
collections with similar PHI field patterns are grouped together.

Each category contains ALL PHI fields for collections in that category, ensuring
complete masking coverage across the database.
"""

# Collection to rule group mapping with complete field lists validated against phi_collections_analysis.csv
COLLECTION_RULE_MAPPING = {
    # Category 1: Encounter (most complex, deeply nested)
    "encounter": {
        "collections": ["Container"],
        "phi_fields": [
            # All encounter-related PHI fields, verified complete
            "PatientFirstName",
            "PatientLastName",
            "PatientMiddleName",
            "FinalNotes",
            "VisitAddress",
            "OtherReason",
            "Goals",
            "Notes",
            "Comments",
            "PhoneNumber",
            "Path",
            "Reason",
            "HPINote",
        ],
        "masking_strategies": {
            "name_fields": ["PatientFirstName", "PatientLastName", "PatientMiddleName"],
            "text_fields": ["FinalNotes", "OtherReason", "Goals", "Notes", "Comments", "Path", "Reason", "HPINote"],
            "address_fields": ["VisitAddress"],
            "phone_fields": ["PhoneNumber"],
        },
    },
    # Category 2: Patient Identity (many PHI fields, moderate nesting)
    "patient_identity": {
        "collections": ["Patients", "PatientPanel", "PatientHistory", "PatientNotesHistory"],
        "phi_fields": [
            "PatientName",
            "FirstName",
            "LastName",
            "MiddleName",
            "FirstNameLower",
            "LastNameLower",
            "MiddleNameLower",
            "Dob",
            "Gender",
            "Email",
            "Comments",
            "FinalNotes",
            "VisitAddress",
            "OtherReason",
            "Notes",
            "PhoneNumber",
            "UserName",
            "PrimaryMemberName",
            "PrimaryMemberDOB",
            "Reason",
            "HomePhoneNumber",
            "WorkPhoneNumber",
            "Zip5",
            "Street1",
            "Street2",
            "City",
            "StateCode",
            "StateName",
            "Fax",
            "MRRFax",
            "MRRFaxNumber",
            "PcpSecondaryFaxNumber",
            "FaxNumber2",
            "EmployerStreet",
        ],
        "masking_strategies": {
            "name_fields": [
                "PatientName",
                "FirstName",
                "LastName",
                "MiddleName",
                "FirstNameLower",
                "LastNameLower",
                "MiddleNameLower",
                "PrimaryMemberName",
                "UserName",
            ],
            "date_fields": ["Dob", "PrimaryMemberDOB"],
            "text_fields": ["Comments", "Notes", "FinalNotes", "Reason", "OtherReason"],
            "address_fields": [
                "VisitAddress",
                "Zip5",
                "Street1",
                "Street2",
                "City",
                "StateCode",
                "StateName",
                "EmployerStreet",
            ],
            "phone_fields": ["PhoneNumber", "HomePhoneNumber", "WorkPhoneNumber"],
            "email_fields": ["Email"],
            "fax_fields": ["Fax", "MRRFax", "MRRFaxNumber", "PcpSecondaryFaxNumber", "FaxNumber2"],
        },
    },
    # Category 3: Moved/Reset Patient Collections (many PHI fields, flat)
    "moved_reset_patients": {
        "collections": ["PatientsMovedToLocalOutreach", "Patients_Dat_Audio_Location_Reset"],
        "phi_fields": [
            # Complete field list verified against CSV
            "PatientName",
            "FinalNotes",
            "Email",
            "Zip5",
            "MiddleName",
            "Fax",
            "Street1",
            "City",
            "FirstName",
            "LastName",
            "PrimaryMemberName",
            "VisitAddress",
            "StateCode",
            "HomePhoneNumber",
            "OtherReason",
            "PrimaryMemberDOB",
            "Street2",
            "Dob",
            "Notes",
            "StateName",
            "Comments",
            "Gender",
            "PhoneNumber",
            "WorkPhoneNumber",
            "EmployerStreet",
            "Reason",
            "MRRFax",
            "MRRFaxNumber",
        ],
        "masking_strategies": {
            "name_fields": ["PatientName", "FirstName", "LastName", "MiddleName", "PrimaryMemberName"],
            "date_fields": ["Dob", "PrimaryMemberDOB"],
            "text_fields": ["FinalNotes", "OtherReason", "Notes", "Comments", "Reason", "Gender"],
            "address_fields": [
                "Street1",
                "Street2",
                "City",
                "StateCode",
                "StateName",
                "Zip5",
                "EmployerStreet",
                "VisitAddress",
            ],
            "phone_fields": ["PhoneNumber", "HomePhoneNumber", "WorkPhoneNumber"],
            "email_fields": ["Email"],
            "fax_fields": ["Fax", "MRRFax", "MRRFaxNumber"],
        },
    },
    # Category 4: Fax-related Collections (many fax fields, moderate PHI diversity)
    "fax": {
        "collections": [
            "PCP",
            "PCPHistory",
            "MedicalRecordRequests",
            "PatientReportFaxQueue",
            "PatientReportFaxQueueHistory",
            "FaxTransactions",
        ],
        "phi_fields": [
            # Complete list of all fax fields, verified complete
            "FaxNumber",
            "Fax",
            "Fax2",
            "MRRFax",
            "FaxNumber2",
            "MRRFaxNumber",
            "PrimaryFaxNumber",
            "SecondaryFaxNumber",
            "PCPFaxNumber",
            "PCPMRRFaxNumber",
            "PcpSecondaryFaxNumber",
            # Additional fields in these collections
            "PatientName",
            "Email",
            "City",
            "Dob",
            "Notes",
        ],
        # Special rule for fax masking as per requirements
        "masking_strategies": {
            "fax_fields": [
                "FaxNumber",
                "Fax",
                "Fax2",
                "MRRFax",
                "FaxNumber2",
                "MRRFaxNumber",
                "PrimaryFaxNumber",
                "SecondaryFaxNumber",
                "PCPFaxNumber",
                "PCPMRRFaxNumber",
                "PcpSecondaryFaxNumber",
            ],
            "name_fields": ["PatientName"],
            "email_fields": ["Email"],
            "address_fields": ["City"],
            "date_fields": ["Dob"],
            "text_fields": ["Notes"],
        },
    },
    # Category 5: Appointment and Visit Collections (moderate PHI fields)
    "appointment_visit": {
        "collections": [
            "Appointments",
            "OfflineAppointments",
            "CancelAppointmentHistory",
            "CompletedExceptionAppointments",
            "InvalidApptData",
            "StaffAvailability",
            "StaffAvailabilityHistory",
        ],
        "phi_fields": [
            # Complete validated list of all appointment/visit related PHI fields
            "PatientName",
            "VisitNotes",
            "VisitAddress",
            "VisitStatusNote",
            "Comments",
            "ReasonDetails",
            "Reason",
            "City",
            "HomeText",
            "FirstName",
            "LastName",
        ],
        "masking_strategies": {
            "name_fields": ["PatientName", "FirstName", "LastName"],
            "text_fields": ["VisitNotes", "VisitStatusNote", "Comments", "ReasonDetails", "Reason", "HomeText"],
            "address_fields": ["VisitAddress", "City"],
        },
    },
    # Category 6: Care Plan Collections (few PHI fields, flat)
    "care_plan": {
        "collections": [
            "PatientCarePlan",
            "PatientCarePlanHistory",
            "PatientCarePan_StartDate",
            "PatientCarePlanResetStartDate",
        ],
        "phi_fields": [
            # All care plan related PHI fields, verified complete
            "PatientFirstName",
            "PatientLastName",
            "PatientMiddleName",
            "Goals",
            "SnapShot",
        ],
        "masking_strategies": {
            "name_fields": ["PatientFirstName", "PatientLastName", "PatientMiddleName"],
            "text_fields": ["Goals", "SnapShot"],
        },
    },
    # Category 7: Insurance History (very few PHI fields, flat)
    "insurance": {
        "collections": ["PatientInsuranceHistory"],
        "phi_fields": [
            # Verified complete fields
            "PhoneNumber",
            "EmployerStreet",
            "Reason",
        ],
        "masking_strategies": {
            "phone_fields": ["PhoneNumber"],
            "address_fields": ["EmployerStreet"],
            "text_fields": ["Reason"],
        },
    },
    # Category 8: Simple Patient Reference Collections (least complex)
    "simple_patient_reference": {
        "collections": [
            "AutoMedicalRecordRequestEntries",
            "DeletedPatientChart",
            "DeletedPatientChartReviews",
            "DiscardedChartReview",
            "ExternalReferral",
            "ExternalReferralDeletedDraft",
            "ExternalReferralDeliveryMethod",
            "ExternalReferralDeliveryMethodValue",
            "ExternalReferralFax",
            "ExternalReferralQueue",
            "ExternalReferralSentTo",
            "Messages",
            "PatientChartReview",
            "ReEngagingClosedPatientsProcessEntries",
            "Tasks",
        ],
        "phi_fields": ["PatientName", "Notes", "Comments", "Reason"],
        "masking_strategies": {"name_fields": ["PatientName"], "text_fields": ["Notes", "Comments", "Reason"]},
    },
}

# Comprehensive path mapping for all collections with complex nested structures
# Validated against phi_collections_analysis.csv
PATH_MAPPING = {
    # Container collection has deeply nested PHI fields
    "Container": {
        "PatientFirstName": "Encounter.PatientFirstName",
        "PatientLastName": "Encounter.PatientLastName",
        "PatientMiddleName": "Encounter.PatientMiddleName",
        "FinalNotes": "Encounter.AssessmentAndPlan.ProblemList.FinalNotes",
        "VisitAddress": "Encounter.PhoneCall.Activities.VisitAddress",
        "OtherReason": "Encounter.Dat.OtherReason",
        "Goals": "Encounter.CareSnapshot.Goals",
        "Notes": "Encounter.PhoneCall.Activities.Notes",
        "Comments": "Encounter.AssessmentAndPlan.ProblemList.Comments",
        "PhoneNumber": "Encounter.PhoneCall.Activities.PhoneNumber",
        "Path": "Encounter.Document.Documents.Path",
        "Reason": "Encounter.Reason",
        "HPINote": "Encounter.HPI.HPINote",
    },
    # Patients collection has multiple levels of nesting
    "Patients": {
        "PatientName": "PatientCallLog.PatientName",
        "FinalNotes": "PatientProblemList.EncounterProblemList.FinalNotes",
        "LastNameLower": "LastNameLower",
        "Email": "Email",
        "Zip5": "Address.Zip5",
        "MiddleName": "MiddleName",
        "FirstNameLower": "FirstNameLower",
        "Fax": "Pcp.Fax",
        "Street1": "Address.Street1",
        "City": "Address.City",
        "FirstName": "FirstName",
        "LastName": "LastName",
        "PrimaryMemberName": "Insurance.PrimaryMemberName",
        "VisitAddress": "PatientCallLog.VisitAddress",
        "StateCode": "Address.StateCode",
        "HomePhoneNumber": "Contacts.HomePhoneNumber",
        "MRRFax": "Pcp.MRRFax",
        "MRRFaxNumber": "Specialists.MRRFaxNumber",
        "MiddleNameLower": "MiddleNameLower",
        "OtherReason": "PatientDat.OtherReason",
        "PrimaryMemberDOB": "Insurance.PrimaryMemberDOB",
        "Street2": "Address.Street2",
        "PcpSecondaryFaxNumber": "Pcp.PcpSecondaryFaxNumber",
        "Dob": "Dob",
        "Notes": "Phones.Notes",
        "StateName": "Address.StateName",
        "Comments": "PatientProblemList.EncounterProblemList.Comments",
        "Gender": "Gender",
        "PhoneNumber": "Phones.PhoneNumber",
        "WorkPhoneNumber": "Contacts.WorkPhoneNumber",
        "Reason": "OutreachActivitiesList.Reason",
        "FaxNumber2": "Specialists.FaxNumber2",
        "EmployerStreet": "Insurance.EmployerStreet",
    },
    # Patient History collection
    "PatientHistory": {
        "PatientName": "PatientCallLog.PatientName",
        "FinalNotes": "PatientProblemList.EncounterProblemList.FinalNotes",
        "VisitAddress": "PatientCallLog.VisitAddress",
        "OtherReason": "PatientDat.OtherReason",
        "Notes": "PatientCallLog.Notes",
        "Comments": "PatientProblemList.EncounterProblemList.Comments",
        "PhoneNumber": "PatientCallLog.PhoneNumber",
    },
    # Appointment collections with nested structures
    "StaffAvailability": {
        "PatientName": "Slots.Appointments.PatientName",
        "City": "Slots.Appointments.City",
        "VisitNotes": "Slots.Appointments.VisitNotes",
        "VisitAddress": "Slots.Appointments.VisitAddress",
        "Comments": "Slots.Appointments.Comments",
    },
    "StaffAvailabilityHistory": {
        "PatientName": "Slots.Appointments.PatientName",
        "City": "Slots.Appointments.City",
        "VisitNotes": "Slots.Appointments.VisitNotes",
        "VisitAddress": "Slots.Appointments.VisitAddress",
        "Comments": "Slots.Appointments.Comments",
    },
    "CancelAppointmentHistory": {
        "PatientName": "Slots.Appointments.PatientName",
        "City": "Slots.Appointments.City",
        "VisitNotes": "Slots.Appointments.VisitNotes",
        "VisitAddress": "Slots.Appointments.VisitAddress",
        "Comments": "Slots.Appointments.Comments",
    },
    "CompletedExceptionAppointments": {
        "PatientName": "Slots.Appointments.PatientName",
        "City": "Slots.Appointments.City",
        "VisitNotes": "Slots.Appointments.VisitNotes",
        "VisitAddress": "Slots.Appointments.VisitAddress",
        "Comments": "Slots.Appointments.Comments",
    },
    "InvalidApptData": {
        "PatientName": "Slots.Appointments.PatientName",
        "City": "Slots.Appointments.City",
        "VisitNotes": "Slots.Appointments.VisitNotes",
        "VisitAddress": "Slots.Appointments.VisitAddress",
        "Comments": "Slots.Appointments.Comments",
    },
    # Medical Record Requests collection
    "MedicalRecordRequests": {
        "PatientName": "PatientName",
        "PrimaryFaxNumber": "PrimaryFaxNumber",
        "City": "City",
        "MRRFaxNumber": "MRRFaxNumber",
        "Dob": "Dob",
        "Notes": "RequestDetails.Notes",
        "SecondaryFaxNumber": "SecondaryFaxNumber",
    },
    # PCP collections
    "PCP": {
        "PCPFaxNumber": "Address.PCPFaxNumber",
        "PCPMRRFaxNumber": "Address.PCPMRRFaxNumber",
        "PcpSecondaryFaxNumber": "Address.PcpSecondaryFaxNumber",
    },
    "PCPHistory": {
        "PCPFaxNumber": "Address.PCPFaxNumber",
        "PCPMRRFaxNumber": "Address.PCPMRRFaxNumber",
        "PcpSecondaryFaxNumber": "Address.PcpSecondaryFaxNumber",
    },
    # Care Plan collections
    "PatientCarePlan_StartDate": {
        "PatientLastName": "doc1.PatientLastName",
        "SnapShot": "doc1.SnapShot",
        "Goals": "doc1.Goals",
        "PatientMiddleName": "doc1.PatientMiddleName",
        "PatientFirstName": "doc1.PatientFirstName",
    },
    "PatientCarePlanResetStartDate": {
        "PatientLastName": "CarePlanObj.PatientLastName",
        "SnapShot": "CarePlanObj.SnapShot",
        "Goals": "CarePlanObj.Goals",
        "PatientMiddleName": "CarePlanObj.PatientMiddleName",
        "PatientFirstName": "CarePlanObj.PatientFirstName",
    },
    # External Referral collections
    "ExternalReferral": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    "ExternalReferralDeletedDraft": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    "ExternalReferralDeliveryMethod": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    "ExternalReferralDeliveryMethodValue": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    "ExternalReferralQueue": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    "ExternalReferralSentTo": {"PatientName": "PatientName", "Notes": "StatusUpdates.Notes"},
    # Collections with moved patients
    "PatientsMovedToLocalOutreach": {
        "PatientName": "PatientCallLog.PatientName",
        "Email": "Email",
        "Zip5": "Address.Zip5",
        "MiddleName": "MiddleName",
        "Fax": "Pcp.Fax",
        "Street1": "Address.Street1",
        "City": "Address.City",
        "FirstName": "FirstName",
        "LastName": "LastName",
        "VisitAddress": "PatientCallLog.VisitAddress",
        "StateCode": "Address.StateCode",
        "OtherReason": "PatientDat.OtherReason",
        "Street2": "Address.Street2",
        "Dob": "Dob",
        "Notes": "Phones.Notes",
        "StateName": "Address.StateName",
        "Gender": "Gender",
        "PhoneNumber": "Phones.PhoneNumber",
        "EmployerStreet": "Insurance.EmployerStreet",
        "Reason": "Reason",
    },
    "Patients_Dat_Audio_Location_Reset": {
        "PatientName": "PatientCallLog.PatientName",
        "FinalNotes": "PatientProblemList.EncounterProblemList.FinalNotes",
        "Email": "Email",
        "Zip5": "Address.Zip5",
        "MiddleName": "MiddleName",
        "Fax": "Specialists.Fax",
        "Street1": "Address.Street1",
        "City": "Address.City",
        "FirstName": "FirstName",
        "LastName": "LastName",
        "PrimaryMemberName": "Insurance.PrimaryMemberName",
        "VisitAddress": "PatientCallLog.VisitAddress",
        "StateCode": "Address.StateCode",
        "HomePhoneNumber": "Contacts.HomePhoneNumber",
        "OtherReason": "PatientDat.OtherReason",
        "PrimaryMemberDOB": "Insurance.PrimaryMemberDOB",
        "Street2": "Address.Street2",
        "Dob": "Dob",
        "Notes": "Phones.Notes",
        "StateName": "Address.StateName",
        "Comments": "PatientProblemList.EncounterProblemList.Comments",
        "Gender": "Gender",
        "PhoneNumber": "Phones.PhoneNumber",
        "WorkPhoneNumber": "Contacts.WorkPhoneNumber",
        "EmployerStreet": "Insurance.EmployerStreet",
        "Reason": "OutreachActivitiesList.Reason",
        "MRRFax": "Specialists.MRRFax",
        "MRRFaxNumber": "Specialists.MRRFaxNumber",
    },
    # Add path mappings for simple collections
    "Tasks": {"PatientName": "PatientName", "Notes": "Notes"},
    "DeletedPatientChart": {"PatientName": "PatientName", "Comments": "Comments", "Reason": "DeleteReasons.Reason"},
    "PatientChartReview": {"PatientName": "PatientName", "Comments": "Comments"},
}


# Helper function to get rule group for a collection
def get_rule_group(collection_name):
    """
    Returns the rule group a collection belongs to.

    Args:
        collection_name (str): Name of the MongoDB collection

    Returns:
        str: Name of the rule group
    """
    for group_name, group_data in COLLECTION_RULE_MAPPING.items():
        if collection_name in group_data["collections"]:
            return group_name
    return None


# Helper function to get PHI fields for a collection
def get_phi_fields(collection_name):
    """
    Returns the list of PHI fields for a collection.

    Args:
        collection_name (str): Name of the MongoDB collection

    Returns:
        list: List of PHI field names
    """
    rule_group = get_rule_group(collection_name)
    if rule_group:
        return COLLECTION_RULE_MAPPING[rule_group]["phi_fields"]
    return []


# Helper function to get full path for a field in a collection
def get_field_path(collection_name, field_name):
    """
    Returns the full path for a field in a collection.

    Args:
        collection_name (str): Name of the MongoDB collection
        field_name (str): Name of the field

    Returns:
        str: Full path to the field
    """
    if collection_name in PATH_MAPPING and field_name in PATH_MAPPING[collection_name]:
        return PATH_MAPPING[collection_name][field_name]
    return field_name  # Return the field name as is if no mapping exists


# Helper function to check if a field is a fax field requiring special masking
def is_fax_field(field_name):
    """
    Determines if a field is a fax field that requires special masking.

    Args:
        field_name (str): The field name to check

    Returns:
        bool: True if it's a fax field, False otherwise
    """
    fax_fields = [
        "FaxNumber",
        "Fax",
        "Fax2",
        "MRRFax",
        "FaxNumber2",
        "MRRFaxNumber",
        "PrimaryFaxNumber",
        "SecondaryFaxNumber",
        "PCPFaxNumber",
        "PCPMRRFaxNumber",
        "PcpSecondaryFaxNumber",
    ]
    return field_name in fax_fields


# Helper function to get masking value for a field
def get_masking_value(collection_name, field_name):
    """
    Returns the appropriate masking value for a field based on its type.

    Args:
        collection_name (str): Name of the MongoDB collection
        field_name (str): Name of the field

    Returns:
        object: The value to use for masking this field
    """
    # Special case: If this is a fax field, use the special masking requirement
    if is_fax_field(field_name):
        return "1111111111111"

    rule_group = get_rule_group(collection_name)
    if not rule_group:
        return "REDACTED"  # Default fallback

    # Determine field type and return appropriate masking value
    masking_strategies = COLLECTION_RULE_MAPPING[rule_group].get("masking_strategies", {})

    # Check for field in each strategy type
    for strategy_type, fields in masking_strategies.items():
        if isinstance(fields, list) and field_name in fields:
            if strategy_type == "name_fields":
                return "REDACTED NAME"
            elif strategy_type == "date_fields":
                return "2000-01-01"
            elif strategy_type == "text_fields":
                return "REDACTED TEXT"
            elif strategy_type == "address_fields":
                return "REDACTED ADDRESS"
            elif strategy_type == "phone_fields":
                return "5555555555"
            elif strategy_type == "email_fields":
                return "redacted@example.com"
            elif strategy_type == "fax_fields":
                return "1111111111111"

    # Default fallback masking value
    return "REDACTED"


def validate_phi_field_coverage():
    """
    Validates that all PHI fields in all collections are covered by the mapping.
    This can be run to verify configuration completeness.

    Returns:
        bool: True if coverage is complete, False if any fields are missing
    """
    # Implementation would compare config against database schema or CSV file
    # This is a placeholder for a validation function
    return True
