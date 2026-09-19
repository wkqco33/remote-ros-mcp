"""Unit tests for CLI commands using wpycli."""

import io
import json

from remote_ros_mcp.cli import build_cli


def test_cli_test_connection_json(mock_server):
    cmd = build_cli()
    out = io.StringIO()
    err = io.StringIO()
    code = cmd.execute(
        ["--host", "127.0.0.1", "--port", str(mock_server.port), "test-connection", "--json"],
        stdout=out,
        stderr=err,
    )
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["serving"] is True
    assert data["status"] == "SERVING"


def test_cli_test_connection_failure():
    cmd = build_cli()
    out = io.StringIO()
    err = io.StringIO()
    # Port 59999 should fail
    code = cmd.execute(
        ["--host", "127.0.0.1", "--port", "59999", "--timeout", "0.5", "test-connection", "--json"],
        stdout=out,
        stderr=err,
    )
    assert code != 0
    data = json.loads(out.getvalue())
    assert data["serving"] is False


def test_cli_inspect_json(mock_server):
    cmd = build_cli()
    out = io.StringIO()
    err = io.StringIO()
    code = cmd.execute(
        ["--host", "127.0.0.1", "--port", str(mock_server.port), "inspect", "--json"],
        stdout=out,
        stderr=err,
    )
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["nodes_count"] >= 2
    assert "topics" in data
    assert "services" in data
