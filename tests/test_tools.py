"""Unit tests for FastMCP Tools."""

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
        # In case FastMCP returns (content, ...)
        res = res[0]
    if isinstance(res, list) and len(res) > 0 and hasattr(res[0], "text"):
        return json.loads(res[0].text)
    if isinstance(res, str):
        return json.loads(res)
    return res


async def test_tool_health_check(mcp_server_instance):
    mcp, client = mcp_server_instance
    tool = mcp._tool_manager.get_tool("ros2_health_check")
    assert tool is not None
    res = await tool.run(arguments={}, context=None)
    data = _parse_tool_result(res)
    assert data["serving"] is True


async def test_tool_get_nodes_and_topics(mcp_server_instance):
    mcp, client = mcp_server_instance
    get_nodes_tool = mcp._tool_manager.get_tool("ros2_get_nodes")
    res_nodes = await get_nodes_tool.run(arguments={}, context=None)
    nodes = _parse_tool_result(res_nodes)
    assert len(nodes) >= 2

    get_topics_tool = mcp._tool_manager.get_tool("ros2_get_topics")
    res_topics = await get_topics_tool.run(arguments={}, context=None)
    topics = _parse_tool_result(res_topics)
    assert any(t["topic"] == "/cmd_vel" for t in topics)


async def test_tool_parameters(mcp_server_instance):
    mcp, client = mcp_server_instance
    set_tool = mcp._tool_manager.get_tool("ros2_set_parameters")
    await set_tool.run(
        arguments={
            "node_name": "/robot/diff_drive_controller",
            "parameters": {"wheel_radius": 0.15},
        },
        context=None,
    )

    get_tool = mcp._tool_manager.get_tool("ros2_get_parameters")
    res = await get_tool.run(
        arguments={
            "node_name": "/robot/diff_drive_controller",
            "names": ["wheel_radius"],
        },
        context=None,
    )
    data = _parse_tool_result(res)
    assert pytest.approx(data["wheel_radius"]) == 0.15


async def test_tool_lookup_tf(mcp_server_instance):
    mcp, client = mcp_server_instance
    tool = mcp._tool_manager.get_tool("ros2_lookup_tf")
    res = await tool.run(
        arguments={"target_frame": "odom", "source_frame": "base_link"}, context=None
    )
    data = _parse_tool_result(res)
    assert data["success"] is True
    assert data["translation"]["x"] == 1.2


async def test_tool_publish_and_service(mcp_server_instance):
    mcp, client = mcp_server_instance
    pub_tool = mcp._tool_manager.get_tool("ros2_topic_publish")
    res_pub = await pub_tool.run(
        arguments={
            "topic": "/robot/cmd_vel",
            "topic_type": "geometry_msgs/msg/Twist",
            "data": {
                "linear": {"x": 1.0, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": 0.5},
            },
        },
        context=None,
    )
    pub_data = _parse_tool_result(res_pub)
    assert pub_data["sequence"] >= 1

    call_tool = mcp._tool_manager.get_tool("ros2_call_service")
    res_call = await call_tool.run(
        arguments={
            "service": "/add_two_ints",
            "service_type": "example_interfaces/srv/AddTwoInts",
            "request_data": {"a": 25, "b": 75},
        },
        context=None,
    )
    call_data = _parse_tool_result(res_call)
    assert call_data["success"] is True
    assert call_data["data"]["sum"] == 100


async def test_tool_action(mcp_server_instance):
    mcp, client = mcp_server_instance
    action_tool = mcp._tool_manager.get_tool("ros2_action_send_goal")
    res = await action_tool.run(
        arguments={
            "action_name": "/navigate_to_pose",
            "action_type": "nav2_msgs/action/NavigateToPose",
            "goal_data": {"x": 5.0, "y": 2.0},
        },
        context=None,
    )
    data = _parse_tool_result(res)
    assert data["accepted"] is True
    assert data["status"] == "STATUS_SUCCEEDED"
