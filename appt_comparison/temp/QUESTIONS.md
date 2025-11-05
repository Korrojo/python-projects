Questions Before Implementation:

1. Date/Time Handling:
Q1: For AvailabilityDate comparison, should I:

Compare only the date part (ignoring time)? yes, there is no time here just 0s to fill the format
Assume year 2025/2026 for 2-digit years in CSV (25 = 2025, 26 = 2026)? yes

Q2: For VisitStartDateTime comparison:

Should I normalize to 24-hour format before comparing? no
Or do exact string match (case-sensitive)? yes
Do I need to combine AvailabilityDate + VisitStartDateTime to create full datetime? no

2. Field Comparison Rules:

Q3: For PatientRef:

CSV has it as integer (e.g., 2565003)
MongoDB schema shows Number
Should I do type conversion or strict type+value match? should be exact match, no decimals

Q4: For VisitTypeValue:

Case-sensitive or case-insensitive comparison? case insensitve
Trim whitespace before comparing? yes

3. MongoDB Query Strategy:

Q5: Should I:
Build one aggregation pipeline per CSV row?
Batch multiple AthenaAppointmentIds into single $in query? yes
Create temporary indexes on Slots.Appointments.AthenaAppointmentId? no

4. Secondary Matching:

Q6: When doing secondary match (4-field combination):
If multiple appointments match the criteria, which one to compare? first one
Should I report multiple matches? no

5. Output Format:

Q7: Should the output CSV:
Overwrite the input file? no
Create timestamped output like {timestamp}_appointment_comparison_output.csv? yes
All the columns in the input file should exisit in the new output csv file
Keep original columns + add new validation columns? no

6. Error Handling:

Q8: How should I handle:
Missing/empty values in CSV (e.g., empty PatientRef)? all fileds on csv are expected to be present
Invalid date formats? check for this at the begning and fix it
MongoDB connection failures mid-processing? report failure and exit

7. Performance & Logging:

Q9: Expected performance requirements:
Process all 4,179 rows in one run? yes, but provide --limit argument to limit the number of rows which will be usfull for testing
Progress logging frequency (e.g., every 100 rows)? yes
Retry logic for MongoDB queries? yes

8. Environment:

Q10: Which MongoDB environment should this target: PROD,
Should it support APP_ENV switching (PROD, STG, LOCL)? yes, follow the patern in other projects, env should be overriden by --env in the argument
Which StaffAvailability collection (is there one per environment)? --env PROD (from shared_config/.env file DATABASE_NAME_PROD=UbiquityProduction)

9. Edge Cases:

Q11: Last row in CSV has empty AthenaAppointmentId:
Should I skip rows with empty AthenaAppointmentId?
Or mark them as "Invalid Input"?
I have updated REQUIRMENT.md with new updated requirments and this should be answered by the updates

ask me if you have any further question
