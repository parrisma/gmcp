"""Storage exceptions for access control and security"""


class PermissionDeniedError(Exception):
    """
    Raised when access to a resource is denied due to group mismatch

    This exception is used to distinguish authorization failures (group mismatch)
    from validation failures (invalid GUID format, etc.) to enable proper HTTP
    status codes: 403 Forbidden vs 400 Bad Request.
    """

    pass
