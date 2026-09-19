"""Unit tests for Testing & Verification MCP Tools."""

import json

import pytest

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.server.app import create_mcp_server


@pytest.fixture
def mcp_server_instance(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    mcp = create_mcp_server(client=client)
    return mcp, client


def _parse_tool_result(res) -> dict:
    if hasattr(res, "content"):
        return json.loads(res.content[0].text)
    if isinstance(res, tuple):
        res = res[0]
    if isinstance(res, list) and len(res) > 0 and hasattr(res[0], "text"):
        return json.loads(res[0].text)
    if isinstance(res, str):
        return json.loads(res)
    return res


async def test_mock_publish_sequence(mcp_server_instance):
    mcp, client = mcp_server_instance
    tool = mcp._tool_manager.get_tool("ros2_mock_publish_sequence")
    assert tool is not None

    sequence = [
        {"linear": {"x": 0.1, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.0}},
        {"linear": {"x": 0.2, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.0}},
        {"linear": {"x": 0.3, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.0}},
    ]
    res = await tool.run(
        arguments={
            "topic": "/robot/cmd_vel",
            "topic_type": "geometry_msgs/msg/Twist",
            "sequence": sequence,
            "interval_sec": 0.01,
        },
        context=None,
    )
    data = _parse_tool_result(res)
    assert data["published_count"] == 3
    assert data["success"] is True


async def test_assert_topic_published_from_cache(mcp_server_instance):
    mcp, client = mcp_server_instance
    pub_tool = mcp._tool_manager.get_tool("ros2_topic_publish")
    await pub_tool.run(
        arguments={
            "topic": "/robot/cmd_vel",
            "topic_type": "geometry_msgs/msg/Twist",
            "data": {
                "linear": {"x": 0.88, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": 0.0},
            },
        },
        context=None,
    )

    tool = mcp._tool_manager.get_tool("ros2_assert_topic_published")
    assert tool is not None

    # Condition: linear.x > 0.5
    res = await tool.run(
        arguments={
            "topic": "/robot/cmd_vel",
            "topic_type": "geometry_msgs/msg/Twist",
            "condition_expr": "msg['linear']['x'] > 0.5",
            "timeout_sec": 1.0,
        },
        context=None,
    )
    data = _parse_tool_result(res)
    assert data["matched"] is True
    assert data["message"]["linear"]["x"] == 0.88


async def test_record_and_inspect(mcp_server_instance):
    mcp, client = mcp_server_instance
    tool = mcp._tool_manager.get_tool("ros2_record_and_inspect")
    assert tool is not None

    res = await tool.run(
        arguments={
            "topic": "/robot/cmd_vel",
            "topic_type": "geometry_msgs/msg/Twist",
            "duration_sec": 0.1,
        },
        context=None,
    )
    data = _parse_tool_result(res)
    assert "summary" in data
    assert "sample_count" in data
