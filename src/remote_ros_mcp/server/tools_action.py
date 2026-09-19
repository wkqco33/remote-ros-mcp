"""Action server tools for ROS2 Actions."""

import asyncio
import json
import time
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from remote_ros_mcp.client import WrosbridgeClient


def register_action_tools(mcp: FastMCP, client: WrosbridgeClient):
    @mcp.tool()
    async def ros2_action_send_goal(
        action_name: str,
        action_type: str,
        goal_data: Dict[str, Any],
        wait_for_result: bool = True,
        timeout_sec: float = 30.0,
    ) -> str:
        """Send a goal to a ROS2 Action server and optionally wait for result.

        Args:
            action_name: Name of the action (e.g. '/navigate_to_pose')
            action_type: Action type identifier (e.g. 'nav2_msgs/action/NavigateToPose')
            goal_data: Goal definition as JSON dict
            wait_for_result: Whether to block until goal completes or times out
            timeout_sec: Maximum timeout to wait for result
        """
        send_res = client.send_goal(
            action_name=action_name, action_type=action_type, goal_data=goal_data
        )
        if not send_res.get("accepted"):
            return json.dumps(
                {
                    "accepted": False,
                    "action_name": action_name,
                    "message": send_res.get("message", "Goal rejected"),
                },
                indent=2,
            )

        goal_id = send_res["goal_id"]
        if not wait_for_result:
            return json.dumps(
                {
                    "accepted": True,
                    "goal_id": goal_id,
                    "action_name": action_name,
                    "message": "Goal accepted and executing asynchronously",
                },
                indent=2,
            )

        loop = asyncio.get_event_loop()
        start_time = time.time()
        final_result = None

        while time.time() - start_time < timeout_sec:
            res = await loop.run_in_executor(
                None, lambda: client.get_action_result(action_name, goal_id)
            )
            status = res.get("status")
            if status in ("STATUS_SUCCEEDED", "STATUS_CANCELED", "STATUS_ABORTED"):
                final_result = res
                break
            await asyncio.sleep(0.5)

        if not final_result:
            return json.dumps(
                {
                    "accepted": True,
                    "goal_id": goal_id,
                    "action_name": action_name,
                    "status": "TIMEOUT",
                    "message": f"Action did not complete within {timeout_sec}s",
                },
                indent=2,
            )

        return json.dumps(
            {
                "accepted": True,
                "goal_id": goal_id,
                "action_name": action_name,
                "status": final_result["status"],
                "message": final_result["message"],
            },
            indent=2,
        )

    @mcp.tool()
    async def ros2_action_cancel_goal(action_name: str, goal_id: str) -> str:
        """Cancel an executing ROS2 action goal.

        Args:
            action_name: Name of the action
            goal_id: Identifier of the goal to cancel
        """
        res = client.cancel_goal(action_name=action_name, goal_id=goal_id)
        return json.dumps(res, indent=2)
