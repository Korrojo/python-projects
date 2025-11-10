// MongoDB Investigation Script for "Not Found" Users
// Run this in MongoDB shell to check status of users not found during update

// Switch to correct database
use UbiquityTRAINING;

print("\n========================================");
print("INVESTIGATION: NOT FOUND USERS");
print("========================================\n");

// List of "not found" users from CSV
const notFoundUsers = [
    { first: "JESSICA", last: "BRUNS", id: 32 },
    { first: "KARA", last: "BRUNTON", id: 46 },
    { first: "THOMAS", last: "CHARLTON", id: 51 },
    { first: "JESSICA", last: "CLOKEY", id: 58 },
    { first: "AMANDA", last: "DARBY", id: 61 },
    { first: "LAUREN", last: "DOLL", id: 33 },
    { first: "SHELLY", last: "DUKE", id: 36 },
    { first: "BRITTANY", last: "GHANI", id: 40 },
    { first: "MANDY", last: "HEATON", id: 34 },
    { first: "RANDY", last: "HERBERT", id: 71 }
    // Add more as needed
];

let inactiveCount = 0;
let missingCount = 0;
let activeCount = 0;

print("Checking first 10 users...\n");

notFoundUsers.forEach(function(user) {
    const result = db.Users_bkp_20251002.findOne(
        {
            FirstName: new RegExp("^" + user.first + "$", "i"),
            LastName: new RegExp("^" + user.last + "$", "i")
        },
        { FirstName: 1, LastName: 1, IsActive: 1, AthenaProviderId: 1 }
    );

    if (result) {
        if (result.IsActive) {
            print("✅ ACTIVE: " + user.first + " " + user.last + " (ID: " + result._id + ")");
            activeCount++;
        } else {
            print("❌ INACTIVE: " + user.first + " " + user.last + " (ID: " + result._id + ", AthenaProviderId: " + result.AthenaProviderId + ")");
            inactiveCount++;
        }
    } else {
        print("⚠️  MISSING: " + user.first + " " + user.last + " (CSV ID: " + user.id + ")");
        missingCount++;
    }
});

print("\n========================================");
print("SUMMARY");
print("========================================");
print("Inactive users: " + inactiveCount);
print("Missing users: " + missingCount);
print("Active users (unexpected): " + activeCount);
print("========================================\n");

// Check for hyphenated name variations
print("\n========================================");
print("CHECKING HYPHENATED NAMES");
print("========================================\n");

print("Searching for HOEHN-GRAVES variations:");
db.Users_bkp_20251002.find(
    { FirstName: /^CONNIE$/i, LastName: /HOEHN/i },
    { FirstName: 1, LastName: 1, IsActive: 1 }
).forEach(printjson);

print("\nSearching for JOUBERT-ROCKETT variations:");
db.Users_bkp_20251002.find(
    { FirstName: /^NICHOLA$/i, LastName: /JOUBERT/i },
    { FirstName: 1, LastName: 1, IsActive: 1 }
).forEach(printjson);

print("\nSearching for TATE variations:");
db.Users_bkp_20251002.find(
    { FirstName: /^TIFFANY$/i, LastName: /TATE/i },
    { FirstName: 1, LastName: 1, IsActive: 1 }
).forEach(printjson);

print("\n========================================");
print("INVESTIGATION COMPLETE");
print("========================================\n");
