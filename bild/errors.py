class BildAPIError(Exception):
    """Generic API error for non-success responses."""

    def __init__(self, message: str, status_code: int | None = None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BildAuthError(BildAPIError):
    """Raised when auth fails (401/403)."""
