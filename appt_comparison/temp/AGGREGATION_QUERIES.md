# MongoDB Aggregation Queries for Appointment Comparison

This document contains MongoDB aggregation queries that can be run directly on the database to replicate the logic used
in the appointment_comparison validator.

## 1. Primary Matching - Find by AthenaAppointmentId (Single Record)

Use this to find a specific appointment by its AthenaAppointmentId:

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.AthenaAppointmentId": "18821"  // Replace with your ID
    }
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  },
  {
    $limit: 1
  }
])
```

**Expected Output:**

```json
{
  "AthenaAppointmentId": "18821",
  "PatientRef": "2565003",
  "VisitTypeValue": "Palliative Prognosis Visit",
  "VisitStartDateTime": "13:35:00",
  "AvailabilityDate": ISODate("2025-10-27T00:00:00.000Z")
}
```

______________________________________________________________________

## 2. Primary Matching - Batch Find by AthenaAppointmentId (Multiple Records)

Use this to find multiple appointments at once (batch processing):

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.AthenaAppointmentId": {
        $in: [
          "18821",
          "20588",
          "22340",
          "21463",
          "19873",
          "20798",
          "22025",
          "20691",
          "21186",
          "21178"
        ]
      }
    }
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  }
])
```

**Expected Output:** Array of matching appointments with the 5 fields projected.

______________________________________________________________________

## 3. Secondary Matching - Find by 4-Field Combination (Fallback)

Use this when AthenaAppointmentId is not found. This searches by the combination of all 4 fields:

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.PatientRef": "2565184",  // Replace with your values
      "Slots.Appointments.VisitTypeValue": {
        $regex: "^Palliative Management$",
        $options: "i"  // Case-insensitive match
      },
      "AvailabilityDate": {
        $gte: ISODate("2025-11-17T00:00:00.000Z"),
        $lt: ISODate("2025-11-18T00:00:00.000Z")  // Date-only comparison
      },
      "Slots.Appointments.VisitStartDateTime": "08:15:00"  // Exact match
    }
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  },
  {
    $limit: 1  // Only take first match
  }
])
```

**Note:** For the date comparison, you need to convert the CSV date (e.g., "11/17/25") to ISO format:

- Input: `11/17/25`
- Output: `ISODate("2025-11-17T00:00:00.000Z")` to `ISODate("2025-11-18T00:00:00.000Z")`

______________________________________________________________________

## 4. Count Total Appointments in Collection

Get a count of all appointments across all staff availability records:

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $count: "totalAppointments"
  }
])
```

______________________________________________________________________

## 5. Find All Appointments for a Specific Date

Find all appointments on a specific availability date:

```javascript
db.StaffAvailability.aggregate([
  {
    $match: {
      "AvailabilityDate": {
        $gte: ISODate("2025-10-27T00:00:00.000Z"),
        $lt: ISODate("2025-10-28T00:00:00.000Z")
      }
    }
  },
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  },
  {
    $sort: {
      VisitStartDateTime: 1
    }
  }
])
```

______________________________________________________________________

## 6. Find All Appointments for a Specific Patient

Find all appointments for a patient by PatientRef:

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.PatientRef": "2565003"  // Replace with patient ref
    }
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  },
  {
    $sort: {
      AvailabilityDate: -1
    }
  }
])
```

______________________________________________________________________

## Key Query Components Used in the Project

### 1. **$unwind Stages** (Required)

The collection has nested arrays, so we need two `$unwind` operations:

1. First `$unwind: "$Slots"` - Expands the Slots array
1. Second `$unwind: "$Slots.Appointments"` - Expands the Appointments array within each Slot

### 2. **$match Stage** (Filtering)

- **Primary Match**: `"Slots.Appointments.AthenaAppointmentId": { $in: [array_of_ids] }`
- **Secondary Match**: Combination of 4 fields with operators:
  - `PatientRef`: Exact match (string)
  - `VisitTypeValue`: Case-insensitive regex (`$regex` with `$options: "i"`)
  - `AvailabilityDate`: Date range (`$gte` and `$lt` for date-only comparison)
  - `VisitStartDateTime`: Exact match (string in "HH:MM:SS" format)

### 3. **$project Stage** (Field Selection)

Projects only the 5 fields needed for comparison:

- `AthenaAppointmentId` (from nested path)
- `PatientRef` (from nested path)
- `VisitTypeValue` (from nested path)
- `VisitStartDateTime` (from nested path)
- `AvailabilityDate` (from root level)

### 4. **$limit Stage** (Performance)

- Batch queries: No limit (returns all matches)
- Secondary matching: `$limit: 1` (only first match needed)

______________________________________________________________________

## Comparison Rules Applied in Project

### Field Comparison Logic

1. **PatientRef** (Number)

   - MongoDB: String like `"2565003"`
   - CSV: Number like `2565003`
   - Comparison: Convert CSV to string, exact match

1. **VisitTypeValue** (String)

   - MongoDB: `"Palliative Management"`
   - CSV: `"Palliative Management"` or `"palliative management"`
   - Comparison: Case-insensitive, trimmed

1. **AvailabilityDate** (Date)

   - MongoDB: `ISODate("2025-10-27T00:00:00.000Z")` or `{"$date": "2025-10-27T00:00:00.000Z"}`
   - CSV: `"10/27/25"` (M/D/YY format)
   - Comparison: Date-only (ignore time component)

1. **VisitStartDateTime** (String/Time)

   - MongoDB: `"13:35:00"` (24-hour HH:MM:SS)
   - CSV: `"1:35 PM"` (12-hour with AM/PM)
   - Comparison: Parse both to time objects, compare

______________________________________________________________________

## How to Run These Queries

### Option 1: MongoDB Compass

1. Open MongoDB Compass
1. Connect to your database
1. Select the `StaffAvailability` collection
1. Click "Aggregations" tab
1. Paste the pipeline stages
1. Click "Run"

### Option 2: MongoDB Shell (mongosh)

```javascript
use UbiquityProduction
// Paste the query here
```

### Option 3: Python with PyMongo

```python
from pymongo import MongoClient

client = MongoClient("your_connection_string")
db = client["UbiquityProduction"]

pipeline = [
    # Paste pipeline stages here
]

results = list(db.StaffAvailability.aggregate(pipeline))
for doc in results:
    print(doc)
```

______________________________________________________________________

## Performance Considerations

1. **Indexes**: Consider creating compound indexes for better performance:

   ```javascript
   db.StaffAvailability.createIndex({"Slots.Appointments.AthenaAppointmentId": 1})
   db.StaffAvailability.createIndex({"AvailabilityDate": 1})
   db.StaffAvailability.createIndex({"Slots.Appointments.PatientRef": 1})
   ```

1. **Batch Size**: The project uses batches of 100 rows to balance memory usage and query performance.

1. **$unwind Impact**: The double `$unwind` can be expensive on large collections. Consider adding `$match` early in the
   pipeline when possible.

______________________________________________________________________

## Example: Testing a Specific CSV Row

To test row from CSV:

```
AthenaAppointmentId: 18821
PatientRef: 2565003
VisitTypeValue: Palliative Prognosis Visit
VisitStartDateTime: 1:35 PM
AvailabilityDate: 10/27/25
```

Run this query:

```javascript
db.StaffAvailability.aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.AthenaAppointmentId": "18821"
    }
  },
  {
    $project: {
      _id: 0,
      AthenaAppointmentId: "$Slots.Appointments.AthenaAppointmentId",
      PatientRef: "$Slots.Appointments.PatientRef",
      VisitTypeValue: "$Slots.Appointments.VisitTypeValue",
      VisitStartDateTime: "$Slots.Appointments.VisitStartDateTime",
      AvailabilityDate: "$AvailabilityDate"
    }
  }
])
```

**Expected Match:**

- PatientRef: `"2565003"` ✅
- VisitTypeValue: `"Palliative Prognosis Visit"` ✅ (case-insensitive)
- AvailabilityDate: `ISODate("2025-10-27T00:00:00.000Z")` ✅ (date only)
- VisitStartDateTime: `"13:35:00"` ✅ (converts from "1:35 PM")
