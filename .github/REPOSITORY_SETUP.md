# Repository Setup & Configuration Guide

This document provides instructions for configuring the GitHub repository settings and branch protection rules.

## Repository URL

**<https://github.com/Korrojo/python-projects>**

## Initial Setup Completed ✅

The following has been automatically configured:

- [x] Repository created with public visibility
- [x] Initial commit pushed to `main` branch
- [x] Issues enabled
- [x] Discussions enabled
- [x] Wiki disabled (using docs/ directory instead)
- [x] Projects disabled
- [x] Delete branch on merge enabled
- [x] Auto-merge enabled
- [x] Squash merge allowed
- [x] Merge commits allowed

## Manual Configuration Steps

### 1. Branch Protection Rules (Recommended)

Configure branch protection for the `main` branch:

**Settings → Branches → Add branch protection rule**

#### Branch name pattern: `main`

**Protect matching branches:**

- [x] **Require a pull request before merging**

  - [x] Require approvals: 1
  - [ ] Dismiss stale pull request approvals when new commits are pushed
  - [ ] Require review from Code Owners
  - [ ] Restrict who can dismiss pull request reviews

- [x] **Require status checks to pass before merging**

  - [x] Require branches to be up to date before merging
  - Required status checks:
    - `Code Quality & Linting`
    - `Test Suite (ubuntu-latest, 3.11)`
    - `Security Scan`
    - `CodeQL`

- [x] **Require conversation resolution before merging**

- [x] **Require signed commits** (optional but recommended)

- [ ] **Require linear history** (optional - prevents merge commits)

- [ ] **Include administrators** (optional - apply rules to admins too)

- [x] **Allow force pushes** → Specify who can force push

  - Only allow specific people/teams (maintainers only)

- [ ] **Allow deletions** (keep unchecked)

#### Additional Branch Protection (Optional)

Create similar rules for `develop` branch if using Git Flow:

**Branch name pattern: `develop`**

- Similar settings as main, but may allow fewer restrictions

### 2. Repository Topics

Add relevant topics to improve discoverability:

**Settings → General → Topics**

Suggested topics:

- `python`
- `python3`
- `mongodb`
- `pymongo`
- `data-validation`
- `data-processing`
- `healthcare`
- `csv-processing`
- `automation`
- `python311`
- `mongodb-atlas`
- `pytest`
- `black`
- `ruff`

### 3. About Section

**Settings → General → About**

- Description: ✅ Already set
- Website: (optional) Add documentation site if available
- Topics: ✅ Configure as above

### 4. Security Settings

**Settings → Security → Code security and analysis**

Enable the following:

- [x] **Dependency graph** (should be enabled by default)
- [x] **Dependabot alerts**
- [x] **Dependabot security updates**
- [x] **Grouped security updates**
- [x] **Dependabot version updates** (via `.github/dependabot.yml` - ✅ already configured)
- [x] **Code scanning** → CodeQL analysis (via workflow - ✅ already configured)
- [x] **Secret scanning**
- [x] **Push protection** (prevents pushing secrets)

### 5. Actions Permissions

**Settings → Actions → General**

- [x] **Allow all actions and reusable workflows**
- [x] **Require approval for first-time contributors**
- Workflow permissions:
  - [x] **Read repository contents and packages permissions**
  - [x] **Allow GitHub Actions to create and approve pull requests**

### 6. Environments (Optional - for production deployments)

**Settings → Environments**

Create environments for deployment protection:

#### Environment: `production`

- Required reviewers: [Add team/user]
- Wait timer: 0 minutes
- Deployment branches: Only `main` branch
- Environment secrets: Add production credentials here

### 7. Labels

**Issues → Labels**

The following labels are automatically created:

- `bug` ✅
- `enhancement` ✅
- `dependencies` ✅ (via Dependabot)
- `python` ✅ (via Dependabot)
- `github-actions` ✅ (via Dependabot)

**Recommended additional labels:**

| Label                        | Color    | Description                                |
| ---------------------------- | -------- | ------------------------------------------ |
| `documentation`              | `0075ca` | Improvements or additions to documentation |
| `good first issue`           | `7057ff` | Good for newcomers                         |
| `help wanted`                | `008672` | Extra attention is needed                  |
| `question`                   | `d876e3` | Further information is requested           |
| `wontfix`                    | `ffffff` | This will not be worked on                 |
| `duplicate`                  | `cfd3d7` | This issue or PR already exists            |
| `invalid`                    | `e4e669` | This doesn't seem right                    |
| `performance`                | `f9d0c4` | Performance improvements                   |
| `refactor`                   | `fbca04` | Code refactoring                           |
| `testing`                    | `0e8a16` | Related to testing                         |
| `security`                   | `b60205` | Security-related issues                    |
| `project:common_config`      | `c5def5` | Related to common_config                   |
| `project:patients_validator` | `c5def5` | Related to patients_hcmid_validator        |
| `project:automate_refresh`   | `c5def5` | Related to automate_refresh                |

### 8. Collaborators & Teams (If working with a team)

**Settings → Collaborators and teams**

- Add collaborators with appropriate permissions
- Create teams for different project areas
- Configure code review assignments

### 9. Webhooks & Integrations (Optional)

**Settings → Webhooks**

Consider adding webhooks for:

- Slack/Discord notifications
- CI/CD pipelines
- Issue tracking systems
- Code coverage services (Codecov)

### 10. GitHub Pages (Optional)

**Settings → Pages**

If you want to host documentation:

- Source: Deploy from a branch
- Branch: `gh-pages` or `main` with `/docs` folder
- Custom domain: (optional)

## Verification Checklist

After configuration, verify:

- [ ] CI/CD workflows run successfully
- [ ] Branch protection prevents direct pushes to main
- [ ] Dependabot creates PRs for dependency updates
- [ ] Security scanning alerts appear in Security tab
- [ ] Issue templates work correctly
- [ ] PR template appears on new PRs
- [ ] Labels are properly configured
- [ ] Repository description and topics are visible

## Best Practices for Repository Management

### Commit Messages

Follow Conventional Commits format:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Testing updates

### Pull Request Workflow

1. Create feature branch from `main`
1. Make changes and commit
1. Push branch and create PR
1. Wait for CI checks to pass
1. Request review
1. Address feedback
1. Merge when approved

### Release Process

1. Update CHANGELOG.md
1. Bump version in relevant files
1. Create and push version tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
1. Push tag: `git push origin v1.0.0`
1. GitHub Actions will create release automatically

### Security

- Never commit `.env` files
- Keep dependencies updated
- Review and fix Dependabot alerts promptly
- Rotate credentials if exposed
- Use environment secrets for sensitive data

## Useful Commands

### View Repository Info

```bash
gh repo view Korrojo/python-projects
```

### Open Repository in Browser

```bash
gh repo view Korrojo/python-projects --web
```

### Clone Repository

```bash
gh repo clone Korrojo/python-projects
# OR
git clone https://github.com/Korrojo/python-projects.git
```

### Create Issue

```bash
gh issue create --title "Bug: Something broken" --body "Description here"
```

### Create Pull Request

```bash
gh pr create --title "feat: Add new feature" --body "Description here"
```

### View CI Status

```bash
gh run list --limit 10
gh run view [run-id]
```

## Support & Resources

- **Repository**: <https://github.com/Korrojo/python-projects>
- **Issues**: <https://github.com/Korrojo/python-projects/issues>
- **Discussions**: <https://github.com/Korrojo/python-projects/discussions>
- **Documentation**: See `/docs` directory
- **Contributing**: See `CONTRIBUTING.md`
- **Security**: See `SECURITY.md`

## Monitoring & Maintenance

### Weekly Tasks

- [ ] Review and merge Dependabot PRs
- [ ] Check GitHub Security alerts
- [ ] Review open issues and PRs
- [ ] Update documentation as needed

### Monthly Tasks

- [ ] Review repository analytics
- [ ] Update dependencies manually if needed
- [ ] Archive inactive issues
- [ ] Review and update labels

### Quarterly Tasks

- [ ] Major dependency updates
- [ ] Security audit
- [ ] Documentation review
- [ ] Repository settings review

______________________________________________________________________

Last updated: 2025-01-26
