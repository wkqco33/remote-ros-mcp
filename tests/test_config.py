"""Unit tests for config file management and CLI config subcommands."""

import io
import json

import pytest

from remote_ros_mcp.cli import build_cli
from remote_ros_mcp.config import (
    BridgeConfig,
    get_config_path,
    load_config_file,
    save_config_file,
)


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    custom_path = tmp_path / "remote-ros-mcp" / "config.json"
    monkeypatch.setenv("REMOTE_ROS_CONFIG_PATH", str(custom_path))
    return custom_path


def test_get_config_path_default_and_override(monkeypatch, tmp_path):
    monkeypatch.delenv("REMOTE_ROS_CONFIG_PATH", raising=False)
    default_p = get_config_path()
    assert "remote-ros-mcp" in str(default_p)
    assert default_p.name == "config.json"

    custom = tmp_path / "custom_config.json"
    monkeypatch.setenv("REMOTE_ROS_CONFIG_PATH", str(custom))
    assert get_config_path() == custom


def test_save_and_load_config_file(temp_config_dir):
    data = {
        "host": "192.168.0.10",
        "port": 50055,
        "api_key": "test-key-123",
        "use_tls": True,
        "tls_cert_path": "/tmp/cert.pem",
        "timeout_sec": 10.0,
    }
    save_config_file(data, path=temp_config_dir)
    assert temp_config_dir.exists()

    loaded = load_config_file(path=temp_config_dir)
    assert loaded["host"] == "192.168.0.10"
    assert loaded["port"] == 50055
    assert loaded["use_tls"] is True


def test_bridge_config_load_priority(temp_config_dir, monkeypatch):
    # 1. Config file has base values
    save_config_file(
        {"host": "config-host", "port": 50010, "timeout_sec": 3.0},
        path=temp_config_dir,
    )

    # 2. Env var overrides host
    monkeypatch.setenv("ROS_BRIDGE_HOST", "env-host")

    # 3. CLI override for port
    cfg = BridgeConfig.load(
        cli_overrides={"port": 50099},
        config_path=temp_config_dir,
    )

    assert cfg.host == "env-host"  # Env overrides file
    assert cfg.port == 50099  # CLI overrides all
    assert cfg.timeout_sec == 3.0  # From file


def test_cli_config_path(temp_config_dir):
    cmd = build_cli()
    out = io.StringIO()
    code = cmd.execute(["config", "path"], stdout=out)
    assert code == 0
    assert str(temp_config_dir) in out.getvalue().strip()


def test_cli_config_init_and_show(temp_config_dir):
    cmd = build_cli()
    out = io.StringIO()
    err = io.StringIO()

    # Init config
    code_init = cmd.execute(["config", "init"], stdout=out, stderr=err)
    assert code_init == 0
    assert temp_config_dir.exists()

    # Show config json
    out_show = io.StringIO()
    code_show = cmd.execute(["config", "show", "--json"], stdout=out_show)
    assert code_show == 0
    data = json.loads(out_show.getvalue())
    assert data["host"] == "127.0.0.1"
    assert data["port"] == 50051

    # Init without --force should inform already exists
    err_again = io.StringIO()
    code_again = cmd.execute(["config", "init"], stderr=err_again)
    assert code_again == 0
    assert "already exists" in err_again.getvalue().lower()


def test_cli_config_set(temp_config_dir):
    cmd = build_cli()
    cmd.execute(["config", "init"])

    # Set host
    code_set_host = cmd.execute(["config", "set", "host", "robot.local"])
    assert code_set_host == 0

    # Set port (should parse to int)
    code_set_port = cmd.execute(["config", "set", "port", "50052"])
    assert code_set_port == 0

    # Set use_tls (should parse to bool)
    code_set_tls = cmd.execute(["config", "set", "use_tls", "true"])
    assert code_set_tls == 0

    # Verify updated values
    loaded = load_config_file(path=temp_config_dir)
    assert loaded["host"] == "robot.local"
    assert loaded["port"] == 50052
    assert loaded["use_tls"] is True

    # Invalid key should fail
    err_invalid = io.StringIO()
    code_invalid = cmd.execute(["config", "set", "unknown_key", "value"], stderr=err_invalid)
    assert code_invalid != 0
