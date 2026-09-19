"""Codec registry for ROS2 topics and services."""

from typing import Dict

from remote_ros_mcp.codecs.base import MessageCodec
from remote_ros_mcp.codecs.standard import (
    AddTwoIntsReqCodec,
    AddTwoIntsResCodec,
    BoolCodec,
    FallbackCodec,
    Float32Codec,
    Float64Codec,
    Int32Codec,
    Int64Codec,
    PointCodec,
    PoseCodec,
    QuaternionCodec,
    SetBoolReqCodec,
    SetBoolResCodec,
    StringCodec,
    TriggerReqCodec,
    TriggerResCodec,
    TwistCodec,
    Vector3Codec,
)


class CodecRegistry:
    """Central registry mapping ROS2 message/service type strings to MessageCodecs."""

    _TOPIC_CODECS: Dict[str, MessageCodec] = {
        "std_msgs/msg/String": StringCodec(),
        "std_msgs/msg/Bool": BoolCodec(),
        "std_msgs/msg/Int32": Int32Codec(),
        "std_msgs/msg/Int64": Int64Codec(),
        "std_msgs/msg/Float32": Float32Codec(),
        "std_msgs/msg/Float64": Float64Codec(),
        "geometry_msgs/msg/Vector3": Vector3Codec(),
        "geometry_msgs/msg/Point": PointCodec(),
        "geometry_msgs/msg/Quaternion": QuaternionCodec(),
        "geometry_msgs/msg/Twist": TwistCodec(),
        "geometry_msgs/msg/Pose": PoseCodec(),
    }

    _SERVICE_REQ_CODECS: Dict[str, MessageCodec] = {
        "example_interfaces/srv/AddTwoInts": AddTwoIntsReqCodec(),
        "std_srvs/srv/SetBool": SetBoolReqCodec(),
        "std_srvs/srv/Trigger": TriggerReqCodec(),
    }

    _SERVICE_RES_CODECS: Dict[str, MessageCodec] = {
        "example_interfaces/srv/AddTwoInts": AddTwoIntsResCodec(),
        "std_srvs/srv/SetBool": SetBoolResCodec(),
        "std_srvs/srv/Trigger": TriggerResCodec(),
    }

    _FALLBACK_CODEC = FallbackCodec()

    @classmethod
    def get(cls, message_type: str) -> MessageCodec:
        """Return registered topic codec or fallback codec."""
        clean_type = message_type.strip()
        if clean_type in cls._TOPIC_CODECS:
            return cls._TOPIC_CODECS[clean_type]
        return cls._FALLBACK_CODEC

    @classmethod
    def get_service_req(cls, service_type: str) -> MessageCodec:
        """Return registered service request codec or fallback codec."""
        clean_type = service_type.strip()
        if clean_type in cls._SERVICE_REQ_CODECS:
            return cls._SERVICE_REQ_CODECS[clean_type]
        return cls._FALLBACK_CODEC

    @classmethod
    def get_service_res(cls, service_type: str) -> MessageCodec:
        """Return registered service response codec or fallback codec."""
        clean_type = service_type.strip()
        if clean_type in cls._SERVICE_RES_CODECS:
            return cls._SERVICE_RES_CODECS[clean_type]
        return cls._FALLBACK_CODEC

    @classmethod
    def register_topic(cls, message_type: str, codec: MessageCodec):
        cls._TOPIC_CODECS[message_type.strip()] = codec

    @classmethod
    def register_service(cls, service_type: str, req_codec: MessageCodec, res_codec: MessageCodec):
        cls._SERVICE_REQ_CODECS[service_type.strip()] = req_codec
        cls._SERVICE_RES_CODECS[service_type.strip()] = res_codec
