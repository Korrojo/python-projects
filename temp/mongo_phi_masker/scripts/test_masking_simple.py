#!/usr/bin/env python
"""
Simple test script for masking rules on StaffAvailability collection.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Custom JSON encoder to handle MongoDB ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Connect to MongoDB
def get_mongo_client(uri):
    """Create MongoDB client from URI."""
    logger.info(f"Connecting to MongoDB: {uri}")
    return MongoClient(uri)

# Load masking rules
def load_masking_rules(rules_file):
    """Load masking rules from JSON file."""
    rules_path = Path(rules_file).resolve()
    if not rules_path.exists():
        logger.error(f"Rules file not found: {rules_path}")
        sys.exit(1)
    
    logger.info(f"Loading masking rules from: {rules_path}")
    with open(rules_path, 'r') as f:
        return json.load(f)

# Apply masking rules to a document
def apply_masking_rules(doc, rules):
    """Apply masking rules to a document."""
    # Create a deep copy of the document to avoid modifying the original
    masked_doc = json.loads(json.dumps(doc, cls=MongoJSONEncoder))
    
    # Apply each rule
    for rule in rules["rules"]:
        field_path = rule["field"].split(".")
        apply_rule_to_path(masked_doc, field_path, rule)
    
    return masked_doc

def apply_rule_to_path(doc, path, rule):
    """Apply a rule to a specific path in a document."""
    if len(path) == 1:
        # Base case: we're at the target field
        field = path[0]
        if field in doc:
            doc[field] = apply_rule_to_value(doc[field], rule)
    elif len(path) > 1:
        # Recursive case: traverse the path
        field = path[0]
        if field in doc:
            if isinstance(doc[field], list):
                # Handle array fields
                for item in doc[field]:
                    if isinstance(item, dict):
                        apply_rule_to_path(item, path[1:], rule)
            elif isinstance(doc[field], dict):
                # Handle nested documents
                apply_rule_to_path(doc[field], path[1:], rule)

def apply_rule_to_value(value, rule):
    """Apply a masking rule to a specific value."""
    rule_type = rule["rule"]
    params = rule["params"]
    
    if value is None:
        return None
    
    if rule_type == "replace_string":
        return params
    elif rule_type == "random_uppercase_name":
        return "[MASKED NAME]"
    elif rule_type == "random_uppercase":
        return "[MASKED TEXT]"
    # Add other rule types as needed
    
    return value

# Find sample documents with PHI fields
def find_sample_documents(db, collection_name, sample_size=5):
    """Find sample documents that contain PHI fields."""
    collection = db[collection_name]
    
    # Query for documents with PHI fields in the nested path
    query = {
        "$or": [
            {"Slots.Appointments.PatientName": {"$exists": True, "$ne": None}},
            {"Slots.Appointments.City": {"$exists": True, "$ne": None}},
            {"Slots.Appointments.VisitNotes": {"$exists": True, "$ne": None}},
            {"Slots.Appointments.VisitAddress": {"$exists": True, "$ne": None}},
            {"Slots.Appointments.Comments": {"$exists": True, "$ne": None}}
        ]
    }
    
    logger.info(f"Finding {sample_size} sample documents with PHI fields")
    return list(collection.find(query).limit(sample_size))

# Extract PHI fields from a document for display
def extract_phi_fields(doc):
    """Extract PHI fields from a document for display."""
    phi_fields = {}
    
    if "Slots" in doc and isinstance(doc["Slots"], list):
        for slot in doc["Slots"]:
            if "Appointments" in slot and isinstance(slot["Appointments"], list):
                for appt in slot["Appointments"]:
                    # Extract PHI fields from appointment
                    if "PatientName" in appt:
                        phi_fields["PatientName"] = appt["PatientName"]
                    if "City" in appt:
                        phi_fields["City"] = appt["City"]
                    if "VisitNotes" in appt:
                        phi_fields["VisitNotes"] = appt["VisitNotes"]
                    if "VisitAddress" in appt:
                        phi_fields["VisitAddress"] = appt["VisitAddress"]
                    if "Comments" in appt:
                        phi_fields["Comments"] = appt["Comments"]
                    
                    # If we found PHI fields, return them
                    if phi_fields:
                        return phi_fields
    
    return phi_fields

# Main function
def main():
    """Main function."""
    # Parse command line arguments
    if len(sys.argv) < 4:
        logger.error("Usage: python test_masking_simple.py <mongo_uri> <db_name> <rules_file> [sample_size]")
        sys.exit(1)
    
    mongo_uri = sys.argv[1]
    db_name = sys.argv[2]
    rules_file = sys.argv[3]
    sample_size = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    collection_name = "StaffAvailability"
    
    # Connect to MongoDB
    client = get_mongo_client(mongo_uri)
    db = client[db_name]
    
    # Load masking rules
    rules = load_masking_rules(rules_file)
    
    # Find sample documents
    sample_docs = find_sample_documents(db, collection_name, sample_size)
    
    # Process each sample document
    for i, doc in enumerate(sample_docs):
        logger.info(f"Processing sample document {i+1}/{len(sample_docs)}")
        
        # Extract PHI fields before masking
        phi_before = extract_phi_fields(doc)
        
        # Apply masking rules
        masked_doc = apply_masking_rules(doc, rules)
        
        # Extract PHI fields after masking
        phi_after = extract_phi_fields(masked_doc)
        
        # Print comparison
        print(f"\n{'='*80}\nSample {i+1}:")
        print("\nBefore masking:")
        for field, value in phi_before.items():
            print(f"  {field}: {value}")
        
        print("\nAfter masking:")
        for field, value in phi_after.items():
            print(f"  {field}: {value}")
        
        print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
