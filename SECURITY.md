# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of our software seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

Please report security vulnerabilities by emailing: **48iaemm5@duck.com**

Include the following information:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response:** Within 48 hours of report submission
- **Status Update:** Within 7 days with assessment of the issue
- **Fix Timeline:** Depends on severity and complexity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

### Disclosure Policy

- We follow coordinated disclosure principles
- Security issues are disclosed once a fix is available
- Reporter will be credited (unless anonymity is requested)
- CVE may be requested for significant vulnerabilities

## Security Best Practices

When using this codebase:

### Environment Variables and Secrets

- **NEVER** commit `.env` files containing credentials
- Use `shared_config/.env.example` as a template
- Store production secrets in secure secret management systems
- Rotate credentials regularly

### MongoDB Connections

- Always use connection strings with authentication
- Enable TLS/SSL for production databases
- Use read-only credentials where write access isn't needed
- Implement IP whitelisting
- Use MongoDB Atlas network access controls

### Data Handling

- Sanitize all user inputs
- Never log sensitive data (passwords, API keys, PII)
- Use prepared statements/parameterized queries
- Implement proper error handling (don't expose stack traces)

### Dependencies

- Keep dependencies updated
- Review Dependabot alerts promptly
- Use `pip audit` to check for known vulnerabilities
- Pin dependency versions in production

### Code Quality

- Follow linting rules (configured in `pyproject.toml`)
- Run tests before commits
- Use type hints for better code safety
- Enable all Ruff security rules

## Security Checklist for Contributors

Before submitting code:

- [ ] No hardcoded credentials or API keys
- [ ] No sensitive data in logs or error messages
- [ ] Input validation implemented
- [ ] Error handling doesn't expose system information
- [ ] Dependencies are up to date
- [ ] Tests cover security-relevant code paths
- [ ] Documentation updated for security-relevant changes

## Known Security Considerations

### MongoDB Injection

This codebase uses PyMongo which provides protection against MongoDB injection when using proper query construction. However:

- Always validate and sanitize user inputs
- Use PyMongo's query operators properly
- Avoid constructing queries from string concatenation

### File Operations

Several projects handle file uploads and processing:

- File paths are validated against directory traversal
- File size limits should be enforced
- File types are validated
- Temporary files are cleaned up

### Authentication

This codebase primarily handles database operations:

- Database authentication is required
- Connection strings should use SRV records with TLS
- Credentials must be stored in environment variables

## Acknowledgments

We appreciate the security research community's efforts in keeping open-source software secure. Security researchers who responsibly disclose vulnerabilities will be acknowledged in our release notes (unless they prefer to remain anonymous).

## Updates to This Policy

This security policy may be updated from time to time. Please check back periodically for changes.

Last updated: 2025-01-26
