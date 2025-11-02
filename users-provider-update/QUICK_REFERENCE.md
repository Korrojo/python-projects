# Quick Reference Card

## 🚀 Two-Step Workflow

### 1️⃣ Update Users Collection

```bash
python src/core/update_users_from_csv.py \
  --csv "data/input/users-provider-update/provider_20250910.csv"
```

### 2️⃣ Validate Updates

```bash
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_20250910.csv" \
  --sample 10
```

______________________________________________________________________

## 📁 File Locations

| What          | Where                               |
| ------------- | ----------------------------------- |
| Raw CSV files | `data/input/users-provider-update/` |
| Logs          | `logs/users-provider-update/`       |

______________________________________________________________________

## 🔧 Configuration

Uses unified `shared_config/.env` via `common_config` with `APP_ENV` and suffixed keys like `MONGODB_URI_TRNG`,
`DATABASE_NAME_TRNG`.

______________________________________________________________________

## 📊 CSV Column Mapping

| CSV Column  | MongoDB Field             | Type    |
| ----------- | ------------------------- | ------- |
| `ID`        | `AthenaProviderId`        | Integer |
| `First`     | Match against `FirstName` | String  |
| `Last`      | Match against `LastName`  | String  |
| `User Name` | `AthenaUserName`          | String  |
| `NPI`       | `NPI`                     | String  |

______________________________________________________________________

## 🔍 Check Logs

```bash
# Latest update log
ls -lt logs/users-provider-update/*_update_users_from_csv.log | head -1

# Latest validation log
ls -lt logs/users-provider-update/*_validation_users_update.log | head -1

# View log
tail -50 logs/$(ls -t logs/ | head -1)
```

______________________________________________________________________

## ⚠️ Common Issues

| Issue             | Solution                                              |
| ----------------- | ----------------------------------------------------- |
| Connection failed | Check `shared_config/.env` and `APP_ENV`              |
| CSV not found     | Verify file is in `data/input/users-provider-update/` |
| No updates        | Check users have `IsActive: true`                     |
| Import error      | Run `pip install -r requirements.txt`                 |

______________________________________________________________________

## 📝 Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Create sample CSV (first 3 rows)
head -4 data/input/users-provider-update/provider_20250910.csv > data/input/users-provider-update/provider_sample.csv

# Test with sample
python src/core/update_users_from_csv.py \
  --csv "data/input/users-provider-update/provider_sample.csv"

# Validate sample
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_sample.csv"

# Clean old logs (30+ days)
find logs/users-provider-update/ -name "*.log" -mtime +30 -delete
```

______________________________________________________________________

## 🎯 Success Indicators

✅ Update log shows "Successfully updated user..."\
✅ Summary shows successful updates count\
✅ Validation shows high match rate (>90%)\
✅ No errors in log files

______________________________________________________________________

## 📋 Processing Rules

- ✅ Only `IsActive: true` users are updated
- ✅ Case-insensitive name matching
- ✅ Duplicates are skipped (all matching records)
- ✅ Users with existing `AthenaProviderId` are skipped
- ✅ Updates 3 fields: `AthenaProviderId`, `AthenaUserName`, `NPI`

______________________________________________________________________

**For Full Documentation**: See [README.md](README.md)
