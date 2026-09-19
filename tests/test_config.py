"""Unit tests for config file management and CLI config subcommands."""

import json

import pytest
from click.testing import CliRunner

from remote_ros_mcp.cli import cli
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
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "path"])
    assert result.exit_code == 0
    assert str(temp_config_dir) in result.output.strip()


def test_cli_config_init_and_show(temp_config_dir):
    runner = CliRunner()
    # Init config
    res_init = runner.invoke(cli, ["config", "init"])
    assert res_init.exit_code == 0
    assert temp_config_dir.exists()

    # Show config json
    res_show = runner.invoke(cli, ["config", "show", "--json"])
    assert res_show.exit_code == 0
    data = json.loads(res_show.output)
    assert data["host"] == "127.0.0.1"
    assert data["port"] == 50051

    # Init without --force should inform already exists
    res_init_again = runner.invoke(cli, ["config", "init"])
    assert "already exists" in res_init_again.output.lower() or res_init_again.exit_code == 0


def test_cli_config_set(temp_config_dir):
    runner = CliRunner()
    runner.invoke(cli, ["config", "init"])

    # Set host
    res_set_host = runner.invoke(cli, ["config", "set", "host", "robot.local"])
    assert res_set_host.exit_code == 0

    # Set port (should parse to int)
    res_set_port = runner.invoke(cli, ["config", "set", "port", "50052"])
    assert res_set_port.exit_code == 0

    # Set use_tls (should parse to bool)
    res_set_tls = runner.invoke(cli, ["config", "set", "use_tls", "true"])
    assert res_set_tls.exit_code == 0

    # Verify updated values
    loaded = load_config_file(path=temp_config_dir)
    assert loaded["host"] == "robot.local"
    assert loaded["port"] == 50052
    assert loaded["use_tls"] is True

    # Invalid key should fail
    res_invalid = runner.invoke(cli, ["config", "set", "unknown_key", "value"])
    assert res_invalid.exit_code != 0
