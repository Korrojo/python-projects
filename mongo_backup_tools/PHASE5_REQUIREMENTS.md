# Phase 5: Production-Ready MongoDB Connection Options

## Overview

Add enterprise-grade MongoDB connection options required for production environments, particularly for MongoDB Atlas,
secured clusters, and authentication mechanisms beyond basic username/password.

## Current State

### ✅ Implemented

- `--uri` - MongoDB connection string
- `--host` - MongoDB host
- `--port` - MongoDB port
- `--username` / `-u` - Username
- `--password` / `-p` - Password
- `--auth-db` - Authentication database

### ❌ Missing Critical Features

1. **Authentication Mechanisms**
1. **TLS/SSL Support**
1. **Client Certificates**
1. **URI-First Approach**

______________________________________________________________________

## Requirements

### 1. Authentication Mechanisms

**MongoDB Authentication Mechanisms:**

- `SCRAM-SHA-1` - Default for MongoDB 3.0+
- `SCRAM-SHA-256` - Default for MongoDB 4.0+
- `MONGODB-CR` - Legacy (deprecated)
- `MONGODB-X509` - Certificate-based authentication
- `GSSAPI` - Kerberos authentication
- `PLAIN` - LDAP authentication
- `MONGODB-AWS` - AWS IAM authentication

**CLI Parameter:**

```bash
--auth-mechanism <mechanism>
```

**mongodump/restore/export/import equivalent:**

```bash
mongodump --authenticationMechanism=SCRAM-SHA-256
```

**Use Cases:**

- MongoDB Atlas: Often requires `SCRAM-SHA-256`
- Enterprise deployments with Kerberos: Requires `GSSAPI`
- X.509 certificate authentication: Requires `MONGODB-X509`
- AWS DocumentDB: May require specific mechanisms

**Model Changes:**

```python
class ConnectionOptions(BaseModel):
    auth_mechanism: Optional[str] = Field(
        None,
        description="Authentication mechanism (SCRAM-SHA-1, SCRAM-SHA-256, MONGODB-X509, etc.)",
    )
```

**Shell Script Mapping:**

```bash
if [ -n "$AUTH_MECHANISM" ]; then
    MONGODUMP_ARGS+=" --authenticationMechanism=$AUTH_MECHANISM"
fi
```

______________________________________________________________________

### 2. TLS/SSL Support

**Required Options:**

#### 2.1 Enable TLS/SSL

```bash
--tls / --ssl
```

**mongodump equivalent:**

```bash
mongodump --tls  # or --ssl for older versions
```

**Use Case:** Required for MongoDB Atlas and any secured MongoDB instance

#### 2.2 TLS Certificate Key File

```bash
--tls-certificate-key-file <path>
--tlsCertificateKeyFile <path>  # Alternative naming
```

**mongodump equivalent:**

```bash
mongodump --tlsCertificateKeyFile=/path/to/client.pem
```

**Use Case:** Client certificate for mutual TLS authentication

#### 2.3 TLS CA File

```bash
--tls-ca-file <path>
--tlsCAFile <path>  # Alternative naming
```

**mongodump equivalent:**

```bash
mongodump --tlsCAFile=/path/to/ca.pem
```

**Use Case:** Custom Certificate Authority certificate

#### 2.4 TLS Certificate Key File Password

```bash
--tls-certificate-key-file-password <password>
```

**mongodump equivalent:**

```bash
mongodump --tlsCertificateKeyFilePassword=secret
```

**Use Case:** Encrypted client certificates

#### 2.5 TLS Allow Invalid Certificates

```bash
--tls-allow-invalid-certificates
--tlsAllowInvalidCertificates
```

**mongodump equivalent:**

```bash
mongodump --tlsAllowInvalidCertificates
```

**Use Case:** Development/testing with self-signed certificates (NOT for production)

#### 2.6 TLS Allow Invalid Hostnames

```bash
--tls-allow-invalid-hostnames
```

**mongodump equivalent:**

```bash
mongodump --tlsAllowInvalidHostnames
```

**Use Case:** When certificate hostname doesn't match server hostname

**Model Changes:**

```python
class ConnectionOptions(BaseModel):
    use_tls: bool = Field(False, description="Enable TLS/SSL")
    tls_certificate_key_file: Optional[Path] = Field(
        None, description="TLS client certificate file"
    )
    tls_ca_file: Optional[Path] = Field(None, description="TLS CA certificate file")
    tls_certificate_key_file_password: Optional[str] = Field(
        None, description="TLS certificate password"
    )
    tls_allow_invalid_certificates: bool = Field(
        False, description="Allow invalid TLS certificates"
    )
    tls_allow_invalid_hostnames: bool = Field(
        False, description="Allow invalid TLS hostnames"
    )
```

______________________________________________________________________

### 3. Dump-Specific Options

#### 3.1 Exclude Collections

```bash
--exclude-collection <name>
```

**mongodump equivalent:**

```bash
mongodump --excludeCollection=system.profile
```

**Use Case:** Skip system collections or large collections not needed for backup

**Can be specified multiple times:**

```bash
--exclude-collection logs --exclude-collection temp_data
```

#### 3.2 Exclude Collections with Prefix

```bash
--exclude-collections-with-prefix <prefix>
```

**mongodump equivalent:**

```bash
mongodump --excludeCollectionsWithPrefix=temp_
```

**Use Case:** Exclude all temporary or cache collections with common prefix

**Can be specified multiple times:**

```bash
--exclude-collections-with-prefix temp_ --exclude-collections-with-prefix cache_
```

#### 3.3 Query File

```bash
--query-file <path>
```

**mongodump equivalent:**

```bash
mongodump --queryFile=/path/to/query.json
```

**Use Case:** Complex query filters too large for command line

**Example query.json:**

```json
{
  "createdAt": {
    "$gte": {"$date": "2024-01-01T00:00:00Z"},
    "$lt": {"$date": "2024-12-31T23:59:59Z"}
  },
  "status": {"$in": ["active", "pending"]}
}
```

#### 3.4 Quiet Mode (Dump)

```bash
--quiet
```

**mongodump equivalent:**

```bash
mongodump --quiet
```

**Use Case:** Suppress verbose output for automated scripts/cron jobs

______________________________________________________________________

### 4. Restore-Specific Options

#### 4.1 Namespace Include Pattern

```bash
--ns-include <pattern>
```

**mongorestore equivalent:**

```bash
mongorestore --nsInclude="test.*"
mongorestore --nsInclude="reporting.*"
```

**Use Case:** Restore only specific namespaces using wildcards

**Can be specified multiple times:**

```bash
--ns-include "test.*" --ns-include "prod.users"
```

**Wildcard Examples:**

- `test.*` - All collections in test database
- `*.users` - users collection in all databases
- `prod_*.*` - All collections in databases starting with prod\_

#### 4.2 Namespace Exclude Pattern

```bash
--ns-exclude <pattern>
```

**mongorestore equivalent:**

```bash
mongorestore --nsExclude="test.*"
```

**Use Case:** Restore everything except specific patterns

**Can be specified multiple times:**

```bash
--ns-exclude "*.logs" --ns-exclude "temp.*"
```

#### 4.3 Dry Run

```bash
--dry-run
```

**mongorestore equivalent:**

```bash
mongorestore --dryRun
```

**Use Case:** Preview what would be restored without actually restoring

**Useful with --verbose:**

```bash
--dry-run --verbose
```

#### 4.4 No Index Restore

```bash
--no-index-restore
```

**mongorestore equivalent:**

```bash
mongorestore --noIndexRestore
```

**Use Case:**

- Restore data faster (skip index rebuilding)
- Manually create optimized indexes later
- Troubleshoot index issues

#### 4.5 Num Insertion Workers Per Collection

```bash
--num-insertion-workers <int>
```

**mongorestore equivalent:**

```bash
mongorestore --numInsertionWorkersPerCollection=4
```

**Default:** 1

**Use Case:** Speed up restore of large collections

**Note:** For single collection restore, `-j` maps to this option

#### 4.6 Quiet Mode (Restore)

```bash
--quiet
```

**mongorestore equivalent:**

```bash
mongorestore --quiet
```

**Use Case:** Suppress verbose output for automated scripts

______________________________________________________________________

### 5. Additional Connection Options

#### 5.1 Read Preference

```bash
--read-preference <mode>
```

**Values:** `primary`, `primaryPreferred`, `secondary`, `secondaryPreferred`, `nearest`

**mongodump equivalent:**

```bash
mongodump --readPreference=secondaryPreferred
```

**Use Case:** Read from secondaries to reduce load on primary

#### 5.2 Replica Set Name

```bash
--replica-set-name <name>
```

**mongodump equivalent:**

```bash
mongodump --replicaSet=myReplicaSet
```

**Use Case:** Connecting to replica sets

#### 5.3 Connection Timeout

```bash
--connect-timeout <ms>
```

**mongodump equivalent:**

```bash
mongodump --connectTimeout=10000
```

**Use Case:** Slow networks or distant servers

#### 5.4 Socket Timeout

```bash
--socket-timeout <ms>
```

**mongodump equivalent:**

```bash
mongodump --socketTimeout=30000
```

______________________________________________________________________

### 4. URI-First Approach

**Current Problem:** Individual options (--host, --port) override --uri, causing confusion

**Required Behavior:**

1. If `--uri` is provided, use it exclusively
1. Individual options only supplement URI if specific components are missing
1. Validate that conflicting options aren't provided together

**Model Changes:**

```python
@model_validator(mode="after")
def validate_connection_precedence(self):
    """Ensure URI takes precedence over individual options."""
    if self.connection.uri:
        # If URI is provided, individual options should not override it
        if any(
            [
                self.connection.host != "localhost",
                self.connection.port != 27017,
                self.connection.username,
                self.connection.password,
            ]
        ):
            logger.warning(
                "Both --uri and individual connection options provided. "
                "URI takes precedence. Individual options will be ignored."
            )
    return self
```

______________________________________________________________________

## Implementation Plan

### Phase 5.1: Authentication Mechanism

**Files to Modify:**

1. `src/models/base.py` - Add `auth_mechanism` field
1. `src/cli.py` - Add `--auth-mechanism` option to all commands
1. `src/scripts/libs/config_parser.sh` - Parse auth mechanism
1. `src/scripts/*/mongo*.sh` - Pass to MongoDB tools
1. Tests - Add auth mechanism tests

**Estimated Effort:** 2-3 hours

### Phase 5.2: TLS/SSL Support

**Files to Modify:**

1. `src/models/base.py` - Add all TLS fields
1. `src/cli.py` - Add all TLS options (6 new flags)
1. `src/scripts/libs/config_parser.sh` - Parse TLS options
1. `src/scripts/*/mongo*.sh` - Pass to MongoDB tools
1. Tests - Add TLS tests (mock certificates)

**Estimated Effort:** 4-5 hours

### Phase 5.3: Additional Connection Options

**Files to Modify:**

1. `src/models/base.py` - Add connection options
1. `src/cli.py` - Add CLI flags
1. `src/scripts/libs/config_parser.sh` - Parse options
1. `src/scripts/*/mongo*.sh` - Pass to MongoDB tools
1. Tests - Add connection option tests

**Estimated Effort:** 2-3 hours

### Phase 5.4: URI-First Approach

**Files to Modify:**

1. `src/models/base.py` - Add validation logic
1. `src/cli.py` - Update help text to clarify precedence
1. Documentation - Update README and TESTING.md

**Estimated Effort:** 1-2 hours

### Phase 5.5: Documentation & Testing

**Deliverables:**

1. Update README.md with new options
1. Update TESTING.md with TLS/auth examples
1. Add E2E tests for Atlas connection
1. Add unit tests for all new options

**Estimated Effort:** 3-4 hours

______________________________________________________________________

## Priority Order

### P0 (Critical - Blocks Atlas usage)

1. ✅ `--tls` / `--ssl` flag
1. ✅ `--auth-mechanism`
1. ✅ URI-first approach

### P1 (High - Common production need)

4. ✅ `--tls-ca-file`
1. ✅ `--tls-certificate-key-file`
1. ✅ `--read-preference`
1. ✅ `--replica-set-name`

### P2 (Medium - Less common but useful)

8. ⚠️ `--tls-certificate-key-file-password`
1. ⚠️ `--tls-allow-invalid-certificates`
1. ⚠️ `--tls-allow-invalid-hostnames`
1. ⚠️ `--connect-timeout`
1. ⚠️ `--socket-timeout`

______________________________________________________________________

## Example Usage (After Implementation)

### MongoDB Atlas with TLS

```bash
python3 run.py dump \
  --uri "mongodb+srv://user:pass@cluster.mongodb.net/mydb" \
  --tls \
  --auth-mechanism SCRAM-SHA-256 \
  --out /backups/atlas_dump
```

### Self-Hosted with Client Certificate

```bash
python3 run.py dump \
  --host mongodb.example.com \
  --port 27017 \
  --tls \
  --tls-certificate-key-file /certs/client.pem \
  --tls-ca-file /certs/ca.pem \
  --auth-mechanism MONGODB-X509 \
  --database mydb
```

### Replica Set with Read Preference

```bash
python3 run.py export \
  --uri "mongodb://host1,host2,host3/mydb" \
  --replica-set-name myReplSet \
  --read-preference secondaryPreferred \
  --database mydb \
  --collection users \
  --out users.json
```

______________________________________________________________________

## Testing Requirements

### Unit Tests

- [ ] Test auth mechanism parsing
- [ ] Test TLS option validation
- [ ] Test URI precedence logic
- [ ] Test invalid certificate combinations

### Integration Tests

- [ ] Mock MongoDB with TLS (using testcontainers)
- [ ] Test auth mechanism switching
- [ ] Test certificate validation

### E2E Tests

- [ ] Test with MongoDB Atlas (requires credentials)
- [ ] Test with local TLS-enabled MongoDB
- [ ] Test with X.509 certificates

______________________________________________________________________

## Documentation Updates

### README.md

Add section: "Advanced Connection Options"

- Authentication mechanisms
- TLS/SSL configuration
- Production deployment examples

### TESTING.md

Add test scenarios:

- Test 6: TLS Connection
- Test 7: Atlas Connection
- Test 8: X.509 Authentication

______________________________________________________________________

## Backward Compatibility

**Breaking Changes:** None

**Deprecations:** None

**New Defaults:**

- `use_tls`: `False` (opt-in for backward compatibility)
- `auth_mechanism`: `None` (MongoDB tools use default)

______________________________________________________________________

## Success Criteria

1. ✅ Can connect to MongoDB Atlas with TLS
1. ✅ Can use all SCRAM authentication mechanisms
1. ✅ Can authenticate with X.509 certificates
1. ✅ URI takes precedence over individual options
1. ✅ All options passed correctly to MongoDB tools
1. ✅ Comprehensive test coverage
1. ✅ Updated documentation

______________________________________________________________________

## Questions for User

1. **Priority:** Implement all P0+P1 features, or just P0 to unblock Atlas?
1. **Testing:** Do you have MongoDB Atlas credentials for E2E testing?
1. **X.509:** Do you have X.509 certificates for testing, or should we mock?
1. **Timeline:** Implement all at once, or incremental PRs per feature?

______________________________________________________________________

**Created:** 2025-11-13 **Status:** Draft - Awaiting Approval **Estimated Total Effort:** 12-17 hours
