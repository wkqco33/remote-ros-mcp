"""Error definitions for remote-ros-mcp."""


class BridgeError(Exception):
    """Base error for wrosbridge communication."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.code = code


class BridgeConnectionError(BridgeError):
    """Raised when cannot connect to wrosbridge gateway."""

    def __init__(self, message: str):
        super().__init__(message, code="UNAVAILABLE")


class BridgeTimeoutError(BridgeError):
    """Raised when operation times out."""

    def __init__(self, message: str):
        super().__init__(message, code="DEADLINE_EXCEEDED")


class ServiceCallError(BridgeError):
    """Raised when ROS2 service invocation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="SERVICE_ERROR")
