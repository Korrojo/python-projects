# MongoDB PHI Masker

A comprehensive data pipeline for extracting data from MongoDB, masking Protected Health Information (PHI), and restoring it to another MongoDB collection.

## Documentation

- [Project Overview](PROJECT.md) - Features, installation, and getting started
- [Development Guide](DEVELOPMENT.md) - Coding standards, architecture, and contribution guidelines
- [Testing Guide](TESTING.md) - Test status, running tests, and known issues

## Quick Start

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Docker (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mongophimasker.git
   cd mongophimasker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy and configure the environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the masker:
   ```bash
   python -m src.main --env .env.dev --config config/config_rules/config.json
   ```

## Features

- **Flexible Data Masking**: Mask PHI data in MongoDB collections using configurable rules
- **Complex Document Support**: Handle nested documents, arrays, and complex MongoDB structures
- **Incremental Processing**: Support for incremental data processing with checkpointing
- **Multi-environment Support**: Configuration for development, testing, and production environments
- **Performance Optimized**: Batch processing with configurable settings for high-volume data

## Latest Updates

- **PowerShell Wrapper Script (Oct 2025)**: Added `run_masking_job.ps1` for Windows users with automatic log file management, background job support, and real-time monitoring capabilities. Fixed issues with path resolution and output redirection in background jobs.
- **Enhanced Logging**: Added support for log rotation and configurable log levels
- **Backward Compatibility Layer**: New compatibility module to maintain backward compatibility
- **In-situ Masking**: New functionality to mask documents in-place without copying to a destination collection
- **Multi-collection Processing**: Support for processing a list of collections defined in config.json
- **Test Improvements**: Fixed test failures related to API changes and object instantiation
- **Configuration Examples**: Added example configuration files for easier setup
- **Test Utilities**: Created test runner scripts for different testing scenarios
- **Documentation Updates**: Added detailed documentation of test fixes and status
- **Strict Category Ordering:** PHI collection categories are now strictly ordered by complexity (most to least) in `collection_rule_mapping.py`. Each category is clearly numbered (1-8) for reference and automation.
- **Category-Specific Masking Rules:** Masking rules are now split into `rule_group_1.json` through `rule_group_8.json`, each aligned to the new category order and field mapping. Each rule group file contains only the PHI fields and masking logic relevant to its category.
- **Updated Masking Logic:** The `PatientName` field now uses the `random_uppercase_name` rule, generating two random uppercase words (first and last name). Fax fields (e.g., Fax, MRRFax, FaxNumber, etc.) are masked with `1111111111111` for HIPAA compliance.
- **rules.json as Template:** The main `rules.json` now serves as a template/example and is not used directly for masking. Category-specific rule groups are used for actual processing.
- **Documentation & Config Updates:** Comments and documentation in config files have been updated to reflect these changes.

## Architecture

The application follows a modular architecture with the following components:

- **Orchestrator**: Coordinates the overall masking process
- **Processor**: Manages the data processing workflow
- **Connector**: Handles MongoDB connections and operations
- **Masker**: Applies masking rules to PHI data
- **Validator**: Validates data before and after masking
- **Config Loader**: Loads and validates configuration
- **Logger**: Manages application logging
- **Error Handler**: Handles and reports errors
- **Email Alerter**: Sends email notifications
- **Metrics Collector**: Collects and reports metrics
- **Compatibility Layer**: Provides backward compatibility for evolving APIs

## Installation

### Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Docker (optional)
- Kubernetes (optional)

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MongoPHIMasker.git
   cd MongoPHIMasker
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the application:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   cp config/config_rules/config.example.yaml config/config_rules/config.json
   # Edit config.json with your configuration
   ```

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t phi-masker:latest .
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up
   ```

## Usage

### Command Line Interface

The application provides a command-line interface with various options:

```bash
python masking.py [options]
```

Options:
- `--config`: Path to configuration file (required)
- `--env`: Path to environment file (required)
- `--limit`: Maximum number of documents to process
- `--query`: MongoDB query in JSON format to filter documents
- `--reset-checkpoint`: Reset checkpoint file
- `--verify-only`: Only verify results without processing
- `--debug`: Enable debug logging
- `--in-situ`: Enable in-situ masking (mask documents directly in source collection)
- `--collection`: Process a specific collection (overrides collections in config)
- `--log-file`: Custom log file path
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--log-max-bytes`: Maximum log file size before rotation (default: 10MB)
- `--log-backup-count`: Number of backup log files to keep (default: 5)
- `--log-timed-rotation`: Enable time-based log rotation

### Running Tests

We've added several scripts to help run tests with different configurations:

1. **Run Specific Tests**:
   ```bash
   ./run_specific_tests.sh
   ```
   This runs specific test modules that are known to work.

2. **Run Filtered Tests**:
   ```bash
   ./run_filtered_tests.sh
   ```
   This runs all tests except those that depend on dask/pyarrow.

3. **Run Key Tests**:
   ```bash
   ./run_key_tests.sh
   ```
   This runs specific tests that have been fixed to verify they now pass.

4. **Run All Tests**:
   ```bash
   ./run_all_tests.sh
   ```
   This runs all unit tests.

## Test Environment Setup

All scripts and documentation for creating a test environment with sample data are now organized under the `test_env/` folder.

- Scripts: `test_env/create_test_samples.py`, `test_env/create_test_config.py`, `test_env/setup_test_environment.py`, `test_env/setup_test_environment.bat`
- Documentation: `test_env/TEST_ENVIRONMENT_SETUP.md`

See [test_env/TEST_ENVIRONMENT_SETUP.md](test_env/TEST_ENVIRONMENT_SETUP.md) for instructions on creating and running a test environment for orchestration and masking workflows.

### Performance Optimization

For optimal performance with large datasets, configure:

1. **Batch Size**: Set in `.env.prod` file with `PROCESSING_BATCH_SIZE` (recommended: 1000-5000)
2. **Connection Pool Size**: Adjust MongoDB connection pool settings in config file

### Windows PowerShell Wrapper Script

For Windows users, a dedicated PowerShell wrapper script (`run_masking_job.ps1`) is provided for running masking jobs in the background with automatic log file management.

#### Features
- Runs masking jobs as PowerShell background jobs
- Automatic timestamped log file creation
- Built-in error logging with separate `.err` files
- In-situ mode enabled by default
- Interactive job monitoring options

#### Usage

**Basic usage:**
```powershell
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory"
```

**With custom parameters:**
```powershell
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000 -ConfigFile "config/config_rules/config_StaffAavailability.json" -EnvFile ".env.phi" -LogDir "logs/phi"
```

#### Parameters
- `-Collection` (required): MongoDB collection name to mask
- `-BatchSize` (optional): Documents per batch (default: 9000)
- `-ConfigFile` (optional): Config file path (default: "config/config_rules/config_StaffAavailability.json")
- `-EnvFile` (optional): Environment file (default: ".env.phi")
- `-InSitu` (optional): Enable in-situ masking (enabled by default)
- `-LogDir` (optional): Log directory (default: "logs/phi")

#### Log Files
Log files are automatically created with the format:
```
logs/phi/{YYYYMMDD_HHMMSS}_masking_{CollectionName}.log
logs/phi/{YYYYMMDD_HHMMSS}_masking_{CollectionName}.log.err
```

#### Monitoring Jobs
```powershell
# Check job status
Get-Job

# View job output
Receive-Job -Id <JobId> -Keep

# Monitor log file in real-time
Get-Content -Path 'logs/phi/20251010_230303_masking_StaffAvailabilityHistory.log' -Tail 20 -Wait

# Stop a job
Stop-Job -Id <JobId>

# Remove completed job
Remove-Job -Id <JobId>
```

### Examples

1. Process a collection in production:
   ```bash
   nohup python masking.py --config config/config.json --env .env.prod > logs/prod/Patients_$(date +%Y%m%d_%H%M%S).log 2>&1 &
   ```

2. Process multiple collections in-situ:
   ```bash
   nohup python masking.py --config config/config.json --env .env.prod --in-situ --reset-checkpoint >logs/prod/nohup.out 2>&1 &
   ```

3. Process with a specific limit:
   ```bash
   source venv/Scripts/activate && python masking.py --config config/config.json --env .env.prod --limit 10000
   ```

4. Process a specific collection in-situ:
   ```bash
   source venv/Scripts/activate && python masking.py --config config/config.json --env .env.prod --in-situ --collection YourCollectionName
   ```

5. Process with a specific query:
   ```bash
   source venv/Scripts/activate && python masking.py --config config/config.json --env .env.prod --query '{"createdAt": {"$gt": {"$date": "2023-01-01T00:00:00Z"}}}'
   ```

6. Process with custom logging configuration:
   ```bash
   source venv/Scripts/activate && python masking.py --config config/config.json --env .env.prod --log-file logs/custom_log.log --log-level DEBUG --log-max-bytes 5242880 --log-backup-count 10
   ```

## Configuration

### Environment Variables

Key environment variables in `.env.prod`:

- `PROCESSING_BATCH_SIZE`: Number of documents to process in each batch (default: 100)
- `PROCESSING_DOC_LIMIT`: Maximum number of documents to process (default: 9999999999)
- `PROCESSING_CHECKPOINT_INTERVAL`: How often to save checkpoints (default: 10000)
- `MONGO_SOURCE_*`: Source MongoDB connection settings
- `MONGO_DEST_*`: Destination MongoDB connection settings

### Configuration File

Key configuration sections in `config/config.json`:

```json
{
    "mongodb": {
        "source": {
            "uri": "${MONGO_SOURCE_URI}",
            "database": "${MONGO_SOURCE_DB}",
            "collection": "${MONGO_SOURCE_COLL}"
        },
        "destination": {
            "uri": "${MONGO_DEST_URI}",
            "database": "${MONGO_DEST_DB}",
            "collection": "${MONGO_DEST_COLL}"
        }
    },
    "processing": {
        "masking_mode": "separate",
        "batch_size": {
            "initial": 50,
            "min": 10,
            "max": 200
        }
    },
    "phi_collections": [
        "Collection1",
        "Collection2",
        "Collection3"
    ]
}
```

The `phi_collections` array specifies which collections to process when running without the `--collection` parameter.

See `config/config.example.yaml` for additional configuration options.

### Masking Rules

Masking rules are defined in `config/masking_rules/rules.json`.

## Development

### Project Structure

```
MongoPHIMasker/
├── config/                 # Configuration files
│   ├── config.example.yaml # Example configuration
│   └── masking_rules/      # Masking rule definitions
├── checkpoints/            # Checkpoint files for resumable processing
├── kubernetes/             # Kubernetes deployment files
├── logs/                   # Log files
│   ├── dev/                # Development logs
│   ├── prod/               # Production logs
│   └── test/               # Test logs
├── reports/                # 
├── results/                # 
├── scripts/                # 
├── src/                    # Source code
│   ├── core/               # Core modules
│   │   ├── connector.py    # MongoDB connection handling
│   │   ├── orchestrator.py # Orchestration logic
│   │   ├── processor.py    # Document processing
│   │   ├── validator.py    # Validation logic
│   │   └── masker.py       # PHI masking implementation
│   ├── models/             # Data models
│   │   └── masking_rule.py # Masking rule definitions
│   └── utils/              # Utility modules
│       ├── compatibility.py # Backward compatibility layer
│       ├── config_loader.py # Configuration loading
│       ├── logger.py       # Logging utilities
│       └── results.py      # Results handling
├── tests/                  # Test files
│   ├── mocks/
│   ├── performance/
│   └── unit/
├── docs/                   # Documentation
├── metrics/                # Metrics collection
├── schema/                 # Schema definitions
├── .env.example            # Example environment variables
├── run_*.sh                # Test runner scripts
├── TEST_FIXES.md           # Documentation of test fixes
├── TEST_STATUS.md          # Test status report
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## In-Situ Masking

The default masking process follows a read-mask-transfer-insert approach:
1. Read documents from source database
2. Apply masking in memory
3. Transfer masked documents over network 
4. Insert into destination database

This approach is safe but introduces network transfer overhead and requires additional storage for duplicate data.

### Using In-Situ Masking

The new in-situ masking feature modifies documents directly in the source collection, eliminating network transfer overhead and reducing processing time significantly:

```bash
# Mask documents in-place
python masking.py --in-situ

# Mask specific documents in-place
python masking.py --in-situ --query '{"department": "cardiology"}'
```

### Benefits of In-Situ Masking

- **Reduced Processing Time**: Eliminates the network transfer step and destination database writes
- **Lower Resource Usage**: Minimizes memory and network bandwidth requirements
- **Space Efficiency**: No need for duplicate storage in a separate collection
- **Simplified Architecture**: Single database connection instead of source and destination

### Considerations

- **Irreversible**: Since documents are modified in-place, this approach is irreversible
- **Backup**: Always create a backup of your data before using in-situ masking
- **Testing**: Consider testing on a small subset of data first

```bash
# Perform a dry-run first to count affected documents
python masking.py --in-situ --dry-run

# Test on a small subset with query
python masking.py --in-situ --query '{"_id": {"$lt": "000000000000000000000010"}}'

# Other options (Linux/Bash)
nohup python masking.py --config config/config_rules/config_StaffAavailability.json --env .env.phi --in-situ --collection StaffAvailability >logs/phi/20251010_000000_masking_StaffAvailability.log 2>&1 & 

# PowerShell - Using the Wrapper Script (Recommended for Windows)
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000 -ConfigFile "config/config_rules/config_StaffAavailability.json" -EnvFile ".env.phi" -LogDir "logs/phi"

# PowerShell - Direct execution with background job
Start-Job -ScriptBlock {
    Set-Location "C:\Users\demesew\projects\python\mongo_phi_masker"
    .\venv-3.11\Scripts\python.exe masking.py --config config/config_rules/config_StaffAavailability.json --env .env.phi --in-situ --collection StaffAvailability *>&1 | Out-File -FilePath "logs/phi/20251010_000000_masking_StaffAvailability.log" -Encoding UTF8
}

# masking in-motion with single collection (--collection) - Linux/Bash
nohup python masking.py --config config/config.json --env .env.test --collection AD_Patients_10k >logs/preprod/nohup.log 2>&1 &

# in-situ masking with single collection (--collection)
nohup python masking.py --config config/config.json --env .env.prod --in-situ --collection StaffAvailability >logs/prod/nohup.log 2>&1 &

# in-situ masking with multiple collections from config.json
nohup python masking.py --config config/config.json --env .env.prod --in-situ >logs/prod/nohup.log 2>&1 &

# fresh in-situ masking with multiple collections from config.json (--reset-checkpoint)
nohup python masking.py --config config/config.json --env .env.prod --in-situ --reset-checkpoint >logs/prod/nohup.log 2>&1 &

# check running process with (Linux/Bash)
ps -aux | grep masking.py | grep -v grep

# check running jobs (PowerShell)
Get-Job
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# monitor progress with (Linux/Bash)
tail -10 logs/{env}/nohup.log

# monitor progress with (PowerShell)
Get-Content -Path logs/{env}/nohup.log -Tail 10 -Wait
# or receive job output
Receive-Job -Id <JobId> -Keep
```