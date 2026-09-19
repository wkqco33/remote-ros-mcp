"""gRPC Client implementation for wrosbridge."""

import uuid
from typing import Any, Dict, Iterator, List, Optional

import grpc

from remote_ros_mcp.codecs.registry import CodecRegistry
from remote_ros_mcp.config import BridgeConfig
from remote_ros_mcp.proto.wrosbridge.v1 import (
    action_pb2,
    action_pb2_grpc,
    admin_pb2,
    admin_pb2_grpc,
    health_pb2,
    health_pb2_grpc,
    service_pb2,
    service_pb2_grpc,
    topic_pb2,
    topic_pb2_grpc,
)
from remote_ros_mcp.utils.errors import (
    BridgeConnectionError,
    BridgeError,
    ServiceCallError,
)


class AuthInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = list(client_call_details.metadata or [])
        metadata.append(("x-api-key", self._api_key))
        details = client_call_details._replace(metadata=metadata)
        return continuation(details, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        metadata = list(client_call_details.metadata or [])
        metadata.append(("x-api-key", self._api_key))
        details = client_call_details._replace(metadata=metadata)
        return continuation(details, request)


class WrosbridgeClient:
    """Client for connecting to wrosbridge gateway."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 50051,
        api_key: Optional[str] = None,
        use_tls: bool = False,
        tls_cert_path: Optional[str] = None,
        timeout_sec: float = 5.0,
    ):
        self.config = BridgeConfig(
            host=host,
            port=port,
            api_key=api_key,
            use_tls=use_tls,
            tls_cert_path=tls_cert_path,
            timeout_sec=timeout_sec,
        )
        self._channel = self._create_channel()
        self._health_stub = health_pb2_grpc.HealthStub(self._channel)
        self._admin_stub = admin_pb2_grpc.AdminServiceStub(self._channel)
        self._topic_stub = topic_pb2_grpc.TopicServiceStub(self._channel)
        self._service_stub = service_pb2_grpc.ServiceServiceStub(self._channel)
        self._action_stub = action_pb2_grpc.ActionServiceStub(self._channel)

    @classmethod
    def from_config(cls, config: BridgeConfig) -> "WrosbridgeClient":
        return cls(
            host=config.host,
            port=config.port,
            api_key=config.api_key,
            use_tls=config.use_tls,
            tls_cert_path=config.tls_cert_path,
            timeout_sec=config.timeout_sec,
        )

    def _create_channel(self) -> grpc.Channel:
        target = self.config.target
        if self.config.use_tls:
            creds = None
            if self.config.tls_cert_path:
                with open(self.config.tls_cert_path, "rb") as f:
                    root_certs = f.read()
                creds = grpc.ssl_channel_credentials(root_certificates=root_certs)
            else:
                creds = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(target, creds)
        else:
            channel = grpc.insecure_channel(target)

        if self.config.api_key:
            interceptor = AuthInterceptor(self.config.api_key)
            channel = grpc.intercept_channel(channel, interceptor)

        return channel

    def close(self):
        self._channel.close()

    # --- Health ---

    def check_health(self) -> Dict[str, Any]:
        try:
            req = health_pb2.HealthCheckRequest()
            resp = self._health_stub.Check(req, timeout=self.config.timeout_sec)
            status_name = health_pb2.HealthCheckResponse.ServingStatus.Name(resp.status)
            return {
                "status": status_name,
                "serving": resp.status == health_pb2.HealthCheckResponse.ServingStatus.SERVING,
            }
        except grpc.RpcError as e:
            raise BridgeConnectionError(f"Health check failed: {e.details()}") from e

    # --- Graph & Discovery ---

    def get_nodes(self) -> List[Dict[str, Any]]:
        try:
            req = admin_pb2.GetGraphRequest()
            resp = self._admin_stub.GetGraph(req, timeout=self.config.timeout_sec)
            results = []
            for n in resp.nodes:
                results.append(
                    {
                        "name": n.node_name,
                        "namespace": n.node_namespace,
                        "published_topics": list(n.published_topics),
                        "subscribed_topics": list(n.subscribed_topics),
                        "services": list(n.services),
                    }
                )
            return results
        except grpc.RpcError as e:
            raise BridgeError(f"Failed to get graph: {e.details()}") from e

    def get_topics(self) -> List[Dict[str, Any]]:
        nodes = self.get_nodes()
        topic_map: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            for t in n["published_topics"]:
                info = topic_map.setdefault(t, {"topic": t, "publishers": [], "subscribers": []})
                info["publishers"].append(n["name"])
            for t in n["subscribed_topics"]:
                info = topic_map.setdefault(t, {"topic": t, "publishers": [], "subscribers": []})
                info["subscribers"].append(n["name"])
        return list(topic_map.values())

    def get_services(self) -> List[str]:
        nodes = self.get_nodes()
        services = set()
        for n in nodes:
            for s in n["services"]:
                services.add(s)
        return sorted(list(services))

    # --- Parameters ---

    def get_parameters(self, node_name: str, names: List[str]) -> Dict[str, Any]:
        try:
            req = admin_pb2.GetParametersRequest(node_name=node_name, names=names)
            resp = self._admin_stub.GetParameters(req, timeout=self.config.timeout_sec)
            out = {}
            for p in resp.parameters:
                val = p.value
                type_name = admin_pb2.ParameterType.Name(val.type)
                if type_name == "PARAM_BOOL":
                    out[p.name] = val.bool_value
                elif type_name == "PARAM_INT":
                    out[p.name] = val.int_value
                elif type_name == "PARAM_DOUBLE":
                    out[p.name] = val.double_value
                elif type_name == "PARAM_STRING":
                    out[p.name] = val.string_value
                elif type_name == "PARAM_BYTE_ARRAY":
                    out[p.name] = val.bytes_value
                else:
                    out[p.name] = None
            return out
        except grpc.RpcError as e:
            raise BridgeError(f"Failed to get parameters: {e.details()}") from e

    def set_parameters(self, node_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            param_list = []
            for k, v in parameters.items():
                val = admin_pb2.ParameterValue()
                if isinstance(v, bool):
                    val.type = admin_pb2.ParameterType.PARAM_BOOL
                    val.bool_value = v
                elif isinstance(v, int):
                    val.type = admin_pb2.ParameterType.PARAM_INT
                    val.int_value = v
                elif isinstance(v, float):
                    val.type = admin_pb2.ParameterType.PARAM_DOUBLE
                    val.double_value = v
                elif isinstance(v, str):
                    val.type = admin_pb2.ParameterType.PARAM_STRING
                    val.string_value = v
                elif isinstance(v, bytes):
                    val.type = admin_pb2.ParameterType.PARAM_BYTE_ARRAY
                    val.bytes_value = v
                else:
                    val.type = admin_pb2.ParameterType.PARAM_STRING
                    val.string_value = str(v)
                param_list.append(admin_pb2.Parameter(name=k, value=val))

            req = admin_pb2.SetParametersRequest(node_name=node_name, parameters=param_list)
            resp = self._admin_stub.SetParameters(req, timeout=self.config.timeout_sec)
            return {"success": resp.success, "message": resp.message}
        except grpc.RpcError as e:
            raise BridgeError(f"Failed to set parameters: {e.details()}") from e

    # --- TF ---

    def lookup_tf(
        self, target_frame: str, source_frame: str, timeout_sec: Optional[float] = None
    ) -> Dict[str, Any]:
        try:
            req = admin_pb2.LookupTFRequest(target_frame=target_frame, source_frame=source_frame)
            resp = self._admin_stub.LookupTF(req, timeout=timeout_sec or self.config.timeout_sec)
            t = resp.transform
            return {
                "success": resp.success,
                "message": resp.message,
                "target_frame": t.frame_id,
                "source_frame": t.child_frame_id,
                "translation": {
                    "x": t.translation.x,
                    "y": t.translation.y,
                    "z": t.translation.z,
                },
                "rotation": {
                    "x": t.rotation.x,
                    "y": t.rotation.y,
                    "z": t.rotation.z,
                    "w": t.rotation.w,
                },
            }
        except grpc.RpcError as e:
            raise BridgeError(f"TF lookup failed: {e.details()}") from e

    # --- Topic Pub / Sub ---

    def publish_topic(self, topic: str, topic_type: str, data: Any) -> Dict[str, Any]:
        codec = CodecRegistry.get(topic_type)
        payload = codec.encode(data)
        try:
            req = topic_pb2.PublishRequest(topic=topic, type=topic_type, payload=payload)
            resp = self._topic_stub.Publish(req, timeout=self.config.timeout_sec)
            return {"sequence": resp.sequence, "topic": topic, "type": topic_type}
        except grpc.RpcError as e:
            raise BridgeError(f"Failed to publish to {topic}: {e.details()}") from e

    def subscribe_stream(
        self, topic: str, topic_type: str, timeout: Optional[float] = None
    ) -> Iterator[Dict[str, Any]]:
        codec = CodecRegistry.get(topic_type)
        req = topic_pb2.SubscribeRequest(topic=topic, type=topic_type)
        try:
            stream = self._topic_stub.Subscribe(req, timeout=timeout)
            for msg in stream:
                decoded = codec.decode(msg.payload)
                yield {
                    "topic": msg.topic,
                    "type": msg.type,
                    "sequence": msg.sequence,
                    "data": decoded,
                }
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.CANCELLED:
                raise BridgeError(f"Topic subscription stream error: {e.details()}") from e

    # --- Service Call ---

    def call_service(
        self,
        service: str,
        service_type: str,
        request_data: Any,
        timeout_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        req_codec = CodecRegistry.get_service_req(service_type)
        res_codec = CodecRegistry.get_service_res(service_type)
        payload = req_codec.encode(request_data)

        eff_timeout = timeout_sec or self.config.timeout_sec
        req = service_pb2.ServiceRequest(
            service=service,
            type=service_type,
            payload=payload,
        )
        try:
            resp = self._service_stub.CallService(req, timeout=eff_timeout + 2.0)
            if not resp.success:
                return {
                    "success": False,
                    "error": resp.error_message,
                    "service": service,
                }
            decoded = res_codec.decode(resp.payload)
            return {
                "success": True,
                "service": service,
                "type": service_type,
                "data": decoded,
            }
        except grpc.RpcError as e:
            raise ServiceCallError(f"Service call failed for {service}: {e.details()}") from e

    # --- Action ---

    def send_goal(
        self, action_name: str, action_type: str, goal_data: Any, goal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        gid = goal_id or f"goal-{uuid.uuid4().hex[:8]}"
        codec = CodecRegistry.get(action_type)
        payload = codec.encode(goal_data)

        req = action_pb2.SendGoalRequest(
            action_name=action_name,
            action_type=action_type,
            goal_id=gid,
            goal_payload=payload,
        )
        try:
            resp = self._action_stub.SendGoal(req, timeout=self.config.timeout_sec)
            return {
                "goal_id": resp.goal_id,
                "accepted": resp.accepted,
                "message": resp.message,
            }
        except grpc.RpcError as e:
            raise BridgeError(f"SendGoal failed: {e.details()}") from e

    def cancel_goal(self, action_name: str, goal_id: str) -> Dict[str, Any]:
        req = action_pb2.CancelGoalRequest(action_name=action_name, goal_id=goal_id)
        try:
            resp = self._action_stub.CancelGoal(req, timeout=self.config.timeout_sec)
            return {"goal_id": resp.goal_id, "canceled": resp.canceled, "message": resp.message}
        except grpc.RpcError as e:
            raise BridgeError(f"CancelGoal failed: {e.details()}") from e

    def get_action_result(self, action_name: str, goal_id: str) -> Dict[str, Any]:
        req = action_pb2.GetResultRequest(action_name=action_name, goal_id=goal_id)
        try:
            resp = self._action_stub.GetResult(req, timeout=self.config.timeout_sec)
            status_name = action_pb2.ActionGoalStatus.Name(resp.status)
            return {
                "goal_id": resp.goal_id,
                "status": status_name,
                "payload_size": len(resp.result_payload),
                "message": resp.message,
            }
        except grpc.RpcError as e:
            raise BridgeError(f"GetResult failed: {e.details()}") from e
