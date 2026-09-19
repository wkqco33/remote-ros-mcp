"""Logging setup using wpylog (wlogger)."""

import os
import sys
from typing import Optional

import wlogger


def setup_logger(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
):
    """Configure structured logging using wlogger."""
    env_level = os.getenv("ROS_BRIDGE_LOG_LEVEL", "INFO").upper()
    eff_level = level or env_level
    if eff_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        eff_level = "INFO"

    wlogger.setup(
        level=eff_level,  # type: ignore
        log_file=log_file,
        console_stream=sys.stderr,
    )


def get_logger(name: str = "remote_ros_mcp"):
    """Get named logger from wlogger."""
    return wlogger.get_logger(name)
