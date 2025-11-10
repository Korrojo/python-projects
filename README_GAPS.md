# MongoDB PHI Masker — Gaps, Discrepancies, and Remediation Plan

This document catalogs notable inconsistencies and risks identified across code, configuration, and documentation. It
also proposes concrete remediation actions to make the project more seamless, robust, and production‑ready.

______________________________________________________________________

## Scope

- Covers code under `src/`, operational scripts in `scripts/`, and docs in project root and `config/`
- Focuses on correctness, developer experience, operability, and maintainability
- Proposes prioritized, actionable steps with clear outcomes

______________________________________________________________________

## Executive Summary (Top Gaps)

- **Python version mismatch** between docs and code typing usage (PEP 585 generics) → requires Python ≥ 3.9; recommend
  standardizing on 3.11
- **CLI/docs drift**: docs reference files/CLIs that don’t exist; dependencies include Typer/Click but CLI uses argparse
- **Logging standard vs code**: active format differs from documented standard; URIs not consistently sanitized on all
  log paths
- **Test-only logic in production code** (inspection-based branching) risks unexpected behavior and complicates
  maintenance
- **Shared config path assumptions** (`../shared_config/.env`) are rigid; missing override/fallback path
- **Windows orchestration** relies on WSL/Git Bash; no native PowerShell backup/restore alternative
- **Config/rules naming and casing**: cross-platform case sensitivity risks; orphaned PATH mappings
- **Docs reference non-existent files** (e.g., `ARCHIVE_PROPOSAL.md`, `src/cli/test_cli.py`,
  `scripts/generate_test_patients.py`)
- **Linter config suppresses many rules** (technical debt) without timeline; missing pre-commit

______________________________________________________________________

## Detailed Discrepancies and Gaps

### 1) Python Version and Typing

- Docs say: “Python 3.8+” (README). Code uses PEP 585 generics (e.g., `list[str]`), which require Python 3.9+.
- Mixed tooling references (3.11 and 3.12) across docs and helper scripts.

Impact

- Setup failures or type errors on Python 3.8.

Remediation

- Set project baseline to Python 3.11 (recommended) and test 3.12.
- Update README and scripts to a single venv name (e.g., `.venv311`).
- Add `python_requires = ">=3.11"` in packaging (when pyproject is introduced).
- Add CI matrix for 3.11 and 3.12.

______________________________________________________________________

### 2) CLI and Documentation Drift

- Dependencies include `typer`/`click`, but current primary CLI is `argparse` in `masking.py`.
- Docs reference: `src/cli/test_cli.py` (not present) and `scripts/generate_test_patients.py` (actual file:
  `generate_test_data.py`).

Impact

- Onboarding friction; confusion about the correct entry points and commands.

Remediation

- Either (A) implement a Typer-based CLI wrapper that delegates to current logic or (B) remove Typer/Click deps and
  update docs to argparse.
- Update all docs to reference `scripts/generate_test_data.py` and remove references to non-existent `test_cli.py`.
- Maintain a compatibility shim if needed (e.g., `scripts/generate_test_patients.py` calling `generate_test_data.py`).

______________________________________________________________________

### 3) Logging Standard vs Implementation

- `LOGGING_STANDARD.md` prescribes: `YYYY-MM-DD HH:MM:SS | LEVEL | message` and avoiding module names.
- `src/utils/logger.setup_logging` currently uses `%(asctime)s - %(name)s - %(levelname)s - %(message)s` by default
  (hyphens and module name included).
- URI sanitization exists in `MongoConnector._sanitize_uri`, but usage is not enforced globally when logging URIs.

Impact

- Inconsistent logs complicate parsing and monitoring; potential credential exposure in logs.

Remediation

- Align `setup_logging` format to standard for both console and file handlers.
- Centralize URI logging through a sanitization helper; ban raw-URI logging via code review/linters.
- Add an option for JSON logs (`python-json-logger`) for SIEM ingestion.

______________________________________________________________________

### 4) Test-Specific Logic in Production Code

- Several functions branch behavior when specific test function names are detected (via `inspect`), e.g., in
  `DocumentMasker` and `RuleEngine`.

Impact

- Hidden side effects; risks if function-name collisions happen; complicates reasoning and future refactors.

Remediation

- Remove inspection-based test hooks from production code.
- Use dependency injection/mocking in tests; expose explicit testing flags or test-only utilities if necessary.

______________________________________________________________________

### 5) Shared Config Path Assumptions

- `src/utils/env_config.get_shared_config_path()` enforces `../shared_config/.env` relative to the project.
- No environment override for alternate locations; errors are hard failures.

Impact

- Rigid deployment; monorepo/submodule layouts or CI runners may place configs elsewhere.

Remediation

- Support `SHARED_CONFIG_PATH` environment variable to override location.
- Add fallback to project-root `.env` when shared config is missing (with clear warnings).
- Improve error messages with actionable hints.

______________________________________________________________________

### 6) ✅ RESOLVED: Windows Orchestration Dependencies

**Status:** Resolved on 2025-11-09

**What was done:**

- ✅ Created `scripts/backup_collection.ps1` - PowerShell-native backup script
- ✅ Created `scripts/restore_collection.ps1` - PowerShell-native restore script
- ✅ Created `scripts/README.md` - Comprehensive documentation for both Bash and PowerShell versions
- ✅ Scripts support all features: environment config, compression, logging, URI masking, confirmation prompts

**Remaining (optional):**

- Add preflight checks in `.bat` wrapper to detect and fallback between Bash/PowerShell

______________________________________________________________________

### 7) MongoDB Access Layer Consistency

- `MongoConnector` encapsulates robust retry/operations; some code paths may still use raw `pymongo` directly
  (counting/iteration), diverging from the abstraction.

Impact

- Inconsistent retry/error handling; harder to mock/test uniformly.

Remediation

- Standardize on `MongoConnector` for all DB interactions or clearly document justified exceptions.
- Extend `MongoConnector` if needed (e.g., efficient count/aggregate helpers).

______________________________________________________________________

### 8) Config/Rules Naming and Casing

- Naming convention standardized to PascalCase (per `COLLECTIONS.md`), but cross-platform case sensitivity can still
  bite (Linux vs Windows).
- `COLLECTIONS.md` notes 18 orphaned `PATH_MAPPING` entries.

Impact

- Missing-file errors in Linux CI or containers; dead configuration paths.

Remediation

- Add a validation script (and pre-commit hook) that asserts every `config_*.json` points to an existing `rules_*.json`
  with correct case.
- Prune or fix orphaned `PATH_MAPPING` entries.

______________________________________________________________________

### 9) ✅ RESOLVED: Documentation References Missing

**Status:** Resolved in P0 work (2025-11-09)

**What was fixed:**

- ✅ Removed references to `ARCHIVE_PROPOSAL.md` (not needed)
- ✅ Removed references to `docs/TEST_DATA_GENERATION_PROPOSAL.md` (not needed)
- ✅ Fixed all broken doc references in QUICKSTART_TESTING.md
- ✅ Updated paths to correct locations (`schema/` at repo root, not `docs/schema/`)

**Impact:** No broken links remain; onboarding documentation is accurate.

______________________________________________________________________

### 10) Lint/Quality Gate Posture

- `.ruff.toml` suppresses many rules as “temporary” with a PR reference; no pre-commit configuration present.

Impact

- Drift accumulates; quality regressions slip through.

Remediation

- Introduce `pre-commit` with `ruff`, `black`, and `isort`.
- Gradually re-enable suppressed rules (feature branch per group) with CI gating.

______________________________________________________________________

### 11) Rule Semantics and Double-Masking

- Special-casing for phones/emails exists in both `DocumentMasker` and `RuleEngine`.

Impact

- Potential for inconsistent or redundant masking (e.g., `xxxxxxxxxx` vs random digits) depending on call path.

Remediation

- Enforce “rules-only” masking by default; move legacy/special behavior behind explicit flags or compatibility layers.
- Add tests that assert consistent outcomes for common PHI fields across both code paths.

______________________________________________________________________

### 12) Packaging and Distribution

- No `pyproject.toml`/package metadata; not installable as a CLI tool.

Impact

- Harder to integrate in CI/CD, containers, or as a dependency.

Remediation

- Add `pyproject.toml` with entry points (e.g., `masking = masking:main`).
- Publish internal package; version and changelog.

______________________________________________________________________

### 13) Dependency Hygiene

- Pinned versions are somewhat dated; unclear lower bounds; some packages unused (click/typer if argparse kept).

Impact

- Security and compatibility risks; unnecessary footprint.

Remediation

- Audit dependencies; remove unused; consider `pip-tools` for lockfiles.
- Establish scheduled dependency updates and CI tests.

______________________________________________________________________

### 14) Secrets and Email Notifications

- Email creds expected in env; ensure they are never logged and are optional.

Impact

- Risk of secret exposure in logs or task scheduler config if misconfigured.

Remediation

- Confirm secret names; document secure storage (Windows Credential Manager, vaults); ensure logging never prints email
  creds.

______________________________________________________________________

## Prioritized Remediation Plan (Actionable)

- **P0 – Correctness & Security**

  - Update Python baseline to 3.11 across docs/scripts; add CI matrix (3.11, 3.12)
  - Align logging formats to standard; enforce URI sanitization everywhere
  - Remove inspection-based test hooks from production code; refactor tests
  - Fix broken/incorrect doc references (Quickstart, README links)

- **P1 – Developer Experience & Stability**

  - Add `SHARED_CONFIG_PATH` override; fallback to project `.env` with warnings
  - Decide on CLI direction: adopt Typer or stick to argparse; update docs/deps accordingly
  - Standardize Mongo access via `MongoConnector`; extend it if needed
  - Validate config/rules casing and prune orphaned `PATH_MAPPING`
  - Introduce `pre-commit` with `ruff`, `black`, `isort`; start re‑enabling suppressed rules

- **P2 – Packaging & Operations**

  - Add `pyproject.toml` with entry points; make installable CLI
  - Provide PowerShell-native backup/restore; enhance `.bat` with preflight checks and fallbacks
  - Add optional JSON logging for aggregation; surface run IDs and correlation IDs
  - Audit and update dependencies; remove unused (e.g., click/typer if not used)

______________________________________________________________________

## Suggested Milestones

- Milestone 1 (Week 1–2): P0 items complete; docs updated; CI green
- Milestone 2 (Week 3–4): P1 items; initial pre-commit enforcement; config validation tool
- Milestone 3 (Week 5–6): P2 items; packaging; Windows-native orchestration; JSON logging option

______________________________________________________________________

## Validation Checklist (post-remediation)

- [ ] `pytest -m unit` passes on Python 3.11 and 3.12
- [ ] Logs match `YYYY-MM-DD HH:MM:SS | LEVEL | message` without module names (unless explicitly enabled)
- [ ] No test-specific branching in production code
- [ ] `--src-env/--dst-env` works with custom `SHARED_CONFIG_PATH` and with project `.env` fallback
- [ ] All README/Quickstart links resolve; no references to missing files
- [ ] `config_*` ↔ `rules_*` paths validate with case-sensitive checks
- [ ] Pre-commit hooks enforce formatting and linting locally and in CI
- [ ] CLI is consistent with docs (argparse or Typer), with stable, versioned entry points

______________________________________________________________________

## Notes

- This document will evolve as items are addressed. Consider tracking the remediation items as GitHub issues with
  labels: `P0`, `P1`, `P2`, `docs`, `logging`, `cli`, `infra`, `quality`.
