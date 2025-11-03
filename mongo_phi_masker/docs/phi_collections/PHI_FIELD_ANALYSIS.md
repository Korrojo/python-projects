# PHI Field Analysis

This document describes the PHI field analysis process implemented in MongoPHIMasker to identify, categorize, and group
collections based on their PHI field patterns.

## Overview

The PHI field analysis process identifies Protected Health Information (PHI) fields across MongoDB collections and
groups collections with similar field patterns to enable targeted masking rules.

## Analysis Process

1. **Field Detection**: The `analyze_collections.py` script identifies PHI fields across collections by:

   - Loading PHI field definitions from `rules.json`
   - Sampling documents from each collection (up to 1000 documents)
   - Using exact field name matching to identify PHI fields
   - Tracking the path of each PHI field within document structures

1. **Collection Grouping**: Collections are clustered based on their PHI field similarity using:

   - Jaccard similarity to measure field pattern overlap
   - Hierarchical clustering to identify natural groupings
   - Characteristic field extraction to identify defining fields for each group

1. **Output Files**:

   - `collection_analysis.json`: Detailed PHI field analysis per collection
   - `phi_field_similarity.json`: Similarity matrix showing collection relationships
   - `collection_groups.json`: Grouped collections with characteristic fields

## Collection Groups

The analysis has identified 7 collection groups with distinct PHI field patterns:

1. **Group 0**: 45 unique PHI fields (comprehensive) - 30 collections
1. **Group 1**: 16 unique PHI fields (name-focused) - 6 collections
1. **Group 2**: 6 unique PHI fields (care plan related) - 5 collections
1. **Group 3**: 0 unique PHI fields (no PHI detected) - 6 collections
1. **Group 4**: 5 unique PHI fields (phone-focused) - 2 collections
1. **Group 5**: 4 unique PHI fields (fax/email-focused) - 3 collections
1. **Group 6**: 1 unique PHI field (reason only) - 6 collections

## Usage

Run the analysis script with:

```bash
cd /dbdrive/projects/python/MongoPHIMasker
source venv/bin/activate
python scripts/analyze_collections.py --env .env.prod --phi-collections docs/phi_collections.json
```

## TODO: Next Steps to Complete Implementation

1. **Create Group-Specific Masking Rules**:

   - Create 7 rule files based on the identified groups
   - Each rule file should contain only the PHI fields needed for its group
   - Example: `rule_group_5.json` would contain rules for Email, FaxNumber, PatientName, UserName

1. **Update Configuration**:

   - Modify `config.json` to include collection-to-group mappings
   - Add a structure to map collection names to rule group files

1. **Update Masking Code**:

   - Modify `masking.py` to select appropriate rule file based on collection name
   - Implement efficient rule loading mechanism

1. **Test Group-Based Masking**:

   - Test each rule group with representative collections
   - Verify all 11 fax field types are properly masked
   - Validate performance with large (25-30GB) collections

1. **Documentation**:

   - Add details about group-based masking to main README
   - Document the rule file selection process

1. **Deployment Preparation**:

   - Ensure Docker/Kubernetes configurations account for additional rule files
   - Update monitoring to track masking by collection group

By implementing these steps, MongoPHIMasker will be able to efficiently process 200+ collections with tailored masking
rules while maintaining a collection-agnostic architecture.
