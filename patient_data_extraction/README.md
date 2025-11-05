# Patient Data Extraction Project

This project uses the common MongoDB framework to extract patient data across two databases:

1. Extract PatientIds from MO state patients (Database 1)
1. Extract detailed patient information using those IDs (Database 2)

## Project Structure

```bash
patient_data_extraction/
├── config/
│   ├── .env                   # Environment variables (not in git)
│   ├── .env.example           # Environment template
│   └── extraction_config.json # Project-specific configuration
├── src/
│   └── patient_extractor.py   # Main extraction logic
├── output/                    # CSV output files
├── logs/                      # Project logs
├── requirements.txt           # Project dependencies
├── run_extraction.py          # Main execution script
└── README.md                  # This file
```

## Configuration

### Shared Configuration (automatic)

MongoDB URIs are loaded from `../shared_config/.env`:

- `DB1_MONGODB_URI`: First database connection (for PatientId extraction)
- `DB2_MONGODB_URI`: Second database connection (for detailed patient data)

### Project Configuration (config/.env)

- `DB1_DATABASE_NAME`: First database name
- `DB2_DATABASE_NAME`: Second database name

### Extraction Config (extraction_config.json)

- Query parameters
- Output file settings
- Batch processing options

## Usage

1. **Setup Environment**:

   ```bash
   python setup_project.py
   ```

1. **Configure Connections**:

   - Copy `config/.env.example` to `config/.env`
   - Update with your MongoDB connection details

1. **Run Extraction**:

   ```bash
   python run_extraction.py
   ```

1. **For Task Scheduler**:

   ```batch
   run_extraction.bat
   ```

## Output Files

- `output/mo_patient_ids.csv` - PatientIds from MO state
- `output/patient_details.csv` - Detailed patient information
- `logs/extraction.log` - Execution logs

## Dependencies

This project uses `common_config` package. Install it with:

```bash
pip install -e C:/Users/dabebe/projects/python/common_config
```
