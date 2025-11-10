# Quick Reference Card

## 🚀 Three-Step Workflow

### 1️⃣ Transform CSV

```bash
python src/transformers/transform_csv_data.py \
  --input "data/input/YOUR_FILE.csv" \
  --output "data/output/YOUR_FILE_transformed.csv"
```

### 2️⃣ Update MongoDB

```bash
python src/core/update_mongodb_from_csv.py \
  --csv "data/output/patient_demographic/YOUR_FILE_transformed.csv"
```

### 3️⃣ Validate

```bash
python validate_prod_vs_training.py
```

______________________________________________________________________

## 📁 File Locations

| What            | Where                              |
| --------------- | ---------------------------------- |
| Raw CSV files   | `data/input/patient_demographic/`  |
| Transformed CSV | `data/output/patient_demographic/` |
| Logs            | `logs/patient_demographic/`        |

______________________________________________________________________

## 🔧 Configuration

Unified-only via `shared_config/.env` + `common_config` with `APP_ENV` and suffixed keys (e.g., `MONGODB_URI_TRNG`).

______________________________________________________________________

## 📊 CSV Column Mapping

| CSV Column              | MongoDB Field            | Type                 |
| ----------------------- | ------------------------ | -------------------- |
| `ptnt bqty lgcy ptnt d` | `PatientId`              | Integer (7-digit)    |
| `patientid`             | `AthenaPatientId`        | Integer (4-digit)    |
| `patient name`          | `FirstName` + `LastName` | String               |
| `patientdob`            | `Dob`                    | Date                 |
| `patientsex`            | `Gender`                 | String (Female/Male) |
| `patient email`         | `Email`                  | String               |
| `patient address1`      | `Address.Street1`        | String               |
| `patient city`          | `Address.City`           | String               |
| `patient state`         | `Address.StateCode`      | String               |
| `patient zip`           | `Address.Zip5`           | String               |
| `patient homephone`     | `Phones.PhoneNumber`     | String (10 digits)   |

______________________________________________________________________

## 🔍 Check Logs

```bash
# Latest transformation log
ls -lt logs/patient_demographic/*transform* | head -1

# Latest update log
ls -lt logs/patient_demographic/*update* | head -1

# Latest validation log
ls -lt logs/patient_demographic/*validation* | head -1
```

______________________________________________________________________

## ⚠️ Common Issues

| Issue               | Solution                                     |
| ------------------- | -------------------------------------------- |
| Connection failed   | Check `shared_config/.env` and `APP_ENV`     |
| PatientId not found | Verify PatientIds exist in collection        |
| Type error          | Check CSV has numeric values in ID columns   |
| Date parsing error  | Verify date format is MM/DD/YY or MM/DD/YYYY |

______________________________________________________________________

## 📞 Python Version

Use Python 3.11:

```bash
"/c/Users/dabebe/AppData/Local/Programs/Python/Python311/python.exe"
```

______________________________________________________________________

## 🎯 Success Indicators

✅ Transformation log shows "Transformation completed successfully!"\
✅ Update log shows "Successfully updated PatientId: XXXXX"\
✅ Validation log shows "Success Rate: 100.0%"\
✅ No errors in any log files

______________________________________________________________________

## 📝 Quick Commands

```bash
# Count transformed records
wc -l data/output/YOUR_FILE_transformed.csv

# Check environment config
cat env/env.trng

# View latest log
tail -50 logs/$(ls -t logs/ | head -1)

# Clean old logs (30+ days)
find logs/ -name "*.log" -mtime +30 -delete
```

______________________________________________________________________

**For Full Documentation**: See [README.md](README.md)
