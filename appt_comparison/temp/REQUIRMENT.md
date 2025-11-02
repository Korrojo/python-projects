## Objective: compare data b/n Athena (csv source) and Ubiquity (MongoDB StaffAvailability collection)

## project name: "appointment_comparison"

## Input file : see "Daily_Appointment_Comparison_input1_20251023.csv"

## Collection schema: see "docs\schema\schema_StaffAvailability_20251007.js"

## requirment

### Cleanup

If "Cancel Status" column is present and the value is "Cancelled"

    Create a new csv file where
        all such rows are remove
        "Cancel Status" column is removed
        save it under data/input/<projectname>/<filename>_cleaned.csv

If "Cancel Status" column is not present

    move to the next step

### Primary Matching Using AthenaAppointmentId

For each entry in the CSV, use AthenaAppointmentId to locate the corresponding appointment (Slots.Appointments.AthenaAppointmentId) in the StaffAvailability collection.
Validate that the following fields match between Athena(csv) and Ubiquity(mongo):

    PatientRef (Slots.Appointments.PatientRef)  --> Number
    VisitTypeValue (Slots.Appointments.VisitTypeValue) --> String
    AvailabilityDate (root level field) --> Date [eg  "AvailabilityDate": ISODate:("2018-05-21T00:00:00.000Z") or "AvailabilityDate": {"$date": "2018-05-21T00:00:00.000Z"}]
    VisitStartDateTime (Slots.Appointments.VisitStartDateTime) --> String

If the AthenaAppointmentId is found in StaffAvailability AND If all of the above 4 fields match:

    mark the AthenaAppointmentId Found? column as True
    mark the Total Match? column as True
    move to the next row

If the AthenaAppointmentId is found in StaffAvailability AND If one or more of the above 4 fields mismatched:

    mark the AthenaAppointmentId Found? column as True
    mark the Total Match? column as False
    List the mismathed field(s) separeted with comma
    move to the next row

If the AthenaAppointmentId is not found in StaffAvailability

    mark the AthenaAppointmentId Found? column as False
    move to secondary matching logic

### Secondary Matching Using the 4 fields (fallback matching)

If the AthenaAppointmentId is not found in StaffAvailability

    Use the combination of following 4 fields to search fo a match:
        PatientRef
        VisitTypeValue
        AvailabilityDate
        VisitStartDateTime

If all of the above 4 fields match:

    mark the Total Match? column as True
    move to the next row

If one or more of the above 4 fields mismatched:

    mark the Total Match? column as False
    List the mismathed field(s) separeted with comma
    move to the next row

 If one or more of the above 4 fields are missing in the csv

    no comparison is needed
    list comma separeted missing fileds under "Missing Fields" column
