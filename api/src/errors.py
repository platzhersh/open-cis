"""Domain exceptions for Open CIS.

Custom exception hierarchy that maps to structured HTTP error responses
via global exception handlers in main.py.
"""


class OpenCISError(Exception):
    """Base exception for Open CIS."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class EHRBaseValidationError(OpenCISError):
    """EHRBase rejected the composition (FLAT format errors, missing fields, etc.)."""

    pass


class EHRBaseUnavailableError(OpenCISError):
    """EHRBase is not reachable or returned a non-application error."""

    pass


class PatientNotFoundError(OpenCISError):
    """Patient does not exist or has no EHR."""

    pass


class CompositionNotFoundError(OpenCISError):
    """Composition UID does not exist."""

    pass
