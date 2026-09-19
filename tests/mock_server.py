"""In-memory Mock wrosbridge gRPC server for testing."""

from concurrent import futures
from typing import Dict, List

import grpc

from remote_ros_mcp.proto.wrosbridge.v1 import (
    action_pb2,
    action_pb2_grpc,
    admin_pb2,
    admin_pb2_grpc,
    common_pb2,
    health_pb2,
    health_pb2_grpc,
    service_pb2,
    service_pb2_grpc,
    topic_pb2,
    topic_pb2_grpc,
)


class MockHealthServicer(health_pb2_grpc.HealthServicer):
    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.ServingStatus.SERVING
        )


class MockAdminServicer(admin_pb2_grpc.AdminServiceServicer):
    def __init__(self):
        self.nodes = [
            admin_pb2.GraphNodeInfo(
                node_name="teleop_twist_keyboard",
                node_namespace="/",
                published_topics=["/cmd_vel"],
                subscribed_topics=[],
                services=[],
            ),
            admin_pb2.GraphNodeInfo(
                node_name="diff_drive_controller",
                node_namespace="/robot",
                published_topics=["/robot/odom"],
                subscribed_topics=["/robot/cmd_vel"],
                services=["/robot/reset_odometry"],
            ),
        ]
        self.params: Dict[str, Dict[str, admin_pb2.ParameterValue]] = {
            "/robot/diff_drive_controller": {
                "wheel_radius": admin_pb2.ParameterValue(
                    type=admin_pb2.ParameterType.PARAM_DOUBLE, double_value=0.105
                ),
                "max_linear_speed": admin_pb2.ParameterValue(
                    type=admin_pb2.ParameterType.PARAM_DOUBLE, double_value=1.5
                ),
            }
        }

    def GetGraph(self, request, context):
        return admin_pb2.GetGraphResponse(nodes=self.nodes)

    def GetParameters(self, request, context):
        node_params = self.params.get(request.node_name, {})
        res = []
        for name in request.names:
            if name in node_params:
                res.append(admin_pb2.Parameter(name=name, value=node_params[name]))
        return admin_pb2.GetParametersResponse(parameters=res)

    def SetParameters(self, request, context):
        node_params = self.params.setdefault(request.node_name, {})
        for p in request.parameters:
            node_params[p.name] = p.value
        return admin_pb2.SetParametersResponse(success=True, message="Updated successfully")

    def LookupTF(self, request, context):
        transform = admin_pb2.TFTransform(
            frame_id=request.target_frame,
            child_frame_id=request.source_frame,
            translation=common_pb2.Vector3(x=1.2, y=0.5, z=0.0),
            rotation=common_pb2.Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
        )
        return admin_pb2.LookupTFResponse(
            success=True, transform=transform, message="TF lookup succeeded"
        )


class MockTopicServicer(topic_pb2_grpc.TopicServiceServicer):
    def __init__(self):
        self.published_messages: List[topic_pb2.PublishRequest] = []
        self.message_stream_queue: Dict[str, List[topic_pb2.TopicMessage]] = {}
        self.seq = 1

    def Publish(self, request, context):
        self.published_messages.append(request)
        curr_seq = self.seq
        self.seq += 1
        return topic_pb2.PublishResponse(sequence=curr_seq)

    def Subscribe(self, request, context):
        msgs = self.message_stream_queue.get(request.topic, [])
        for m in msgs:
            yield m


class MockServiceServicer(service_pb2_grpc.ServiceServiceServicer):
    def CallService(self, request, context):
        if request.service == "/add_two_ints":
            import struct

            # Request payload starts after 4-byte header
            a, b = struct.unpack("<qq", request.payload[4:20])
            res_payload = b"\x00\x01\x00\x00" + struct.pack("<q", a + b)
            return service_pb2.ServiceResponse(
                service=request.service,
                type=request.type,
                payload=res_payload,
                success=True,
            )
        elif request.service == "/set_power":
            import struct

            val = struct.unpack("<?", request.payload[4:5])[0]
            # response: bool success, string message
            w_buf = bytearray(b"\x00\x01\x00\x00")
            w_buf.append(1 if val else 0)
            msg = b"OK\x00"
            w_buf.extend(struct.pack("<I", len(msg)))
            w_buf.extend(msg)
            return service_pb2.ServiceResponse(
                service=request.service,
                type=request.type,
                payload=bytes(w_buf),
                success=True,
            )
        return service_pb2.ServiceResponse(
            service=request.service,
            type=request.type,
            success=False,
            error_message="Unknown test service",
        )


class MockActionServicer(action_pb2_grpc.ActionServiceServicer):
    def __init__(self):
        self.goals = {}

    def SendGoal(self, request, context):
        self.goals[request.goal_id] = request
        return action_pb2.SendGoalResponse(
            goal_id=request.goal_id,
            accepted=True,
            message="Goal accepted by mock action server",
        )

    def CancelGoal(self, request, context):
        return action_pb2.CancelGoalResponse(
            goal_id=request.goal_id,
            canceled=True,
            message="Goal canceled successfully",
        )

    def GetResult(self, request, context):
        return action_pb2.GetResultResponse(
            goal_id=request.goal_id,
            status=action_pb2.ActionGoalStatus.STATUS_SUCCEEDED,
            result_payload=b"success: true",
            message="Action completed",
        )

    def StreamFeedback(self, request, context):
        for i in range(1, 4):
            yield action_pb2.FeedbackStreamResponse(
                goal_id=request.goal_id,
                status=action_pb2.ActionGoalStatus.STATUS_EXECUTING,
                feedback_payload=f"progress: {i * 33}%".encode(),
            )


class MockWrosbridgeServer:
    """Manages an in-process mock gRPC server for testing."""

    def __init__(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        self.health_servicer = MockHealthServicer()
        self.admin_servicer = MockAdminServicer()
        self.topic_servicer = MockTopicServicer()
        self.service_servicer = MockServiceServicer()
        self.action_servicer = MockActionServicer()

        health_pb2_grpc.add_HealthServicer_to_server(self.health_servicer, self.server)
        admin_pb2_grpc.add_AdminServiceServicer_to_server(self.admin_servicer, self.server)
        topic_pb2_grpc.add_TopicServiceServicer_to_server(self.topic_servicer, self.server)
        service_pb2_grpc.add_ServiceServiceServicer_to_server(self.service_servicer, self.server)
        action_pb2_grpc.add_ActionServiceServicer_to_server(self.action_servicer, self.server)

        self.port = self.server.add_insecure_port("127.0.0.1:0")

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop(grace=0)

    @property
    def target(self) -> str:
        return f"127.0.0.1:{self.port}"
