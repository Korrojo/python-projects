import json
import os
import traceback

from dotenv import load_dotenv
from pymongo import MongoClient

try:
    # Construct the absolute path to the .env.prod file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.prod")
    print(f"Attempting to load environment from: {os.path.abspath(env_path)}")
    load_dotenv(dotenv_path=env_path)
    print("Environment variables loaded successfully.")
except Exception as e:
    print(f"Error loading environment variables: {e}")
    traceback.print_exc()

# Aggregation pipeline (converted from JS to Python dictionary format)
phi_aggregation_pipeline = [
    {
        "$project": {
            "PatientRef": 1,
            "Dob": 1,
            "Email": 1,
            "FirstName": 1,
            "FirstNameLower": 1,
            "Gender": 1,
            "LastName": 1,
            "LastNameLower": 1,
            "MiddleName": 1,
            "MiddleNameLower": 1,
            "Address_City": "$Address.City",
            "Address_StateCode": "$Address.StateCode",
            "Address_StateName": "$Address.StateName",
            "Address_Street1": "$Address.Street1",
            "Address_Street2": "$Address.Street2",
            "Address_Zip5": "$Address.Zip5",
            "Allergies_Notes": "$Allergies.Notes",
            "Contacts_Dob": "$Contacts.Dob",
            "Contacts_FirstName": "$Contacts.FirstName",
            "Contacts_HomePhoneNumber": "$Contacts.HomePhoneNumber",
            "Contacts_LastName": "$Contacts.LastName",
            "Contacts_MiddleName": "$Contacts.MiddleName",
            "Contacts_WorkPhoneNumber": "$Contacts.WorkPhoneNumber",
            "DocuSign_UserName": "$DocuSign.UserName",
            "HealthPlanMemberId": 1,
            "HomeHealthAndDMEDetails_City": "$HomeHealthAndDMEDetails.City",
            "HomeHealthAndDMEDetails_PhoneNumber": "$HomeHealthAndDMEDetails.PhoneNumber",
            "Insurance_EmployerStreet": "$Insurance.EmployerStreet",
            "Insurance_PhoneNumber": "$Insurance.PhoneNumber",
            "Insurance_PrimaryMemberDOB": "$Insurance.PrimaryMemberDOB",
            "Insurance_PrimaryMemberName": "$Insurance.PrimaryMemberName",
            "MobileAppRegistration_PhoneNumber": "$MobileAppRegistration.PhoneNumber",
            "OutreachActivitiesList_Reason": "$OutreachActivitiesList.Reason",
            "PatientCallLog_Notes": "$PatientCallLog.Notes",
            "PatientCallLog_PatientName": "$PatientCallLog.PatientName",
            "PatientCallLog_PhoneNumber": "$PatientCallLog.PhoneNumber",
            "PatientCallLog_VisitAddress": "$PatientCallLog.VisitAddress",
            "PatientDat_Notes": "$PatientDat.Notes",
            "PatientDat_OtherReason": "$PatientDat.OtherReason",
            "PatientProblemList_EncounterProblemList_Comments": "$PatientProblemList.EncounterProblemList.Comments",
            "PatientProblemList_EncounterProblemList_FinalNotes": "$PatientProblemList.EncounterProblemList.FinalNotes",
            "PatientSyncFailureDetails_UserName": "$PatientSyncFailureDetails.UserName",
            "Pcp_City": "$Pcp.City",
            "Pcp_FirstName": "$Pcp.FirstName",
            "Pcp_LastName": "$Pcp.LastName",
            "Pcp_MiddleName": "$Pcp.MiddleName",
            "Phones_Notes": "$Phones.Notes",
            "Phones_PhoneNumber": "$Phones.PhoneNumber",
            "PreviousAddress_City": "$PreviousAddress.City",
            "PreviousAddress_StateCode": "$PreviousAddress.StateCode",
            "PreviousAddress_StateName": "$PreviousAddress.StateName",
            "PreviousAddress_Street1": "$PreviousAddress.Street1",
            "PreviousAddress_Street2": "$PreviousAddress.Street2",
            "PreviousAddress_Zip5": "$PreviousAddress.Zip5",
            "Programs_Notes": "$Programs.Notes",
            "Specialists_Email": "$Specialists.Email",
            "Specialists_FirstName": "$Specialists.FirstName",
            "Specialists_LastName": "$Specialists.LastName",
            "Specialists_MiddleName": "$Specialists.MiddleName",
            "SubscribedUserDetails_UserName": "$SubscribedUserDetails.UserName",
        }
    }
]


def compare_collections():
    # Print the absolute path to the .env.prod file for debugging
    print(f"Loading environment from: {os.path.abspath(env_path)}")

    # Get individual MongoDB connection variables
    username = os.getenv("MONGO_SOURCE_USERNAME")
    password = os.getenv("MONGO_SOURCE_PASSWORD")
    host = os.getenv("MONGO_SOURCE_HOST")
    auth_db = os.getenv("MONGO_SOURCE_AUTH_DB")
    use_ssl = os.getenv("MONGO_SOURCE_USE_SSL", "false").lower() == "true"
    use_srv = os.getenv("MONGO_SOURCE_USE_SRV", "false").lower() == "true"
    db_name = os.getenv("MONGO_SOURCE_DB")

    # Check if required variables are present
    if not all([host, db_name]):
        print("ERROR: Required MongoDB connection details not found in .env.prod file.")
        print("Please ensure your .env.prod file contains at least MONGO_SOURCE_HOST and MONGO_SOURCE_DB variables.")
        return

    # Construct the MongoDB URI
    protocol = "mongodb+srv" if use_srv else "mongodb"
    auth_part = f"{username}:{password}@" if username and password else ""
    auth_db_part = f"/?authSource={auth_db}" if auth_db else "/"
    ssl_part = "&ssl=true" if use_ssl else ""

    uri = f"{protocol}://{auth_part}{host}{auth_db_part}{ssl_part}"

    # Redact credentials in log output
    redacted_auth = "***:***@" if username and password else ""
    print(f"Constructed MongoDB URI: {protocol}://{redacted_auth}[HOST]{auth_db_part}{ssl_part}")
    print(f"Using database: {db_name}")

    # Connect to MongoDB
    client = MongoClient(uri)
    db = client[db_name]

    original_col = db["AD_Patients_20250630_copy"]
    masked_col = db["AD_Patients_20250630"]

    print("Fetching data from original collection...")
    original_docs = list(original_col.aggregate(phi_aggregation_pipeline))
    print("Fetching data from masked collection...")
    masked_docs = list(masked_col.aggregate(phi_aggregation_pipeline))

    original_docs_map = {str(doc["_id"]): doc for doc in original_docs}

    different_count = 0
    same_count = 0

    for masked_doc in masked_docs:
        masked_id = str(masked_doc["_id"])
        original_doc = original_docs_map.get(masked_id)

        if original_doc:
            differences = []
            # Sort keys to ensure consistent comparison
            sorted_keys = sorted(masked_doc.keys())
            for key in sorted_keys:
                # Use json.dumps for a consistent, type-agnostic comparison
                if json.dumps(masked_doc.get(key), sort_keys=True) != json.dumps(original_doc.get(key), sort_keys=True):
                    differences.append({"field": key, "original": original_doc.get(key), "masked": masked_doc.get(key)})

            if differences:
                different_count += 1
                print(f"\nDocument with _id: {masked_id} has changed.")
                for diff in differences:
                    print(f'  - Field: {diff["field"]}')
                    print(f'    Original: {json.dumps(diff["original"])}')
                    print(f'    Masked:   {json.dumps(diff["masked"])}')
            else:
                same_count += 1
        else:
            print(f"Document with _id: {masked_id} not found in original collection.")

    print("\n--- Comparison Summary ---")
    print(f"Total documents checked: {len(masked_docs)}")
    print(f"Documents with differences: {different_count}")
    print(f"Documents that are the same: {same_count}")
    print("--------------------------")

    client.close()


if __name__ == "__main__":
    try:
        print("Starting comparison script...")
        compare_collections()
        print("Script completed.")
    except Exception as e:
        print(f"Error running comparison script: {e}")
        traceback.print_exc()
