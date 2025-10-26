# Requirements

- **Database name:** `UbiquitySTG3`
- **Collection name:** `Users`
- **Copied collection name:** `AD_Users_{timestamp}`
- **Source file name:** `provider_3320210.csv`

## Steps

1. Work on the `UbiquitySTG3` database and take a copy of the `Users` collection (eg name --> `AD_Users_{timestamp}`).
2. Updates will be made on the copied collection.
3. Use the provided CSV to match the first and last names in the copied collection (`FirstName` / `LastName`).
    - Example:
      ```js
      db.getCollection("AD_Users_{timestamp}").find({ "LastName": "Heaton", "FirstName": "Mandy" })
      ```
    - If duplicates are present, skip and log an error for that user.
4. Update the following fields for the matches:
    - `NPI`: NPI field from CSV
    - `AthenaProviderId`: ID field from CSV (should be an integer)
    - `AthenaUserName`: UserName field from CSV
    - Example:
      ```json
      {
        "NPI": "1003453028",
        "AthenaProviderId": 56,
        "AthenaUserName": "p-mheaton"
      }
      ```
5. If the `AthenaProviderId` exists for the user, skip the record and log the occurrence.
6. Do a thorough validation of the updates on the copied collection.
7. Ask Karthik to do a quick validation.
8. Rename the `Users` collection to `Users_bkp_{timestamp}`.
9. Rename the copied collection (`AD_Users_{timestamp}`) to `Users`.
10. End of task.