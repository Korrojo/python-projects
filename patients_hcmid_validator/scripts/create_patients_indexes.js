// patients_hcmid_validator/indexes/create_patients_indexes.js
// -----------------------------------------------------------
// Mongosh script to create/verify indexes for the Patients collection.
// Usage:
//   mongosh "mongodb://localhost:27017/UbiquityLOCAL" patients_hcmid_validator/indexes/create_patients_indexes.js
//
// This script:
//   1. Verifies connection & active DB.
//   2. (Optional) Checks for duplicate HcmId values (informational only now).
//   3. Ensures a NON-UNIQUE index on HcmId.
//   4. (Optional) Creates a compound index across identity fields (disabled by default).
//   5. Prints resulting indexes.
//
// Adjust DB / collection names as needed before running.

const COLLECTION_NAME = "Patients"; // change if your target differs

// Toggle whether to run the duplicate check (can be expensive on very large collections)
const RUN_DUPLICATE_CHECK = true;

// Toggle creation of a compound index. Enable ONLY if you have query patterns that filter
// with equality/ordering on more than just HcmId (e.g., analytics, alternative matching flows).
// NOTE: Your current validator code queries ONLY by HcmId using {$in: [...]}, so a compound
// index provides no additional benefit for that workload and increases index size & write cost.
const CREATE_COMPOUND_INDEX = false;

// Definition of optional compound index (HcmId prefix preserves utility for HcmId-only queries)
const COMPOUND_INDEX_DEF = { HcmId: 1, LastName: 1, FirstName: 1, Dob: 1, Gender: 1 };
const COMPOUND_INDEX_NAME = "IX_Patients_HcmId_Last_First_Dob_Gender";

function log(msg) {
    // Simple timestamped logger
    const ts = new Date().toISOString();
    print(`[${ts}] ${msg}`);
}

if (typeof db === 'undefined') {
    throw new Error("'db' is not defined. Run this via mongosh with a connection string.");
}

log(`Connected to database: ${db.getName()}`);

const coll = db.getCollection(COLLECTION_NAME);
if (!coll) {
    throw new Error(`Collection not found or inaccessible: ${COLLECTION_NAME}`);
}

log(`Target collection: ${COLLECTION_NAME}`);

let hasDuplicates = false;
if (RUN_DUPLICATE_CHECK) {
    log("Checking for duplicate HcmId values (first 1 if any)...");
    const dup = coll.aggregate([
        { $match: { HcmId: { $exists: true, $ne: null } } },
        { $group: { _id: "$HcmId", c: { $sum: 1 } } },
        { $match: { c: { $gt: 1 } } },
        { $limit: 1 }
    ]).toArray();
    hasDuplicates = dup.length > 0;
    if (hasDuplicates) {
        log(`Duplicate HcmId detected (e.g. '${dup[0]._id}').`);
    } else {
        log("No duplicate HcmId values detected (informational). Unique constraint intentionally NOT applied.");
    }
} else {
    log("Skipping duplicate check (RUN_DUPLICATE_CHECK=false).");
}

// 2. Determine if an HcmId index already exists
const existingIndexes = coll.getIndexes();
const hcmIdIndex = existingIndexes.find(ix => JSON.stringify(ix.key) === JSON.stringify({ HcmId: 1 }));

if (hcmIdIndex) {
    log(`Existing HcmId index found: name='${hcmIdIndex.name}', unique=${!!hcmIdIndex.unique}`);
    if (hcmIdIndex.unique) {
        log("NOTE: Unique constraint present but not required; consider dropping & recreating if duplicates are acceptable.");
    }
} else {
    // 3. Create NON-UNIQUE index
    const options = { name: "IX_Patients_HcmId" }; // no unique flag
    log("Creating NON-UNIQUE index on { HcmId: 1 } ...");
    const resultName = coll.createIndex({ HcmId: 1 }, options);
    log(`Index created: ${resultName}`);
}

// 4. (Optional) Compound index
if (CREATE_COMPOUND_INDEX) {
    const already = existingIndexes.find(ix => ix.name === COMPOUND_INDEX_NAME);
    if (already) {
        log(`Compound index already exists: ${COMPOUND_INDEX_NAME}`);
    } else {
        log(`Creating compound index ${COMPOUND_INDEX_NAME} on ${JSON.stringify(COMPOUND_INDEX_DEF)} ...`);
        coll.createIndex(COMPOUND_INDEX_DEF, { name: COMPOUND_INDEX_NAME });
    }
} else {
    log("Compound index creation disabled (CREATE_COMPOUND_INDEX=false).");
}

// 5. Print final index list
log("Final indexes:");
coll.getIndexes().forEach(ix => printjson(ix));

log("Done.");