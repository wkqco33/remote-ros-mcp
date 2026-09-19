"""Tests for ROS2 CDR <-> Python Dict/JSON Codec Engine."""

import pytest

from remote_ros_mcp.codecs.registry import CodecRegistry


def test_twist_roundtrip():
    codec = CodecRegistry.get("geometry_msgs/msg/Twist")
    assert codec is not None

    sample_dict = {
        "linear": {"x": 1.5, "y": -0.5, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": 0.8},
    }

    cdr_bytes = codec.encode(sample_dict)
    assert isinstance(cdr_bytes, bytes)
    # Check CDR header for Little Endian
    assert cdr_bytes[:4] == b"\x00\x01\x00\x00"

    decoded = codec.decode(cdr_bytes)
    assert pytest.approx(decoded["linear"]["x"]) == 1.5
    assert pytest.approx(decoded["linear"]["y"]) == -0.5
    assert pytest.approx(decoded["angular"]["z"]) == 0.8


def test_std_msgs_string_roundtrip():
    codec = CodecRegistry.get("std_msgs/msg/String")
    assert codec is not None

    sample = {"data": "Hello ROS2 MCP Gateway!"}
    encoded = codec.encode(sample)
    decoded = codec.decode(encoded)
    assert decoded["data"] == "Hello ROS2 MCP Gateway!"


def test_std_msgs_primitives():
    # Int64
    codec_int = CodecRegistry.get("std_msgs/msg/Int64")
    encoded_int = codec_int.encode({"data": 1234567890123})
    assert codec_int.decode(encoded_int)["data"] == 1234567890123

    # Float64
    codec_float = CodecRegistry.get("std_msgs/msg/Float64")
    encoded_float = codec_float.encode({"data": 3.1415926535})
    assert pytest.approx(codec_float.decode(encoded_float)["data"]) == 3.1415926535

    # Bool
    codec_bool = CodecRegistry.get("std_msgs/msg/Bool")
    encoded_bool = codec_bool.encode({"data": True})
    assert codec_bool.decode(encoded_bool)["data"] is True


def test_service_codecs():
    # AddTwoInts
    req_codec = CodecRegistry.get_service_req("example_interfaces/srv/AddTwoInts")
    res_codec = CodecRegistry.get_service_res("example_interfaces/srv/AddTwoInts")

    req_bytes = req_codec.encode({"a": 42, "b": 58})
    assert req_codec.decode(req_bytes) == {"a": 42, "b": 58}

    res_bytes = res_codec.encode({"sum": 100})
    assert res_codec.decode(res_bytes) == {"sum": 100}

    # SetBool
    sb_req_codec = CodecRegistry.get_service_req("std_srvs/srv/SetBool")
    sb_res_codec = CodecRegistry.get_service_res("std_srvs/srv/SetBool")

    sb_req_bytes = sb_req_codec.encode({"data": True})
    assert sb_req_codec.decode(sb_req_bytes) == {"data": True}

    sb_res_bytes = sb_res_codec.encode({"success": True, "message": "Power turned on"})
    assert sb_res_codec.decode(sb_res_bytes) == {"success": True, "message": "Power turned on"}


def test_pose_and_quaternion():
    codec = CodecRegistry.get("geometry_msgs/msg/Pose")
    sample = {
        "position": {"x": 1.0, "y": 2.0, "z": 3.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
    }
    encoded = codec.encode(sample)
    decoded = codec.decode(encoded)
    assert decoded["position"]["x"] == 1.0
    assert decoded["orientation"]["w"] == 1.0


def test_unknown_type_fallback():
    # Unknown type should return FallbackCodec which encodes/decodes raw bytes or dict
    codec = CodecRegistry.get("unknown_pkg/msg/UnknownType")
    assert codec is not None

    sample_raw = b"\x00\x01\x00\x00test-raw-bytes"
    decoded = codec.decode(sample_raw)
    assert "raw_hex" in decoded or "data" in decoded
