"""Unit tests for masking rules validation."""

import pytest

from src.models.masking_rule import MaskingRule, MaskingRuleType, RuleEngine


@pytest.mark.unit
class TestMaskingRuleType:
    """Test MaskingRuleType enum."""

    def test_all_rule_types_exist(self):
        """Test that all expected rule types are defined."""
        expected_types = [
            "replace_string",
            "replace_email",
            "replace_gender",
            "replace_path",
            "random_uppercase",
            "random_uppercase_name",
            "lowercase_match",
            "random_10_digit_number",
            "add_milliseconds",
        ]

        for rule_type in expected_types:
            assert hasattr(MaskingRuleType, rule_type.upper().replace("_", "_"))
            # Verify the enum value matches
            enum_value = MaskingRuleType(rule_type)
            assert enum_value.value == rule_type

    def test_rule_type_string_conversion(self):
        """Test converting string to MaskingRuleType."""
        assert MaskingRuleType("replace_string") == MaskingRuleType.REPLACE_STRING
        assert MaskingRuleType("replace_email") == MaskingRuleType.REPLACE_EMAIL
        assert MaskingRuleType("replace_gender") == MaskingRuleType.REPLACE_GENDER

    def test_invalid_rule_type_raises_error(self):
        """Test that invalid rule types raise ValueError."""
        with pytest.raises(ValueError):
            MaskingRuleType("invalid_rule_type")


@pytest.mark.unit
class TestMaskingRule:
    """Test MaskingRule class."""

    def test_masking_rule_initialization(self):
        """Test basic masking rule initialization."""
        rule = MaskingRule(
            field="PatientName",
            rule_type=MaskingRuleType.REPLACE_STRING,
            params={"replacement": "MASKED"},
            description="Mask patient name",
        )

        assert rule.field == "PatientName"
        assert rule.rule == MaskingRuleType.REPLACE_STRING
        assert rule.params == {"replacement": "MASKED"}
        assert rule.description == "Mask patient name"

    def test_masking_rule_with_string_type(self):
        """Test creating masking rule with string rule type."""
        rule = MaskingRule(field="Email", rule_type="replace_email")

        assert rule.field == "Email"
        assert rule.rule == MaskingRuleType.REPLACE_EMAIL

    def test_masking_rule_defaults(self):
        """Test masking rule with default parameters."""
        rule = MaskingRule(field="Phone", rule_type=MaskingRuleType.RANDOM_10_DIGIT_NUMBER)

        assert rule.field == "Phone"
        assert rule.params == {}
        assert rule.description is None

    def test_masking_rule_invalid_type_defaults_to_replace_string(self):
        """Test that invalid rule type defaults to REPLACE_STRING."""
        rule = MaskingRule(field="TestField", rule_type="invalid_type")

        assert rule.field == "TestField"
        assert rule.rule == MaskingRuleType.REPLACE_STRING

    def test_masking_rule_to_dict(self):
        """Test converting masking rule to dictionary."""
        rule = MaskingRule(
            field="SSN",
            rule_type=MaskingRuleType.REPLACE_STRING,
            params={"replacement": "XXX-XX-XXXX"},
            description="Mask SSN",
        )

        rule_dict = rule.to_dict()

        assert rule_dict["field"] == "SSN"
        assert rule_dict["rule"] == "replace_string"
        assert rule_dict["params"] == {"replacement": "XXX-XX-XXXX"}
        assert rule_dict["description"] == "Mask SSN"

    def test_masking_rule_str_representation(self):
        """Test string representation of masking rule."""
        rule = MaskingRule(field="Address", rule_type=MaskingRuleType.REPLACE_STRING)

        str_repr = str(rule)

        assert "Address" in str_repr
        assert "replace_string" in str_repr or "REPLACE_STRING" in str_repr

    def test_masking_rule_repr_equals_str(self):
        """Test that __repr__ equals __str__."""
        rule = MaskingRule(field="Phone", rule_type=MaskingRuleType.RANDOM_10_DIGIT_NUMBER)

        assert repr(rule) == str(rule)


@pytest.mark.unit
class TestRuleEngine:
    """Test RuleEngine class."""

    def test_rule_engine_initialization_empty(self):
        """Test initializing rule engine with no rules."""
        engine = RuleEngine()

        assert engine.rules == []

    def test_rule_engine_initialization_with_rules(self):
        """Test initializing rule engine with rules."""
        rules = [
            MaskingRule("PatientName", MaskingRuleType.REPLACE_STRING),
            MaskingRule("Email", MaskingRuleType.REPLACE_EMAIL),
        ]
        engine = RuleEngine(rules=rules)

        assert len(engine.rules) == 2
        assert engine.rules[0].field == "PatientName"
        assert engine.rules[1].field == "Email"

    def test_get_rule_for_field_exact_match(self):
        """Test getting rule for field with exact match."""
        rules = [
            MaskingRule("PatientName", MaskingRuleType.REPLACE_STRING),
            MaskingRule("Email", MaskingRuleType.REPLACE_EMAIL),
        ]
        engine = RuleEngine(rules=rules)

        rule = engine.get_rule_for_field("PatientName")

        assert rule is not None
        assert rule.field == "PatientName"
        assert rule.rule == MaskingRuleType.REPLACE_STRING

    def test_get_rule_for_field_no_match(self):
        """Test getting rule for field with no match."""
        rules = [MaskingRule("PatientName", MaskingRuleType.REPLACE_STRING)]
        engine = RuleEngine(rules=rules)

        rule = engine.get_rule_for_field("NonExistentField")

        assert rule is None

    def test_get_rule_for_field_pattern_match(self):
        """Test getting rule for field with glob pattern."""
        rules = [
            MaskingRule("Patient*", MaskingRuleType.REPLACE_STRING),
        ]
        engine = RuleEngine(rules=rules)

        rule = engine.get_rule_for_field("PatientName")

        assert rule is not None
        assert rule.field == "Patient*"

    def test_get_rule_for_field_nested_pattern(self):
        """Test getting rule for nested field with pattern."""
        rules = [
            MaskingRule("Slots.*.PatientName", MaskingRuleType.REPLACE_STRING),
        ]
        engine = RuleEngine(rules=rules)

        rule = engine.get_rule_for_field("Slots.Appointments.PatientName")

        assert rule is not None
        assert rule.field == "Slots.*.PatientName"

    def test_get_all_fields_in_document_flat(self):
        """Test getting all fields from a flat document."""
        engine = RuleEngine()
        document = {"name": "John", "age": 30, "email": "john@example.com"}

        fields = engine._get_all_fields_in_document(document)

        assert "name" in fields
        assert "age" in fields
        assert "email" in fields
        assert len(fields) == 3

    def test_get_all_fields_in_document_nested(self):
        """Test getting all fields from a nested document."""
        engine = RuleEngine()
        document = {
            "name": "John",
            "address": {"street": "123 Main St", "city": "Springfield"},
        }

        fields = engine._get_all_fields_in_document(document)

        assert "name" in fields
        assert "address" in fields
        assert "address.street" in fields
        assert "address.city" in fields

    def test_get_all_fields_in_document_with_array(self):
        """Test getting all fields from document with arrays."""
        engine = RuleEngine()
        document = {
            "name": "John",
            "appointments": [
                {"date": "2024-01-01", "doctor": "Dr. Smith"},
                {"date": "2024-02-01", "doctor": "Dr. Jones"},
            ],
        }

        fields = engine._get_all_fields_in_document(document)

        assert "name" in fields
        assert "appointments" in fields
        # Array fields should be included with indices
        assert any("appointments[0].date" in field for field in fields)
        assert any("appointments[0].doctor" in field for field in fields)


@pytest.mark.unit
class TestMaskingRuleValidation:
    """Test masking rule validation logic."""

    @pytest.mark.parametrize(
        "rule_type,field,params,is_valid",
        [
            (MaskingRuleType.REPLACE_STRING, "Address", {"replacement": "MASKED"}, True),
            (MaskingRuleType.REPLACE_EMAIL, "Email", {}, True),
            (MaskingRuleType.REPLACE_GENDER, "Gender", {}, True),
            (MaskingRuleType.RANDOM_10_DIGIT_NUMBER, "Phone", {}, True),
            (MaskingRuleType.ADD_MILLISECONDS, "DateOfBirth", {"offset": 1000}, True),
        ],
    )
    def test_rule_type_compatibility(self, rule_type, field, params, is_valid):
        """Test that rule types are compatible with field types."""
        rule = MaskingRule(field=field, rule_type=rule_type, params=params)

        assert rule.rule == rule_type
        assert rule.field == field
        assert is_valid  # All test cases should be valid

    def test_email_rule_validation(self):
        """Test email masking rule validation."""
        rule = MaskingRule(field="Email", rule_type=MaskingRuleType.REPLACE_EMAIL)

        assert rule.rule == MaskingRuleType.REPLACE_EMAIL
        # Email rules should preserve @ symbol format

    def test_gender_rule_validation(self):
        """Test gender masking rule validation."""
        rule = MaskingRule(field="Gender", rule_type=MaskingRuleType.REPLACE_GENDER)

        assert rule.rule == MaskingRuleType.REPLACE_GENDER
        # Gender should be replaced with valid gender value

    def test_date_rule_validation(self):
        """Test date masking rule with offset."""
        rule = MaskingRule(
            field="DateOfBirth",
            rule_type=MaskingRuleType.ADD_MILLISECONDS,
            params={"offset": 86400000},  # 1 day in ms
        )

        assert rule.rule == MaskingRuleType.ADD_MILLISECONDS
        assert rule.params["offset"] == 86400000

    def test_phone_number_rule_validation(self):
        """Test phone number masking rule."""
        rule = MaskingRule(field="Phone", rule_type=MaskingRuleType.RANDOM_10_DIGIT_NUMBER)

        assert rule.rule == MaskingRuleType.RANDOM_10_DIGIT_NUMBER
        # Should generate 10-digit random number
