# Index Creation Script for Appointment Comparison Performance

## Critical Index Missing

The `appointment_comparison` project performs lookups by `Slots.Appointments.AthenaAppointmentId` for **every single row** in the CSV. Without a proper index, this requires full collection scans.

---

## Index to Create

### **Primary Index (CRITICAL - Create Immediately)**

```javascript
// Create index on AthenaAppointmentId for fast primary matching
db.StaffAvailability.createIndex(
  { "Slots.Appointments.AthenaAppointmentId": 1 },
  { name: "IX_Appointments_AthenaAppointmentId" }
)
```

**Purpose**: Enables fast lookup by AthenaAppointmentId (used in primary matching for every CSV row)

**Expected Impact**:

- Reduces query time from O(n) to O(log n) where n = total appointments
- Batch queries with `$in` operator will be significantly faster
- Processing 2,127 rows could go from hours to minutes

---

## Secondary Indexes (RECOMMENDED for Secondary Matching)

If primary matching fails, the project falls back to 4-field combination matching. These indexes would help:

### **1. PatientRef Index**

```javascript
// Create index on PatientRef for secondary matching
db.StaffAvailability.createIndex(
  { "Slots.Appointments.PatientRef": 1 },
  { name: "IX_Appointments_PatientRef_Enhanced" }
)
```

**Note**: An index named `"PatientRef"` already exists, but this creates a more specific one for appointments.

### **2. Compound Index for 4-Field Secondary Matching**

```javascript
// Create compound index for efficient secondary matching
db.StaffAvailability.createIndex(
  {
    "AvailabilityDate": 1,
    "Slots.Appointments.PatientRef": 1,
    "Slots.Appointments.VisitTypeValue": 1,
    "Slots.Appointments.VisitStartDateTime": 1
  },
  { name: "IX_Appointments_SecondaryMatching" }
)
```

**Purpose**: Optimizes secondary matching queries when AthenaAppointmentId is not found

**Impact**: Makes 4-field combination lookups much faster

---

## How to Create These Indexes

### **Option 1: MongoDB Shell (mongosh)**

```bash
# Connect to MongoDB
mongosh "your_connection_string"

# Switch to database
use UbiquityProduction

# Create the critical index
db.StaffAvailability.createIndex(
  { "Slots.Appointments.AthenaAppointmentId": 1 },
  { name: "IX_Appointments_AthenaAppointmentId" }
)

# Verify index was created
db.StaffAvailability.getIndexes().filter(idx => idx.name.includes("AthenaAppointmentId"))
```

### **Option 2: MongoDB Compass**

1. Open MongoDB Compass
2. Connect to your database
3. Navigate to `UbiquityProduction` → `StaffAvailability`
4. Click on the "Indexes" tab
5. Click "Create Index"
6. Paste this JSON:

```json
{
  "Slots.Appointments.AthenaAppointmentId": 1
}
```

7. Set index name: `IX_Appointments_AthenaAppointmentId`
8. Click "Create Index"

### **Option 3: Python Script**

```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("your_connection_string")
db = client["UbiquityProduction"]

# Create the critical index
result = db.StaffAvailability.create_index(
    [("Slots.Appointments.AthenaAppointmentId", 1)],
    name="IX_Appointments_AthenaAppointmentId"
)

print(f"Index created: {result}")

# Verify
indexes = db.StaffAvailability.list_indexes()
for idx in indexes:
    if "AthenaAppointmentId" in idx.get("name", ""):
        print(f"Found index: {idx}")
```

---

## Index Creation Time Estimate

**Factors affecting creation time:**

- Collection size (number of documents)
- Number of appointments per document
- Server resources
- Current server load

**Typical estimates:**

- Small collection (<10K docs): 1-5 minutes
- Medium collection (10K-100K docs): 5-30 minutes
- Large collection (>100K docs): 30 minutes - 2 hours

**Note**: Index creation runs in the background by default in MongoDB 4.2+. The collection remains available during creation.

---

## Verify Index Performance

After creating the index, test performance with an explain query:

```javascript
db.StaffAvailability.explain("executionStats").aggregate([
  {
    $unwind: "$Slots"
  },
  {
    $unwind: "$Slots.Appointments"
  },
  {
    $match: {
      "Slots.Appointments.AthenaAppointmentId": { $in: ["18821", "20588", "22340"] }
    }
  }
])
```

**Look for:**

- `executionStats.totalDocsExamined` - Should be low (not scanning entire collection)
- `executionStats.executionTimeMillis` - Should be under 100ms for small batches
- `winningPlan.inputStage.indexName` - Should show `"IX_Appointments_AthenaAppointmentId"`

---

## Expected Indexes After Creation

After creating the critical index, you should have:

### Existing Indexes (from your file)

- ✅ `PatientRef` - Exists (helps with secondary matching)
- ✅ `AvailabilityDate` - Exists (helps with date filtering)
- ❌ `AthenaAppointmentId` - **MISSING - MUST CREATE**

### Recommended Final Index Set

1. ✅ `{ "Slots.Appointments.AthenaAppointmentId": 1 }` ← **CREATE THIS NOW**
2. ✅ `{ "Slots.Appointments.PatientRef": 1 }` ← Already exists
3. ✅ `{ "AvailabilityDate": 1 }` ← Already exists
4. ⚠️ `{ "AvailabilityDate": 1, "Slots.Appointments.PatientRef": 1, ... }` ← Optional compound index

---

## Performance Impact Measurement

### Before Index

Run a test query and note the time:

```javascript
db.StaffAvailability.aggregate([
  { $unwind: "$Slots" },
  { $unwind: "$Slots.Appointments" },
  { $match: { "Slots.Appointments.AthenaAppointmentId": { $in: ["18821", "20588"] } } },
  { $limit: 10 }
]).explain("executionStats")
```

### After Index

Run the same query and compare:

- Execution time should be 10-100x faster
- Documents examined should be dramatically reduced
- Index should be used in the winning plan

---

## Monitoring Index Usage

Check if your new index is being used:

```javascript
// Get index stats
db.StaffAvailability.aggregate([
  { $indexStats: {} },
  { $match: { name: "IX_Appointments_AthenaAppointmentId" } }
])
```

---

## Maintenance Notes

1. **Index Size**: The new index will take up disk space (typically 1-5% of collection size)
2. **Write Performance**: Slight overhead on inserts/updates to Appointments (negligible)
3. **Read Performance**: Massive improvement (10-100x faster for primary matching queries)

---

## Summary

### Action Items

1. ✅ **Immediately Create**: `db.StaffAvailability.createIndex({"Slots.Appointments.AthenaAppointmentId": 1})`
2. ⚠️ **Monitor**: Check index creation progress
3. ✅ **Verify**: Run explain query to confirm index is used
4. ⚠️ **Optional**: Create compound index for secondary matching if needed

### Expected Results

- **Before**: 2,127 row validation could take 2-4 hours
- **After**: 2,127 row validation should take 5-15 minutes

**Priority**: 🔴 **CRITICAL** - Create this index before running full validation!
