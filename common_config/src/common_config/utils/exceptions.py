class CommonConfigError(Exception):
    """Base exception for common_config."""


class ValidationError(CommonConfigError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class DatabaseError(CommonConfigError):
    pass


class DataProcessingError(CommonConfigError):
    pass
