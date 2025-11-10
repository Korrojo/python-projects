"""Security utilities for credential redaction and sensitive data handling."""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse


def redact_uri(uri: Optional[str], mask: str = "***") -> str:
    """Redact credentials from a URI for safe logging.

    Args:
        uri: The URI to redact (e.g., MongoDB connection string)
        mask: The string to use for redaction (default: "***")

    Returns:
        URI with credentials replaced by mask

    Examples:
        >>> redact_uri("mongodb://user:pass@host:27017/db")
        'mongodb://***:***@host:27017/db'

        >>> redact_uri("mongodb+srv://user:pass@cluster.mongodb.net/?options")
        'mongodb+srv://***:***@cluster.mongodb.net/?options'

        >>> redact_uri(None)
        'None'

        >>> redact_uri("mongodb://localhost:27017")  # No credentials
        'mongodb://localhost:27017'
    """
    if uri is None:
        return "None"

    if not uri or not isinstance(uri, str):
        return str(uri)

    try:
        parsed = urlparse(uri)

        # If there's no username, return as-is (no credentials to redact)
        if not parsed.username:
            return uri

        # Replace username and password with mask
        netloc = parsed.netloc
        if parsed.username:
            # Handle both username:password@host and username@host
            if parsed.password:
                # Replace both username and password
                old_auth = f"{parsed.username}:{parsed.password}@"
                new_auth = f"{mask}:{mask}@"
            else:
                # Replace only username
                old_auth = f"{parsed.username}@"
                new_auth = f"{mask}@"

            netloc = netloc.replace(old_auth, new_auth)

        # Reconstruct URI with redacted credentials
        redacted = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

        return redacted

    except Exception:
        # If parsing fails, use regex as fallback
        # Pattern: protocol://username:password@host
        pattern = r"([a-zA-Z][a-zA-Z0-9+.-]*://)[^:]+:[^@]+@"
        redacted = re.sub(pattern, rf"\1{mask}:{mask}@", uri)
        return redacted


def redact_password(text: str, mask: str = "***") -> str:
    """Redact passwords from text using common patterns.

    Args:
        text: Text that may contain passwords
        mask: The string to use for redaction (default: "***")

    Returns:
        Text with passwords redacted

    Examples:
        >>> redact_password("password=secret123")
        'password=***'

        >>> redact_password("PASSWORD: secret123")
        'PASSWORD: ***'
    """
    if not text or not isinstance(text, str):
        return str(text)

    # Common password patterns
    patterns = [
        (r"(password\s*[=:]\s*)[^\s]+", rf"\1{mask}"),
        (r"(PASSWORD\s*[=:]\s*)[^\s]+", rf"\1{mask}"),
        (r"(pwd\s*[=:]\s*)[^\s]+", rf"\1{mask}"),
        (r"(PWD\s*[=:]\s*)[^\s]+", rf"\1{mask}"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def get_safe_connection_info(uri: Optional[str], database: str) -> dict:
    """Get safe connection information for logging (no credentials).

    Args:
        uri: MongoDB connection URI
        database: Database name

    Returns:
        Dictionary with safe connection info for logging

    Example:
        >>> info = get_safe_connection_info(
        ...     "mongodb+srv://user:pass@cluster.mongodb.net/?options",
        ...     "mydb"
        ... )
        >>> info['host']
        'cluster.mongodb.net'
        >>> info['uri']
        'mongodb+srv://***:***@cluster.mongodb.net/?options'
    """
    safe_info = {
        "database": database,
        "uri": redact_uri(uri),
    }

    if uri:
        try:
            parsed = urlparse(uri)
            safe_info["host"] = parsed.hostname or "unknown"
            safe_info["port"] = parsed.port
            safe_info["scheme"] = parsed.scheme
        except Exception:
            safe_info["host"] = "unknown"

    return safe_info
