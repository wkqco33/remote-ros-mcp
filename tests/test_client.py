"""Tests for WrosbridgeClient."""

import pytest

from remote_ros_mcp.client import WrosbridgeClient


def test_client_health(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    res = client.check_health()
    assert res["status"] == "SERVING"
    assert res["serving"] is True


def test_client_graph(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    nodes = client.get_nodes()
    assert len(nodes) >= 2
    assert any(n["name"] == "teleop_twist_keyboard" for n in nodes)

    topics = client.get_topics()
    assert any(t["topic"] == "/cmd_vel" for t in topics)


def test_client_parameters(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    # Get parameters
    params = client.get_parameters("/robot/diff_drive_controller", ["wheel_radius"])
    assert "wheel_radius" in params
    assert pytest.approx(params["wheel_radius"]) == 0.105

    # Set parameters
    set_res = client.set_parameters("/robot/diff_drive_controller", {"wheel_radius": 0.12})
    assert set_res["success"] is True

    # Check updated value
    updated = client.get_parameters("/robot/diff_drive_controller", ["wheel_radius"])
    assert pytest.approx(updated["wheel_radius"]) == 0.12


def test_client_tf_lookup(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    tf_res = client.lookup_tf(target_frame="odom", source_frame="base_link")
    assert tf_res["success"] is True
    assert tf_res["translation"]["x"] == 1.2


def test_client_publish_and_service(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)

    # Publish Twist
    twist_data = {
        "linear": {"x": 0.5, "y": 0.0, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": 1.0},
    }
    pub_res = client.publish_topic("/robot/cmd_vel", "geometry_msgs/msg/Twist", twist_data)
    assert pub_res["sequence"] >= 1

    # Call AddTwoInts service
    srv_res = client.call_service(
        "/add_two_ints", "example_interfaces/srv/AddTwoInts", {"a": 100, "b": 250}
    )
    assert srv_res["success"] is True
    assert srv_res["data"]["sum"] == 350


def test_client_action(mock_server):
    client = WrosbridgeClient(host="127.0.0.1", port=mock_server.port)
    goal_res = client.send_goal(
        action_name="/navigate_to_pose",
        action_type="nav2_msgs/action/NavigateToPose",
        goal_data={"target": "room_a"},
    )
    assert goal_res["accepted"] is True
    goal_id = goal_res["goal_id"]

    result = client.get_action_result("/navigate_to_pose", goal_id)
    assert result["status"] == "STATUS_SUCCEEDED"
