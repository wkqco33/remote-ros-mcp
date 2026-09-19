"""FastMCP Server Application for remote ROS2 gateway."""

import json
from typing import Dict, Optional

from mcp.server.fastmcp import FastMCP

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.config import BridgeConfig
from remote_ros_mcp.server.tools_action import register_action_tools
from remote_ros_mcp.server.tools_data import register_data_tools
from remote_ros_mcp.server.tools_graph import register_graph_tools
from remote_ros_mcp.server.tools_test import register_test_tools
from remote_ros_mcp.utils.ring_buffer import TopicRingBuffer


def create_mcp_server(
    client: Optional[WrosbridgeClient] = None,
    config: Optional[BridgeConfig] = None,
) -> FastMCP:
    """Create and configure FastMCP server instance."""
    if client is None:
        cfg = config or BridgeConfig.from_env()
        client = WrosbridgeClient.from_config(cfg)

    mcp = FastMCP(
        name="remote-ros-mcp",
        instructions=(
            "MCP server for remote ROS2 robotics development, "
            "inspection, and verification via wrosbridge."
        ),
    )

    buffers: Dict[str, TopicRingBuffer] = {}

    # Register Resources
    @mcp.resource("ros2://health")
    def resource_health() -> str:
        """Get live health status of wrosbridge gateway."""
        return json.dumps(client.check_health(), indent=2)

    @mcp.resource("ros2://graph/nodes")
    def resource_nodes() -> str:
        """Get current list of active ROS2 nodes and connections."""
        return json.dumps(client.get_nodes(), indent=2)

    @mcp.resource("ros2://graph/topics")
    def resource_topics() -> str:
        """Get current list of active ROS2 topics."""
        return json.dumps(client.get_topics(), indent=2)

    # Register Tools
    register_graph_tools(mcp, client)
    register_data_tools(mcp, client, buffers)
    register_action_tools(mcp, client)
    register_test_tools(mcp, client, buffers)

    return mcp
