"""Testing and Verification Suite for ROS2 development."""

import asyncio
import json
import statistics
import time
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.utils.ring_buffer import TopicRingBuffer


def register_test_tools(
    mcp: FastMCP, client: WrosbridgeClient, buffers: Dict[str, TopicRingBuffer]
):
    @mcp.tool()
    async def ros2_assert_topic_published(
        topic: str,
        topic_type: str,
        condition_expr: Optional[str] = None,
        timeout_sec: float = 3.0,
    ) -> str:
        """Assert that a message matching an optional condition has been published to a topic.

        Args:
            topic: Topic to check (e.g. '/robot/cmd_vel')
            topic_type: Message type string (e.g. 'geometry_msgs/msg/Twist')
            condition_expr: Python expression evaluating 'msg' (e.g. "msg['linear']['x'] > 0.5")
            timeout_sec: Max wait duration in seconds
        """
        buf = buffers.setdefault(topic, TopicRingBuffer(capacity=100))

        def _eval_condition(msg_data: Dict[str, Any]) -> bool:
            if not condition_expr:
                return True
            try:
                # Safe eval scope with msg variable
                return bool(eval(condition_expr, {"__builtins__": {}}, {"msg": msg_data}))
            except Exception:
                return False

        # 1. Check existing buffer entries first
        all_entries = buf.get_all()
        for entry in reversed(all_entries):
            d = entry["data"].get("data", entry["data"])
            if _eval_condition(d):
                return json.dumps(
                    {
                        "matched": True,
                        "source": "cache",
                        "topic": topic,
                        "message": d,
                        "timestamp": entry["timestamp"],
                    },
                    indent=2,
                )

        # 2. Wait for incoming messages on stream
        loop = asyncio.get_event_loop()
        start_time = time.time()
        matched_msg = None

        def _listen_stream():
            try:
                for stream_msg in client.subscribe_stream(topic, topic_type, timeout=timeout_sec):
                    buf.add(stream_msg)
                    d = stream_msg.get("data", stream_msg)
                    if _eval_condition(d):
                        return d
                    if time.time() - start_time > timeout_sec:
                        break
            except Exception:
                pass
            return None

        matched_msg = await loop.run_in_executor(None, _listen_stream)

        if matched_msg:
            return json.dumps(
                {
                    "matched": True,
                    "source": "stream",
                    "topic": topic,
                    "message": matched_msg,
                },
                indent=2,
            )

        return json.dumps(
            {
                "matched": False,
                "topic": topic,
                "timeout_sec": timeout_sec,
                "condition": condition_expr,
                "message": (
                    f"No message satisfied condition '{condition_expr}' within {timeout_sec}s"
                ),
            },
            indent=2,
        )

    @mcp.tool()
    async def ros2_measure_topic_hz(
        topic: str,
        topic_type: str,
        sample_count: int = 10,
        timeout_sec: float = 5.0,
    ) -> str:
        """Measure publishing frequency (Hz) and period statistics of a topic.

        Args:
            topic: ROS2 topic to measure
            topic_type: Type of message
            sample_count: Target number of samples to record
            timeout_sec: Maximum collection time
        """
        timestamps: List[float] = []
        loop = asyncio.get_event_loop()

        def _collect():
            count = 0
            start = time.time()
            try:
                for _ in client.subscribe_stream(topic, topic_type, timeout=timeout_sec):
                    timestamps.append(time.time())
                    count += 1
                    if count >= sample_count or (time.time() - start) > timeout_sec:
                        break
            except Exception:
                pass

        await loop.run_in_executor(None, _collect)

        if len(timestamps) < 2:
            return json.dumps(
                {
                    "success": False,
                    "topic": topic,
                    "samples_received": len(timestamps),
                    "message": "Not enough samples to calculate frequency. Is topic publishing?",
                },
                indent=2,
            )

        periods = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:], strict=False)]
        avg_period = statistics.mean(periods)
        hz = 1.0 / avg_period if avg_period > 0 else 0.0
        jitter = statistics.stdev(periods) if len(periods) > 1 else 0.0

        return json.dumps(
            {
                "success": True,
                "topic": topic,
                "samples_count": len(timestamps),
                "frequency_hz": round(hz, 2),
                "average_period_sec": round(avg_period, 4),
                "min_period_sec": round(min(periods), 4),
                "max_period_sec": round(max(periods), 4),
                "jitter_sec": round(jitter, 4),
            },
            indent=2,
        )

    @mcp.tool()
    async def ros2_mock_publish_sequence(
        topic: str,
        topic_type: str,
        sequence: List[Dict[str, Any]],
        interval_sec: float = 0.1,
    ) -> str:
        """Publish a sequence of mock messages to stimulate and test subscriber nodes.

        Args:
            topic: Target topic name
            topic_type: Message type identifier
            sequence: List of JSON message objects to publish in order
            interval_sec: Delay between each published message
        """
        buf = buffers.setdefault(topic, TopicRingBuffer(capacity=100))
        published = 0
        seq_nums = []

        for item in sequence:
            res = client.publish_topic(topic, topic_type, item)
            buf.add({"topic": topic, "type": topic_type, "data": item, "sequence": res["sequence"]})
            seq_nums.append(res["sequence"])
            published += 1
            if interval_sec > 0:
                await asyncio.sleep(interval_sec)

        return json.dumps(
            {
                "success": True,
                "topic": topic,
                "published_count": published,
                "sequences": seq_nums,
            },
            indent=2,
        )

    @mcp.tool()
    async def ros2_record_and_inspect(
        topic: str,
        topic_type: str,
        duration_sec: float = 2.0,
    ) -> str:
        """Record topic messages for a period and return summary statistics.

        Args:
            topic: Topic to record
            topic_type: Message type
            duration_sec: Recording duration in seconds
        """
        buf = buffers.setdefault(topic, TopicRingBuffer(capacity=200))
        samples: List[Dict[str, Any]] = []
        loop = asyncio.get_event_loop()

        def _record():
            start = time.time()
            try:
                for msg in client.subscribe_stream(topic, topic_type, timeout=duration_sec):
                    samples.append(msg)
                    buf.add(msg)
                    if time.time() - start >= duration_sec:
                        break
            except Exception:
                pass

        await loop.run_in_executor(None, _record)

        # Fallback to buffer if stream didn't yield anything
        if not samples and buf.count() > 0:
            samples = [e["data"] for e in buf.get_all()]

        return json.dumps(
            {
                "topic": topic,
                "duration_sec": duration_sec,
                "sample_count": len(samples),
                "summary": "Captured samples successfully" if samples else "No messages captured",
                "samples_preview": samples[:5],
            },
            indent=2,
        )
