"""Smoke tests for appointment_comparison package."""


def test_imports():
    """Test that all modules can be imported."""
    from appointment_comparison.csv_handler import parse_date
    from appointment_comparison.field_comparator import FieldComparator
    from appointment_comparison.mongo_matcher import MongoMatcher
    from appointment_comparison.validator import AppointmentValidator

    assert parse_date is not None
    assert FieldComparator is not None
    assert MongoMatcher is not None
    assert AppointmentValidator is not None


def test_csv_handler_parse_date():
    """Test date parsing."""
    from appointment_comparison.csv_handler import parse_date

    # Valid dates
    dt = parse_date("10/27/25")
    assert dt is not None
    assert dt.year == 2025
    assert dt.month == 10
    assert dt.day == 27

    dt = parse_date("1/5/26")
    assert dt is not None
    assert dt.year == 2026

    # Invalid dates
    dt = parse_date("")
    assert dt is None

    dt = parse_date("invalid")
    assert dt is None


def test_field_comparator_patient_ref():
    """Test PatientRef comparison."""
    from appointment_comparison.field_comparator import FieldComparator

    comparator = FieldComparator()

    # Match
    assert comparator.compare_patient_ref("2565003", 2565003) is True
    assert comparator.compare_patient_ref("2565003", 2565003.0) is True

    # Mismatch
    assert comparator.compare_patient_ref("2565003", 2565004) is False
    assert comparator.compare_patient_ref("", 2565003) is False


def test_field_comparator_visit_type():
    """Test VisitTypeValue comparison."""
    from appointment_comparison.field_comparator import FieldComparator

    comparator = FieldComparator(case_sensitive_visit_type=False)

    # Case-insensitive match
    assert comparator.compare_visit_type("Palliative Management", "palliative management") is True
    assert comparator.compare_visit_type("Maintenance Visit", "MAINTENANCE VISIT") is True

    # Mismatch
    assert comparator.compare_visit_type("Palliative Management", "Maintenance Visit") is False


def test_smoke():
    """Basic smoke test."""
    assert True
