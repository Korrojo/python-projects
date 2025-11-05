# PHI Collection Masking Status

## Already Masked Collections (4 collections)

These collections have been successfully masked and should NOT be processed again:

1. **Container** - ✅ MASKED
1. **Patients** - ✅ MASKED
1. **StaffAvailability** - ✅ MASKED
1. **Tasks** - ✅ MASKED

## Collections to be Masked (38 collections)

These collections need to be processed with in-situ masking:

1. PatientCarePlanHistory
1. OfflineAppointments
1. PatientInsuranceHistory
1. Messages
1. PatientReportFaxQueue
1. Appointments
1. AutoMedicalRecordRequestEntries
1. CancelAppointmentHistory
1. cdc_c2p
1. CompletedExceptionAppointments
1. DeletedPatientChart
1. DeletedPatientChartReviews
1. DiscardedChartReview
1. ExternalReferral
1. ExternalReferralDeletedDraft
1. ExternalReferralDeliveryMethod
1. ExternalReferralDeliveryMethodValue
1. ExternalReferralFax
1. ExternalReferralQueue
1. ExternalReferralSentTo
1. FaxTransactions
1. InvalidApptData
1. MedicalRecordRequests
1. MobileAppRegistrationHistory
1. PCP
1. PCPHistory
1. PatientCarePan_StartDate
1. PatientCarePlan
1. PatientCarePlanResetStartDate
1. PatientChartReview
1. PatientHistory
1. PatientNotesHistory
1. PatientPanel
1. PatientReportFaxQueueHistory
1. PatientsMovedToLocalOutreach
1. Patients_Dat_Audio_Location_Reset
1. ReEngagingClosedPatientsProcessEntries
1. StaffAvailabilityOverrideHistory

## Configuration Files Updated

### Main Configuration

- **File**: `config/config_rules/config.json`
- **Updated**: `phi_collections` array now contains only the 38 collections that need masking
- **Updated**: `masking.rules_path` now points to `config/masking_rules/rules.json`

### PHI Collections List for Orchestration

- **File**: `docs/phi_collections.json`
- **Updated**: Contains JSON array of the 38 collections to be masked

### Masking Rules

- **File**: `config/masking_rules/rules.json`
- **Status**: Contains comprehensive PHI masking rules for all field types

## Usage Commands

### Run All Remaining Collections with In-Situ Masking

```bash
# Using orchestration script (recommended)
python scripts/orchestrate_migration.py --config config/config_rules/config.json --env .env.phi

# Using main masking script directly
python masking.py --in-situ --config config/config_rules/config.json --env .env.phi
```

### Process Individual Collection (if needed)

```bash
python masking.py --collection PatientCarePlanHistory --in-situ --config config/config_rules/config.json --env .env.phi
```

## Processing Mode

- **Mode**: In-Situ Masking (default in orchestration script)
- **Benefit**: Fastest processing, modifies source collections directly
- **No data transfer**: Documents are masked in place, no destination copying

## Logging Configuration

- **Base Directory**: `C:\Users\demesew\logs\mask\PHI`
- **Run Directory**: `mask_parallel_yyyymmdd_hhmmss` (created for each orchestration run)
- **Orchestration Log**: `mask_orchestration_yyyymmdd_hhmmss.log`
- **Multi-Collection Log**: `mask_parallel_yyyymmdd_hhmmss.log`
- **Single Collection Log**: `mask_Collection-name_yyyymmdd_hhmmss.log`

## Log Directory Structure

Each orchestration run creates a timestamped directory containing all related logs:

```
C:\Users\demesew\logs\mask\PHI\
├── mask_parallel_20250820_143022\                    # Run directory
│   ├── mask_orchestration_20250820_143022.log        # Orchestration coordination
│   ├── mask_parallel_20250820_143022.log             # Multi-collection processing
│   ├── mask_PatientCarePlanHistory_20250820_143025.log    # Individual collection
│   ├── mask_Messages_20250820_143030.log             # Individual collection
│   └── mask_OfflineAppointments_20250820_143035.log  # Individual collection
├── mask_parallel_20250820_151500\                    # Another run
│   ├── mask_orchestration_20250820_151500.log
│   └── ...
└── mask_single_20250820_160000\                      # Single collection run
    └── mask_Container_20250820_160000.log
```

## Benefits of Directory Structure

- **Organized by run**: Each execution gets its own folder
- **Easy cleanup**: Remove entire run directories when no longer needed
- **Parallel processing**: Multiple runs can execute simultaneously without log conflicts
- **Clear tracking**: Easy to find all logs related to a specific run

Last Updated: August 20, 2025
