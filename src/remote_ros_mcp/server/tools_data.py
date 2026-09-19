"""Data exchange tools: publish, echo, and service calls."""

import asyncio
import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.utils.ring_buffer import TopicRingBuffer


def register_data_tools(
    mcp: FastMCP, client: WrosbridgeClient, buffers: Dict[str, TopicRingBuffer]
):
    @mcp.tool()
    async def ros2_topic_publish(topic: str, topic_type: str, data: Dict[str, Any]) -> str:
        """Publish a message to a ROS2 topic.

        Args:
            topic: ROS2 topic name (e.g. '/robot/cmd_vel')
            topic_type: Message type string (e.g. 'geometry_msgs/msg/Twist')
            data: Message content as JSON object/dict
        """
        res = client.publish_topic(topic=topic, topic_type=topic_type, data=data)
        # Store in local ring buffer for quick inspection
        buf = buffers.setdefault(topic, TopicRingBuffer(capacity=100))
        buf.add({"topic": topic, "type": topic_type, "data": data, "sequence": res["sequence"]})
        return json.dumps(res, indent=2)

    @mcp.tool()
    async def ros2_topic_echo(
        topic: str,
        topic_type: str,
        count: int = 1,
        timeout_sec: float = 3.0,
    ) -> str:
        """Capture and return messages from a ROS2 topic.

        Args:
            topic: Topic name to listen to (e.g. '/robot/cmd_vel')
            topic_type: Message type (e.g. 'geometry_msgs/msg/Twist')
            count: Number of messages to capture (default 1)
            timeout_sec: Maximum time to wait in seconds
        """
        # First check if we already have recent messages in buffer
        buf = buffers.get(topic)
        collected: List[Dict[str, Any]] = []

        if buf and buf.count() > 0:
            all_entries = buf.get_all()
            for entry in reversed(all_entries):
                collected.append(entry["data"])
                if len(collected) >= count:
                    break

        if not collected:
            # Attempt to pull from stream
            loop = asyncio.get_event_loop()

            def _pull_stream():
                results = []
                try:
                    for msg in client.subscribe_stream(topic, topic_type, timeout=timeout_sec):
                        results.append(msg)
                        if len(results) >= count:
                            break
                except Exception:
                    pass
                return results

            collected = await loop.run_in_executor(None, _pull_stream)

        return json.dumps(
            {
                "topic": topic,
                "type": topic_type,
                "count": len(collected),
                "messages": collected,
            },
            indent=2,
        )

    @mcp.tool()
    async def ros2_call_service(
        service: str,
        service_type: str,
        request_data: Dict[str, Any],
        timeout_sec: Optional[float] = 5.0,
    ) -> str:
        """Call a ROS2 service and receive the response.

        Args:
            service: Service name (e.g. '/add_two_ints' or '/robot/reset_odometry')
            service_type: Service type (e.g. 'example_interfaces/srv/AddTwoInts')
            request_data: Request parameters as JSON object/dict
            timeout_sec: Maximum wait time for service response
        """
        res = client.call_service(
            service=service,
            service_type=service_type,
            request_data=request_data,
            timeout_sec=timeout_sec,
        )
        return json.dumps(res, indent=2)
