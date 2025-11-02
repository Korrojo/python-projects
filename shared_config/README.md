# Shared Configuration

This directory contains shared environment variables and configuration for all Python projects under
`C:/Users/dabebe/projects/python/`.

## Files

- **`.env`** - Shared MongoDB URIs and connection strings
- **`app_config.json`** - Shared application settings (database, processing, export, logging)

## Setup (Optional)

`common_config` automatically finds this directory. No environment variable needed!

**Optional**: Set `COMMON_CONFIG_ENV_FILE` to override the default location:

```cmd
setx COMMON_CONFIG_ENV_FILE "C:\path\to\custom\.env"
```

## Usage

### In your project code

```python
from common_config.config import get_settings, load_shared_config

# Automatically loads shared .env
settings = get_settings()

# Load shared app_config.json
shared_cfg = load_shared_config()
batch_size = shared_cfg.get("processing", {}).get("batch_size", 1000)
```

### Configuration precedence

Environment variables are loaded in this order (last wins):

1. Shared `.env` (this directory)
1. Project `config/.env`
1. Project root `.env`
1. OS environment variables (highest priority)

### Project-specific overrides

Each project can override or add settings in their own `config/.env` file for:

- Database names
- Collection names
- Project-specific settings
