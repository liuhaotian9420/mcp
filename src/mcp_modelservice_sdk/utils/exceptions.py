"""
Custom exception classes for the MCP Modelservice SDK.
"""


class TransformationError(Exception):
    """Custom exception for errors during the transformation process."""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ImportError(Exception):
    """Custom exception for import-related errors."""
    pass 