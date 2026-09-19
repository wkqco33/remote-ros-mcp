"""Configuration for wrosbridge client and MCP server."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BridgeConfig:
    """Connection settings for remote wrosbridge gateway."""

    host: str = "127.0.0.1"
    port: int = 50051
    api_key: Optional[str] = None
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    timeout_sec: float = 5.0

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        return cls(
            host=os.getenv("ROS_BRIDGE_HOST", "127.0.0.1"),
            port=int(os.getenv("ROS_BRIDGE_PORT", "50051")),
            api_key=os.getenv("ROS_BRIDGE_API_KEY"),
            use_tls=os.getenv("ROS_BRIDGE_USE_TLS", "false").lower() in ("1", "true", "yes"),
            tls_cert_path=os.getenv("ROS_BRIDGE_TLS_CERT"),
            timeout_sec=float(os.getenv("ROS_BRIDGE_TIMEOUT_SEC", "5.0")),
        )

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"
