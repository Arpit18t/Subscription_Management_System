"""Custom exceptions and business rule violations."""

class BrightloopException(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundException(BrightloopException):
    """Raised when an entity is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND")


class BusinessRuleViolation(BrightloopException):
    """Raised when a business domain rule is violated."""
    def __init__(self, message: str):
        super().__init__(message, code="BUSINESS_RULE_VIOLATION")


class ConcurrencyConflictException(BrightloopException):
    """Raised when an idempotency or concurrency violation occurs."""
    def __init__(self, message: str = "Concurrent operation conflict"):
        super().__init__(message, code="CONCURRENCY_CONFLICT")


class UnauthorizedException(BrightloopException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenException(BrightloopException):
    """Raised when permission is denied."""
    def __init__(self, message: str = "Operation not permitted"):
        super().__init__(message, code="FORBIDDEN")

