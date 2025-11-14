#!/usr/bin/env python3
"""Setup test data for E2E testing."""

from pymongo import MongoClient


def setup_test_data():
    """Create test database with sample data."""
    # Connect to local MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["test_backup_demo"]
    collection = db["users"]

    # Clear existing data
    collection.delete_many({})

    # Insert test data
    users = [
        {
            "_id": 1,
            "name": "Alice Johnson",
            "age": 30,
            "email": "alice@example.com",
            "city": "New York",
        },
        {
            "_id": 2,
            "name": "Bob Smith",
            "age": 25,
            "email": "bob@example.com",
            "city": "Los Angeles",
        },
        {
            "_id": 3,
            "name": "Charlie Brown",
            "age": 35,
            "email": "charlie@example.com",
            "city": "Chicago",
        },
        {
            "_id": 4,
            "name": "Diana Prince",
            "age": 28,
            "email": "diana@example.com",
            "city": "Seattle",
        },
        {
            "_id": 5,
            "name": "Eve Wilson",
            "age": 32,
            "email": "eve@example.com",
            "city": "Boston",
        },
    ]
    collection.insert_many(users)

    print("✓ Created database: test_backup_demo")
    print(f"✓ Inserted {collection.count_documents({})} documents into users collection")


if __name__ == "__main__":
    setup_test_data()
