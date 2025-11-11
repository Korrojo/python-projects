# Branch Cleanup Action Plan

Generated: 2025-11-16

## Summary

Reviewed 5 key branches to determine merge/delete actions.

## Immediate Actions

### 🗑️ Safe to Delete (Work Already Incorporated)

#### 1. `feature/mongo-backup-tools-phase1`

**Reason:** Duplicate of work merged via PR #64 (commit 9f1c576)

**Unique commits:** 1 (commit 81a9b57 - same as 9f1c576)

**Action:**

```bash
git branch -D feature/mongo-backup-tools-phase1
```

#### 2. `feature/mongo-backup-tools-phase2`

**Reason:** All Phase 2 shell scripts incorporated into Phase 5

**Unique commits:** 2

- `e95f001` - Remove broken test (cleanup, not needed)
- `3aa3499` - Phase 2 shell infrastructure (already in phase5)

**Verification:** Scripts exist in `mongo_backup_tools/src/scripts/`

**Action:**

```bash
git branch -D feature/mongo-backup-tools-phase2
```

### 🔀 Should Merge Then Delete

#### 3. `feature/mongo-backup-tools-phase4`

**Reason:** Has 2 useful fixes not yet in main/phase5

**Unique commits not in main/phase5:** 2

- `4d87a73` - Fix markdown formatting in staff_appointment_visitStatus README
- `6afe197` - Fix CodeQL empty except blocks in E2E test fixtures

**Action:**

```bash
# Option A: Cherry-pick specific commits to main
git checkout main
git cherry-pick 6afe197  # CodeQL fix
git cherry-pick 4d87a73  # Markdown fix
git push origin main

# Then delete branch
git branch -D feature/mongo-backup-tools-phase4
git push origin --delete feature/mongo-backup-tools-phase4
```

**OR**

```bash
# Option B: Merge entire branch to main
git checkout main
git merge feature/mongo-backup-tools-phase4 --no-ff
git push origin main
git branch -D feature/mongo-backup-tools-phase4
```

#### 4. `chore/cleanup-gitignore`

**Reason:** Has 2 test-related commits useful for main

**Unique commits:** 2

- `cf8d7d9` - Add @pytest.mark.unit to root-level smoke tests
- `5dc9b0b` - Remove broken integration test for non-existent sample_project

**Action:**

```bash
# Cherry-pick to main
git checkout main
git cherry-pick 5dc9b0b  # Remove broken test
git cherry-pick cf8d7d9  # Add pytest markers
git push origin main

# Delete branch
git branch -D chore/cleanup-gitignore
```

#### 5. `feat/readme-quick-wins`

**Reason:** Has 4 valuable commits (type fixes, security, docs)

**Unique commits:** 4

- `1a923fc` - Fix 15 type safety issues in MongoConnector
- `1e95cba` - Mark section 9 (stale doc references) as resolved
- `f75262d` - Centralize URI sanitization in common_config (SECURITY!)
- `7f190c3` - Standardize Python version to 3.11+ across all READMEs

**Priority:** HIGH (security fix + type safety improvements)

**Action:**

```bash
# Merge to main (preserve all commits)
git checkout main
git merge feat/readme-quick-wins --no-ff -m "Merge feat/readme-quick-wins: type fixes, security, and docs"
git push origin main

# Delete branch
git branch -D feat/readme-quick-wins
git push origin --delete feat/readme-quick-wins
```

## Execution Order

### Step 1: Delete Safe Branches (No Merge Needed)

```bash
# Delete phase1 and phase2 locally
git branch -D feature/mongo-backup-tools-phase1
git branch -D feature/mongo-backup-tools-phase2

# No remote deletion needed (already deleted or never pushed)
```

### Step 2: Merge Important Changes to Main

```bash
# Checkout main and pull latest
git checkout main
git pull origin main

# Merge readme-quick-wins (PRIORITY - has security fix)
git merge feat/readme-quick-wins --no-ff -m "Merge feat/readme-quick-wins: type fixes, security, and docs"

# Cherry-pick from phase4
git cherry-pick 6afe197  # CodeQL fix
git cherry-pick 4d87a73  # Markdown fix

# Cherry-pick from cleanup-gitignore
git cherry-pick 5dc9b0b  # Remove broken test
git cherry-pick cf8d7d9  # Add pytest markers

# Push all changes to main
git push origin main
```

### Step 3: Delete Merged Branches

```bash
# Local deletion
git branch -D feature/mongo-backup-tools-phase4
git branch -D chore/cleanup-gitignore
git branch -D feat/readme-quick-wins

# Remote deletion
git push origin --delete feat/readme-quick-wins
# (phase4 and cleanup-gitignore may not have remotes)
```

### Step 4: Update Current Branch (phase5)

```bash
# Return to phase5 and merge main to stay current
git checkout phase5-production-connection-options
git merge main
git push origin phase5-production-connection-options
```

## Summary Stats

- **Branches to delete without merge:** 2 (phase1, phase2)
- **Branches to merge then delete:** 3 (phase4, cleanup-gitignore, readme-quick-wins)
- **Total commits to preserve:** 8
  - Security fixes: 1
  - Type safety fixes: 1
  - Documentation: 2
  - Test improvements: 2
  - Code quality: 2

## Risk Assessment

- **Low risk:** Deleting phase1, phase2 (duplicates)
- **Medium risk:** Cherry-picking individual commits (may have conflicts)
- **High value:** Merging readme-quick-wins (security + type safety)

## Next Steps After Cleanup

1. Run full test suite on main
1. Verify all changes work correctly
1. Consider creating a PR for phase5 to main when ready
