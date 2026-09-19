"""Configuration management for wrosbridge client and MCP server."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import click


def get_config_path() -> Path:
    """Return platform-standard path for remote-ros-mcp configuration file."""
    env_override = os.getenv("REMOTE_ROS_CONFIG_PATH")
    if env_override:
        return Path(env_override)
    app_dir = Path(click.get_app_dir("remote-ros-mcp"))
    return app_dir / "config.json"


def load_config_file(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration dictionary from JSON file."""
    cfg_path = path or get_config_path()
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config_file(data: Dict[str, Any], path: Optional[Path] = None):
    """Save configuration dictionary to JSON file."""
    cfg_path = path or get_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


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
    def default_dict(cls) -> Dict[str, Any]:
        """Return default configuration mapping."""
        return asdict(cls())

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        """Build configuration solely from environment variables and defaults."""
        return cls.load()

    @classmethod
    def load(
        cls,
        cli_overrides: Optional[Dict[str, Any]] = None,
        config_path: Optional[Path] = None,
    ) -> "BridgeConfig":
        """Load configuration with standard precedence: CLI > Env > File > Default."""
        # 1. Start with defaults
        cfg_dict = cls.default_dict()

        # 2. Layer config file values if present
        file_data = load_config_file(config_path)
        for k, v in file_data.items():
            if k in cfg_dict and v is not None:
                cfg_dict[k] = v

        # 3. Layer environment variables
        env_host = os.getenv("ROS_BRIDGE_HOST")
        if env_host:
            cfg_dict["host"] = env_host

        env_port = os.getenv("ROS_BRIDGE_PORT")
        if env_port:
            try:
                cfg_dict["port"] = int(env_port)
            except ValueError:
                pass

        env_api_key = os.getenv("ROS_BRIDGE_API_KEY")
        if env_api_key is not None:
            cfg_dict["api_key"] = env_api_key

        env_tls = os.getenv("ROS_BRIDGE_USE_TLS")
        if env_tls is not None:
            cfg_dict["use_tls"] = env_tls.lower() in ("1", "true", "yes")

        env_cert = os.getenv("ROS_BRIDGE_TLS_CERT")
        if env_cert is not None:
            cfg_dict["tls_cert_path"] = env_cert

        env_timeout = os.getenv("ROS_BRIDGE_TIMEOUT_SEC")
        if env_timeout:
            try:
                cfg_dict["timeout_sec"] = float(env_timeout)
            except ValueError:
                pass

        # 4. Layer CLI overrides (highest priority)
        if cli_overrides:
            for k, v in cli_overrides.items():
                if k in cfg_dict and v is not None:
                    cfg_dict[k] = v

        return cls(**cfg_dict)

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"
