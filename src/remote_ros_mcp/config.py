"""Configuration management using wpyconf (wconfig)."""

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import wconfig


def get_config_path() -> Path:
    """Return platform-standard path for remote-ros-mcp configuration file using wconfig."""
    env_override = os.getenv("REMOTE_ROS_CONFIG_PATH")
    if env_override:
        return Path(env_override)
    app_dir = wconfig.user_config_dir("remote-ros-mcp")
    return app_dir / "config.json"


def load_config_file(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration dictionary from JSON file using wconfig."""
    cfg_path = path or get_config_path()
    if not cfg_path.exists():
        return {}
    try:
        cfg = wconfig.load_config(files=(cfg_path,))
        return cfg.as_dict()
    except Exception:
        return {}


def save_config_file(data: Dict[str, Any], path: Optional[Path] = None):
    """Save configuration dictionary to JSON file using wconfig."""
    cfg_path = path or get_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = wconfig.Config()
    cfg.write_mapping(cfg_path, data, overwrite=True)


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
        cfg_path = config_path or get_config_path()
        files = (cfg_path,) if cfg_path.exists() else ()

        # 1. Use wconfig to load defaults, file, and environment variables
        cfg = wconfig.load_config(
            defaults=cls.default_dict(),
            files=files,
            env_prefix="ROS_BRIDGE",
        )
        cfg_dict = cfg.as_dict()

        # 2. Type normalization for common environment variables if needed
        if "port" in cfg_dict and cfg_dict["port"] is not None:
            try:
                cfg_dict["port"] = int(cfg_dict["port"])
            except (ValueError, TypeError):
                pass

        if "use_tls" in cfg_dict and cfg_dict["use_tls"] is not None:
            if isinstance(cfg_dict["use_tls"], str):
                cfg_dict["use_tls"] = cfg_dict["use_tls"].lower() in ("1", "true", "yes")

        if "timeout_sec" in cfg_dict and cfg_dict["timeout_sec"] is not None:
            try:
                cfg_dict["timeout_sec"] = float(cfg_dict["timeout_sec"])
            except (ValueError, TypeError):
                pass

        # 3. Layer CLI overrides (highest priority)
        if cli_overrides:
            for k, v in cli_overrides.items():
                if k in cfg_dict and v is not None:
                    cfg_dict[k] = v

        return cls(**cfg_dict)

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"
