# Test Data Generation Proposal for Patients Collection

## Executive Summary

This proposal outlines a strategy for generating realistic test data for the Patients collection using the Faker
library, focusing on the 34 identified PHI fields while maintaining a simplified document structure suitable for testing
the mongo_phi_masker.

## PHI Field Analysis

Based on the field check results, 34 PHI fields were identified across 4 main categories:

### 1. Personal Identifiers (9 fields)

- `FirstName`, `MiddleName`, `LastName` (root level)
- `FirstNameLower`, `MiddleNameLower`, `LastNameLower` (derived fields)
- `Email` (root level)
- `Dob` (Date of Birth - root level)
- `Gender` (root level)
- `MedicareId` (root level)

### 2. Contact Information (7 fields)

- `PhoneNumber` (nested: `Phones.PhoneNumber`)
- `HomePhoneNumber` (nested: `Contacts.HomePhoneNumber`)
- `WorkPhoneNumber` (nested: `Contacts.WorkPhoneNumber`)
- `Fax` (nested: `Pcp.Fax`)
- `PcpSecondaryFaxNumber` (nested: `Pcp.PcpSecondaryFaxNumber`)
- `MRRFax` (nested: `Pcp.MRRFax`)
- `MRRFaxNumber` (nested: `Specialists.MRRFaxNumber`)
- `FaxNumber2` (nested: `Specialists.FaxNumber2`)

### 3. Address Information (7 fields)

- `Street1`, `Street2` (nested: `Address.*`)
- `City`, `StateName`, `StateCode` (nested: `Address.*`)
- `Zip5` (nested: `Address.Zip5`)
- `EmployerStreet` (nested: `Insurance.EmployerStreet`)
- `VisitAddress` (nested: `PatientCallLog.VisitAddress`)

### 4. Clinical/Notes (11 fields)

- `Notes` (nested: `Phones.Notes`)
- `FinalNotes` (nested: `PatientProblemList.EncounterProblemList.FinalNotes`)
- `Comments` (nested: `PatientProblemList.EncounterProblemList.Comments`)
- `Reason` (nested: `OutreachActivitiesList.Reason`)
- `OtherReason` (nested: `PatientDat.OtherReason`)
- `PatientName` (nested: `PatientCallLog.PatientName`)
- `UserName` (nested: `SubscribedUserDetails.UserName`)
- `PrimaryMemberName` (nested: `Insurance.PrimaryMemberName`)
- `PrimaryMemberDOB` (nested: `Insurance.PrimaryMemberDOB`)

## Faker Provider Mapping

| PHI Field           | Masking Rule             | Faker Provider                                         | Notes                      |
| ------------------- | ------------------------ | ------------------------------------------------------ | -------------------------- |
| `FirstName`         | `random_uppercase`       | `fake.first_name().upper()`                            | Uppercase names            |
| `MiddleName`        | `random_uppercase`       | `fake.first_name().upper()`                            | Use first_name for variety |
| `LastName`          | `random_uppercase`       | `fake.last_name().upper()`                             | Uppercase surnames         |
| `FirstNameLower`    | `lowercase_match`        | Derived from `FirstName.lower()`                       | Consistency check          |
| `MiddleNameLower`   | `lowercase_match`        | Derived from `MiddleName.lower()`                      | Consistency check          |
| `LastNameLower`     | `lowercase_match`        | Derived from `LastName.lower()`                        | Consistency check          |
| `Email`             | `replace_email`          | `fake.email()`                                         | Realistic email format     |
| `Dob`               | `add_milliseconds`       | `fake.date_of_birth(minimum_age=18, maximum_age=90)`   | Adult patients             |
| `Gender`            | `replace_gender`         | `fake.random_element(['Male', 'Female', 'Other'])`     | HIPAA compliant            |
| `MedicareId`        | `replace_string`         | `fake.bothify('?##-??-####').upper()`                  | Medicare format            |
| `PhoneNumber`       | `random_10_digit_number` | `fake.phone_number()` or `fake.numerify('##########')` | 10-digit US format         |
| `HomePhoneNumber`   | `random_10_digit_number` | `fake.numerify('##########')`                          | 10-digit                   |
| `WorkPhoneNumber`   | `random_10_digit_number` | `fake.numerify('##########')`                          | 10-digit                   |
| `Fax`               | `replace_string`         | `fake.numerify('##########')`                          | 10-digit fax               |
| `Street1`           | `replace_string`         | `fake.street_address()`                                | Full street address        |
| `Street2`           | `replace_string`         | `fake.secondary_address()` or `None`                   | Apt/Suite (optional)       |
| `City`              | `replace_string`         | `fake.city()`                                          | City name                  |
| `StateName`         | `replace_string`         | `fake.state()`                                         | Full state name            |
| `StateCode`         | No masking               | Derived from `fake.state_abbr()`                       | 2-letter code              |
| `Zip5`              | `replace_string`         | `fake.zipcode()[:5]`                                   | 5-digit ZIP                |
| `Notes`             | `replace_string`         | `fake.sentence(nb_words=10)`                           | Clinical notes             |
| `Comments`          | `replace_string`         | `fake.text(max_nb_chars=200)`                          | Problem comments           |
| `Reason`            | `replace_string`         | `fake.sentence(nb_words=8)`                            | Visit reason               |
| `PatientName`       | `random_uppercase`       | `f"{FirstName} {LastName}".upper()`                    | Full name consistency      |
| `PrimaryMemberName` | `replace_string`         | `fake.name().upper()`                                  | Insurance member           |
| `PrimaryMemberDOB`  | `add_milliseconds`       | `fake.date_of_birth(minimum_age=18, maximum_age=90)`   | Spouse/parent DOB          |
| `UserName`          | `replace_string`         | `fake.user_name()`                                     | Login username             |
| `EmployerStreet`    | `replace_string`         | `fake.street_address()`                                | Employer address           |

## Simplified Document Structure

Instead of replicating the entire Patients collection (which is large), we'll create a **focused test document**
containing only the essential nested structures for PHI field testing:

```python
{
    "_id": ObjectId(),
    # Top-level Personal Info (9 fields)
    "FirstName": "JOHN",
    "MiddleName": "MICHAEL",
    "LastName": "DOE",
    "FirstNameLower": "john",
    "MiddleNameLower": "michael",
    "LastNameLower": "doe",
    "Email": "john.doe@example.com",
    "Dob": ISODate("1985-06-15T00:00:00Z"),
    "Gender": "Male",
    "MedicareId": "A12-BC-3456",
    # Address nested object (6 fields)
    "Address": {
        "Street1": "123 Main Street",
        "Street2": "Apt 4B",
        "City": "Springfield",
        "StateName": "Illinois",
        "StateCode": "IL",
        "Zip5": "62701",
    },
    # Phones nested array (2 fields)
    "Phones": [
        {
            "PhoneType": "Mobile",
            "PhoneNumber": "5551234567",
            "Notes": "Primary contact number",
        }
    ],
    # Contacts nested object (2 fields)
    "Contacts": {"HomePhoneNumber": "5559876543", "WorkPhoneNumber": "5555555555"},
    # Pcp (Primary Care Provider) nested object (3 fields)
    "Pcp": {
        "Fax": "5551111111",
        "PcpSecondaryFaxNumber": "5552222222",
        "MRRFax": "5553333333",
    },
    # Insurance nested object (3 fields)
    "Insurance": {
        "PrimaryMemberName": "JANE DOE",
        "PrimaryMemberDOB": ISODate("1987-03-22T00:00:00Z"),
        "EmployerStreet": "456 Business Blvd",
    },
    # Specialists nested array (2 fields)
    "Specialists": [
        {
            "SpecialtyType": "Cardiology",
            "MRRFaxNumber": "5554444444",
            "FaxNumber2": "5555555555",
        }
    ],
    # PatientCallLog nested array (2 fields)
    "PatientCallLog": [
        {
            "CallDate": ISODate("2025-01-15T10:30:00Z"),
            "PatientName": "JOHN DOE",
            "VisitAddress": "789 Healthcare Dr, Springfield, IL",
        }
    ],
    # PatientProblemList nested structure (2 fields)
    "PatientProblemList": {
        "EncounterProblemList": [
            {
                "Problem": "Hypertension",
                "FinalNotes": "Blood pressure controlled with medication",
                "Comments": "Follow up in 3 months",
            }
        ]
    },
    # SubscribedUserDetails nested object (1 field)
    "SubscribedUserDetails": {
        "UserName": "johndoe123",
        "SubscriptionDate": ISODate("2024-01-01T00:00:00Z"),
    },
    # OutreachActivitiesList nested array (1 field)
    "OutreachActivitiesList": [
        {
            "ActivityDate": ISODate("2025-02-01T14:00:00Z"),
            "Reason": "Annual wellness check reminder",
        }
    ],
    # PatientDat nested object (1 field)
    "PatientDat": {"OtherReason": "Patient requested appointment change"},
}
```

**Document Complexity**: 34 PHI fields across 12 nested structures (7 objects, 4 arrays, 1 top-level)

## Implementation Plan

### Phase 1: Create Faker Data Generator Script

Create `scripts/generate_test_patients.py`:

```python
#!/usr/bin/env python3
"""
Generate realistic test patient data using Faker library.
Focuses on 34 PHI fields identified in the Patients collection.
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from faker import Faker
import random

# Initialize Faker with US locale for healthcare data
fake = Faker("en_US")
Faker.seed(42)  # For reproducible test data


class PatientDataGenerator:
    """Generates test patient documents with realistic PHI data."""

    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility."""
        self.fake = Faker("en_US")
        Faker.seed(seed)
        random.seed(seed)

    def generate_patient(self) -> Dict[str, Any]:
        """Generate a single patient document with all 34 PHI fields."""

        # Generate consistent name data
        first_name = self.fake.first_name().upper()
        middle_name = self.fake.first_name().upper()
        last_name = self.fake.last_name().upper()

        # Generate address data (keep StateCode consistent with StateName)
        state_abbr = self.fake.state_abbr()
        state_name = self._get_state_name(state_abbr)

        return {
            # Top-level Personal Info (9 fields)
            "FirstName": first_name,
            "MiddleName": middle_name,
            "LastName": last_name,
            "FirstNameLower": first_name.lower(),
            "MiddleNameLower": middle_name.lower(),
            "LastNameLower": last_name.lower(),
            "Email": self.fake.email(),
            "Dob": self.fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "Gender": random.choice(["Male", "Female", "Other"]),
            "MedicareId": self.fake.bothify("?##-??-####").upper(),
            # Address nested object (6 fields)
            "Address": {
                "Street1": self.fake.street_address(),
                "Street2": (
                    self.fake.secondary_address() if random.random() > 0.5 else None
                ),
                "City": self.fake.city(),
                "StateName": state_name,
                "StateCode": state_abbr,
                "Zip5": self.fake.zipcode()[:5],
            },
            # Phones nested array (2 fields)
            "Phones": [
                {
                    "PhoneType": "Mobile",
                    "PhoneNumber": self.fake.numerify("##########"),
                    "Notes": self.fake.sentence(nb_words=10),
                }
            ],
            # Contacts nested object (2 fields)
            "Contacts": {
                "HomePhoneNumber": self.fake.numerify("##########"),
                "WorkPhoneNumber": self.fake.numerify("##########"),
            },
            # Pcp nested object (3 fields)
            "Pcp": {
                "ProviderName": self.fake.name(),
                "Fax": self.fake.numerify("##########"),
                "PcpSecondaryFaxNumber": self.fake.numerify("##########"),
                "MRRFax": self.fake.numerify("##########"),
            },
            # Insurance nested object (3 fields)
            "Insurance": {
                "PrimaryMemberName": self.fake.name().upper(),
                "PrimaryMemberDOB": self.fake.date_of_birth(
                    minimum_age=18, maximum_age=90
                ).isoformat(),
                "EmployerStreet": self.fake.street_address(),
            },
            # Specialists nested array (2 fields)
            "Specialists": [
                {
                    "SpecialtyType": random.choice(
                        ["Cardiology", "Dermatology", "Orthopedics"]
                    ),
                    "MRRFaxNumber": self.fake.numerify("##########"),
                    "FaxNumber2": self.fake.numerify("##########"),
                }
            ],
            # PatientCallLog nested array (2 fields)
            "PatientCallLog": [
                {
                    "CallDate": self.fake.date_time_this_year().isoformat(),
                    "PatientName": f"{first_name} {last_name}",
                    "VisitAddress": f"{self.fake.street_address()}, {self.fake.city()}, {state_abbr}",
                }
            ],
            # PatientProblemList nested structure (2 fields)
            "PatientProblemList": {
                "EncounterProblemList": [
                    {
                        "Problem": random.choice(
                            ["Hypertension", "Diabetes", "Asthma", "Arthritis"]
                        ),
                        "FinalNotes": self.fake.text(max_nb_chars=200),
                        "Comments": self.fake.text(max_nb_chars=150),
                    }
                ]
            },
            # SubscribedUserDetails nested object (1 field)
            "SubscribedUserDetails": {
                "UserName": self.fake.user_name(),
                "SubscriptionDate": self.fake.date_time_this_year().isoformat(),
            },
            # OutreachActivitiesList nested array (1 field)
            "OutreachActivitiesList": [
                {
                    "ActivityDate": self.fake.date_time_this_month().isoformat(),
                    "Reason": self.fake.sentence(nb_words=8),
                }
            ],
            # PatientDat nested object (1 field)
            "PatientDat": {"OtherReason": self.fake.sentence(nb_words=10)},
        }

    def _get_state_name(self, state_abbr: str) -> str:
        """Map state abbreviation to full state name."""
        # Simplified mapping - in production use complete mapping
        state_map = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
            "DC": "District of Columbia",
        }
        return state_map.get(state_abbr, state_abbr)

    def generate_batch(self, count: int) -> List[Dict[str, Any]]:
        """Generate a batch of patient documents."""
        return [self.generate_patient() for _ in range(count)]

    def save_to_json(self, patients: List[Dict[str, Any]], filepath: str):
        """Save generated patients to JSON file."""
        with open(filepath, "w") as f:
            json.dump(patients, f, indent=2, default=str)
        print(f"✓ Generated {len(patients)} patient documents → {filepath}")

    def save_to_mongodb(
        self,
        patients: List[Dict[str, Any]],
        connection_string: str,
        database: str,
        collection: str,
    ):
        """Save generated patients directly to MongoDB."""
        from pymongo import MongoClient

        client = MongoClient(connection_string)
        db = client[database]
        coll = db[collection]

        result = coll.insert_many(patients)
        print(
            f"✓ Inserted {len(result.inserted_ids)} documents into {database}.{collection}"
        )
        client.close()


def main():
    """CLI entry point for test data generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate test patient data with Faker"
    )
    parser.add_argument(
        "--count", type=int, default=100, help="Number of patients to generate"
    )
    parser.add_argument(
        "--output", type=str, default="test_patients.json", help="Output JSON file"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--mongo-uri", type=str, help="MongoDB connection URI (optional)"
    )
    parser.add_argument(
        "--database", type=str, default="local_test_db", help="MongoDB database name"
    )
    parser.add_argument(
        "--collection", type=str, default="Patients", help="MongoDB collection name"
    )

    args = parser.parse_args()

    print(f"Generating {args.count} test patient documents...")

    generator = PatientDataGenerator(seed=args.seed)
    patients = generator.generate_batch(args.count)

    # Save to JSON file
    generator.save_to_json(patients, args.output)

    # Optionally save to MongoDB
    if args.mongo_uri:
        generator.save_to_mongodb(
            patients, args.mongo_uri, args.database, args.collection
        )

    print(f"\n✓ Test data generation complete!")
    print(f"  Documents: {args.count}")
    print(f"  PHI fields per document: 34")
    print(f"  Output file: {args.output}")


if __name__ == "__main__":
    main()
```

### Phase 2: Integration with Test Infrastructure

#### 2.1 Add to pytest fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def patient_generator():
    """Provide PatientDataGenerator for tests."""
    from scripts.generate_test_patients import PatientDataGenerator

    return PatientDataGenerator(seed=42)


@pytest.fixture
def sample_patient(patient_generator):
    """Generate a single test patient."""
    return patient_generator.generate_patient()


@pytest.fixture
def sample_patient_batch(patient_generator):
    """Generate a batch of 10 test patients."""
    return patient_generator.generate_batch(10)
```

#### 2.2 Update test suite to use generated data

```python
# tests/test_masking_patients.py
def test_mask_all_phi_fields(sample_patient, sample_masking_rules, mock_mongo_client):
    """Test that all 34 PHI fields are properly masked."""
    # Insert test patient
    db = mock_mongo_client["test_db"]
    coll = db["Patients"]
    coll.insert_one(sample_patient)

    # Apply masking rules
    masker = PatientMasker(masking_rules=sample_masking_rules)
    masked_patient = masker.mask_document(sample_patient)

    # Verify all PHI fields are masked
    assert masked_patient["FirstName"] != sample_patient["FirstName"]
    assert masked_patient["Email"] != sample_patient["Email"]
    # ... verify all 34 fields
```

### Phase 3: Update Testing Documentation

Add new section to `docs/TESTING_ENVIRONMENTS.md`:

````markdown
## Generating Test Data

### Using the Faker-based Patient Generator

The project includes a test data generator that creates realistic patient documents:

```bash
# Generate 100 test patients to JSON file
python scripts/generate_test_patients.py --count 100 --output test_patients.json

# Generate and load directly into LOCAL MongoDB
python scripts/generate_test_patients.py \
  --count 1000 \
  --mongo-uri "mongodb://localhost:27017" \
  --database local_test_db \
  --collection Patients

# Generate with custom seed for reproducibility
python scripts/generate_test_patients.py --count 50 --seed 12345
````

### Loading Test Data for Masking Tests

```bash
# 1. Generate test data
python scripts/generate_test_patients.py --count 100 --output test_patients.json

# 2. Load into LOCAL MongoDB
mongoimport --db local_test_db --collection Patients \
  --file test_patients.json --jsonArray

# 3. Run masking test
./scripts/test_local_to_dev.sh Patients 100
```

````

## Benefits of This Approach

### 1. **Focused Testing**
- Contains all 34 PHI fields without full production complexity
- Simplified document structure (12 nested structures vs. 50+ in production)
- Easier to debug and verify masking rules

### 2. **Realistic Data**
- Faker generates contextually appropriate data
- Maintains data consistency (e.g., FirstName ↔ FirstNameLower)
- State/city/ZIP codes are geographically consistent

### 3. **Reproducibility**
- Seeded random generation for consistent test data
- Version-controlled generator script
- Deterministic test outcomes

### 4. **Flexibility**
- Generate any quantity (10 for quick tests, 10,000 for load testing)
- Output to JSON file or directly to MongoDB
- Customizable complexity by adjusting nested array sizes

### 5. **Integration Ready**
- Works with existing pytest fixtures
- Compatible with current masking rules
- Supports both unit and integration tests

## Example Generated Document

```json
{
  "FirstName": "ROBERT",
  "MiddleName": "JAMES",
  "LastName": "ANDERSON",
  "FirstNameLower": "robert",
  "MiddleNameLower": "james",
  "LastNameLower": "anderson",
  "Email": "robert.anderson@example.com",
  "Dob": "1978-09-12",
  "Gender": "Male",
  "MedicareId": "H45-GF-7892",
  "Address": {
    "Street1": "8421 Pine Avenue",
    "Street2": "Suite 12",
    "City": "Austin",
    "StateName": "Texas",
    "StateCode": "TX",
    "Zip5": "78701"
  },
  "Phones": [
    {
      "PhoneType": "Mobile",
      "PhoneNumber": "5127894561",
      "Notes": "Patient prefers text messages for appointment reminders"
    }
  ],
  "Contacts": {
    "HomePhoneNumber": "5129876543",
    "WorkPhoneNumber": "5121234567"
  },
  "Pcp": {
    "ProviderName": "Dr. Sarah Mitchell",
    "Fax": "5125551111",
    "PcpSecondaryFaxNumber": "5125552222",
    "MRRFax": "5125553333"
  },
  "Insurance": {
    "PrimaryMemberName": "JENNIFER ANDERSON",
    "PrimaryMemberDOB": "1980-04-22",
    "EmployerStreet": "1500 Technology Blvd"
  },
  "Specialists": [
    {
      "SpecialtyType": "Cardiology",
      "MRRFaxNumber": "5125554444",
      "FaxNumber2": "5125555555"
    }
  ],
  "PatientCallLog": [
    {
      "CallDate": "2025-02-15T10:30:00",
      "PatientName": "ROBERT ANDERSON",
      "VisitAddress": "8421 Pine Avenue, Austin, TX"
    }
  ],
  "PatientProblemList": {
    "EncounterProblemList": [
      {
        "Problem": "Hypertension",
        "FinalNotes": "Blood pressure readings have stabilized with current medication regimen. Patient reports no adverse effects.",
        "Comments": "Continue current treatment plan. Schedule follow-up in 3 months."
      }
    ]
  },
  "SubscribedUserDetails": {
    "UserName": "randerson78",
    "SubscriptionDate": "2024-06-15T00:00:00"
  },
  "OutreachActivitiesList": [
    {
      "ActivityDate": "2025-03-01T14:00:00",
      "Reason": "Annual wellness check and flu vaccination reminder"
    }
  ],
  "PatientDat": {
    "OtherReason": "Patient requested appointment rescheduling due to work conflict"
  }
}
````

## Next Steps

1. **Immediate**: Create `scripts/generate_test_patients.py` with the implementation above
1. **Testing**: Generate 100 test patients and validate all 34 PHI fields are present
1. **Integration**: Add pytest fixtures to `tests/conftest.py`
1. **Documentation**: Update `TESTING_ENVIRONMENTS.md` with usage examples
1. **CI/CD**: Add test data generation to GitHub Actions workflow
1. **Validation**: Run masking on generated data and verify all rules apply correctly

## Dependencies

Add to `requirements.txt`:

```
Faker==24.0.0
```

## Success Criteria

- ✅ All 34 PHI fields present in generated documents
- ✅ Data passes existing masking rule validation
- ✅ Reproducible test data with seeded generation
- ✅ Performance: Generate 10,000 documents in \< 30 seconds
- ✅ Integration with pytest test suite
- ✅ Documentation complete with usage examples
