"""Unit tests for CLI commands."""

import json

from click.testing import CliRunner

from remote_ros_mcp.cli import cli


def test_cli_test_connection_json(mock_server):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--host", "127.0.0.1", "--port", str(mock_server.port), "test-connection", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["serving"] is True
    assert data["status"] == "SERVING"


def test_cli_test_connection_failure():
    runner = CliRunner()
    # Port 59999 should fail
    result = runner.invoke(
        cli,
        ["--host", "127.0.0.1", "--port", "59999", "--timeout", "0.5", "test-connection", "--json"],
    )
    assert result.exit_code != 0
    data = json.loads(result.output)
    assert data["serving"] is False


def test_cli_inspect_json(mock_server):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--host", "127.0.0.1", "--port", str(mock_server.port), "inspect", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["nodes_count"] >= 2
    assert "topics" in data
    assert "services" in data
