# Quick Start Guide - Appointment Comparison Validator

## Prerequisites Check

1. ✅ Python 3.11+ installed
1. ✅ Virtual environment activated
1. ✅ `common_config` package installed: `pip install -e ../common_config`
1. ✅ MongoDB credentials in `shared_config/.env`

## First Time Setup (One-time)

```bash
# 1. Navigate to project root
cd f:/ubiquityMongo_phiMasking/python

# 2. Install common_config if not already
pip install -e ./common_config

# 3. Verify configuration
python -c "from common_config.config import get_settings; s=get_settings(); print(f'APP_ENV={os.getenv(\"APP_ENV\")}\nDB={s.database_name}')"
```

## Quick Test Run (Recommended First)

Test with 10 rows to verify everything works:

```bash
cd appointment_comparison
python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD --limit 10
```

Expected output:

- Log file: `../../logs/appointment_comparison/{timestamp}_app.log`
- Output CSV: `../../data/output/appointment_comparison/{timestamp}_appointment_comparison_output.csv`
- Cleaned CSV: `../../data/output/appointment_comparison/Daily_Appointment_Comparison_input1_20251023_cleaned.csv`

## Full Production Run

After successful test, run full validation:

```bash
cd appointment_comparison
python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD
```

## Check Results

### View Log

```bash
# Latest log
ls -lt ../../logs/appointment_comparison/ | head -n 2

# View log content
cat ../../logs/appointment_comparison/20251023_*_app.log
```

### View Output CSV

```bash
# Open in Excel or view with less
ls -lt ../../data/output/appointment_comparison/

# View first few rows
head -n 20 ../../data/output/appointment_comparison/20251023_*_output.csv
```

### Check Statistics

Look for JSON summary at end of log or terminal output:

```json
{
  "status": "success",
  "statistics": {
    "total_rows": 4179,
    "cancelled_removed": 1523,
    "processed": 2656,
    "total_match": 2400,
    "total_mismatch": 256
  }
}
```

## Troubleshooting

### Error: "MongoDB URI and DATABASE_NAME must be set"

**Fix**: Check `shared_config/.env`

```bash
# View current config
cat ../shared_config/.env | grep -E "APP_ENV|MONGODB_URI|DATABASE_NAME"

# Should see:
# APP_ENV=PROD
# MONGODB_URI_PROD=mongodb://...
# DATABASE_NAME_PROD=UbiquityProduction
```

### Error: "Input file not found"

**Fix**: Verify file is in correct location

```bash
ls ../../data/input/appointment_comparison/
```

Expected: `Daily_Appointment_Comparison_input1_20251023.csv`

### Error: Connection timeout

**Fix**:

1. Check VPN/network connection
1. Verify MongoDB host is reachable
1. Test MongoDB connection: `ping your-mongo-host`

## Common Commands

### Test with specific row count

```bash
python run.py --input myfile.csv --env PROD --limit 50
```

### Use different environment

```bash
python run.py --input myfile.csv --env LOCL --limit 10
```

### Larger batch size (faster for big files)

```bash
python run.py --input myfile.csv --env PROD --batch-size 200
```

### Different collection

```bash
python run.py --input myfile.csv --env PROD --collection StaffAvailability_Backup
```

## Next Steps

1. ✅ Review output CSV validation results
1. ✅ Check mismatched fields for patterns
1. ✅ Investigate appointments with "AthenaAppointmentId Found? = False"
1. ✅ Share statistics JSON with stakeholders
1. ✅ Schedule regular validation runs if needed

## Support

Questions? Contact the data engineering team or check:

- Full documentation: `README.md`
- Project requirements: `../../REQUIRMENT.md`
- Common config docs: `../common_config/README.md`
