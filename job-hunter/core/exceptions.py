"""Job Hunter custom exceptions."""


class JobHunterError(Exception):
    """Base exception."""


class DatabaseError(JobHunterError):
    """Database operation failed."""


class ProfileError(JobHunterError):
    """Profile operation failed."""


class SearchError(JobHunterError):
    """Job search failed."""


class ApplyError(JobHunterError):
    """Auto-apply failed."""


class AIError(JobHunterError):
    """AI generation failed."""


class SettingsError(JobHunterError):
    """Settings operation failed."""
