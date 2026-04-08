class IntelPlatformError(Exception):
    """Base exception for Intel Platform."""

class APIError(IntelPlatformError):
    """External API request failed."""
    def __init__(self, source: str, message: str, status_code: int = 0):
        self.source = source
        self.status_code = status_code
        super().__init__(f"[{source}] {message} (HTTP {status_code})")

class RateLimitError(APIError):
    """Rate limit exceeded for an API."""

class ConfigError(IntelPlatformError):
    """Missing or invalid configuration."""

class DatabaseError(IntelPlatformError):
    """SQLite operation failed."""

class ParseError(IntelPlatformError):
    """Failed to parse response data."""

class NotFoundError(IntelPlatformError):
    """Requested resource not found."""
