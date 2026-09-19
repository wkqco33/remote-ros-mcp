"""Graph, node, parameter, and TF introspection tools."""

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from remote_ros_mcp.client import WrosbridgeClient


def register_graph_tools(mcp: FastMCP, client: WrosbridgeClient):
    @mcp.tool()
    async def ros2_health_check() -> str:
        """Check the connection and serving health of the remote wrosbridge gateway."""
        res = client.check_health()
        return json.dumps(res, indent=2)

    @mcp.tool()
    async def ros2_get_nodes() -> str:
        """List all active ROS2 nodes with namespace, pub/sub topics, and services."""
        nodes = client.get_nodes()
        return json.dumps(nodes, indent=2)

    @mcp.tool()
    async def ros2_get_topics() -> str:
        """List all available ROS2 topics along with their publisher and subscriber nodes."""
        topics = client.get_topics()
        return json.dumps(topics, indent=2)

    @mcp.tool()
    async def ros2_get_services() -> str:
        """List all active ROS2 services available in the graph."""
        services = client.get_services()
        return json.dumps(services, indent=2)

    @mcp.tool()
    async def ros2_get_parameters(node_name: str, names: List[str]) -> str:
        """Get parameter values for a specific ROS2 node.

        Args:
            node_name: Full name of the node (e.g. '/robot/diff_drive_controller')
            names: List of parameter names to read
        """
        params = client.get_parameters(node_name, names)
        return json.dumps(params, indent=2)

    @mcp.tool()
    async def ros2_set_parameters(node_name: str, parameters: Dict[str, Any]) -> str:
        """Set runtime parameters for a specific ROS2 node.

        Args:
            node_name: Full name of the node (e.g. '/robot/diff_drive_controller')
            parameters: Key-value dictionary of parameters to update
        """
        res = client.set_parameters(node_name, parameters)
        return json.dumps(res, indent=2)

    @mcp.tool()
    async def ros2_lookup_tf(
        target_frame: str, source_frame: str, timeout_sec: Optional[float] = 5.0
    ) -> str:
        """Lookup geometric coordinate transform between two frames from ROS2 TF tree.

        Args:
            target_frame: Target coordinate frame (e.g. 'odom' or 'map')
            source_frame: Source coordinate frame (e.g. 'base_link' or 'camera_link')
            timeout_sec: Timeout in seconds
        """
        res = client.lookup_tf(
            target_frame=target_frame, source_frame=source_frame, timeout_sec=timeout_sec
        )
        return json.dumps(res, indent=2)
