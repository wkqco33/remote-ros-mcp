"""Standard ROS2 message and service codecs."""

import json
from typing import Any, Dict

from remote_ros_mcp.codecs.base import CDRReader, CDRWriter, MessageCodec


class StringCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", "") if isinstance(data, dict) else str(data)
        w = CDRWriter()
        w.write_string(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_string()}


class BoolCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", False) if isinstance(data, dict) else bool(data)
        w = CDRWriter()
        w.write_bool(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_bool()}


class Int32Codec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", 0) if isinstance(data, dict) else int(data)
        w = CDRWriter()
        w.write_int32(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_int32()}


class Int64Codec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", 0) if isinstance(data, dict) else int(data)
        w = CDRWriter()
        w.write_int64(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_int64()}


class Float32Codec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", 0.0) if isinstance(data, dict) else float(data)
        w = CDRWriter()
        w.write_float32(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_float32()}


class Float64Codec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        val = data.get("data", 0.0) if isinstance(data, dict) else float(data)
        w = CDRWriter()
        w.write_float64(val)
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {"data": r.read_float64()}


class Vector3Codec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_float64(d.get("x", 0.0))
        w.write_float64(d.get("y", 0.0))
        w.write_float64(d.get("z", 0.0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "x": r.read_float64(),
            "y": r.read_float64(),
            "z": r.read_float64(),
        }


class PointCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_float64(d.get("x", 0.0))
        w.write_float64(d.get("y", 0.0))
        w.write_float64(d.get("z", 0.0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "x": r.read_float64(),
            "y": r.read_float64(),
            "z": r.read_float64(),
        }


class QuaternionCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_float64(d.get("x", 0.0))
        w.write_float64(d.get("y", 0.0))
        w.write_float64(d.get("z", 0.0))
        w.write_float64(d.get("w", 1.0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "x": r.read_float64(),
            "y": r.read_float64(),
            "z": r.read_float64(),
            "w": r.read_float64(),
        }


class TwistCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        linear = d.get("linear", {})
        angular = d.get("angular", {})
        w = CDRWriter()
        # linear: Vector3 (x, y, z)
        w.write_float64(linear.get("x", 0.0))
        w.write_float64(linear.get("y", 0.0))
        w.write_float64(linear.get("z", 0.0))
        # angular: Vector3 (x, y, z)
        w.write_float64(angular.get("x", 0.0))
        w.write_float64(angular.get("y", 0.0))
        w.write_float64(angular.get("z", 0.0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "linear": {
                "x": r.read_float64(),
                "y": r.read_float64(),
                "z": r.read_float64(),
            },
            "angular": {
                "x": r.read_float64(),
                "y": r.read_float64(),
                "z": r.read_float64(),
            },
        }


class PoseCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        pos = d.get("position", {})
        ori = d.get("orientation", {})
        w = CDRWriter()
        # position (x, y, z)
        w.write_float64(pos.get("x", 0.0))
        w.write_float64(pos.get("y", 0.0))
        w.write_float64(pos.get("z", 0.0))
        # orientation (x, y, z, w)
        w.write_float64(ori.get("x", 0.0))
        w.write_float64(ori.get("y", 0.0))
        w.write_float64(ori.get("z", 0.0))
        w.write_float64(ori.get("w", 1.0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "position": {
                "x": r.read_float64(),
                "y": r.read_float64(),
                "z": r.read_float64(),
            },
            "orientation": {
                "x": r.read_float64(),
                "y": r.read_float64(),
                "z": r.read_float64(),
                "w": r.read_float64(),
            },
        }


class AddTwoIntsReqCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_int64(d.get("a", 0))
        w.write_int64(d.get("b", 0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "a": r.read_int64(),
            "b": r.read_int64(),
        }


class AddTwoIntsResCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_int64(d.get("sum", 0))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "sum": r.read_int64(),
        }


class SetBoolReqCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_bool(d.get("data", False))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "data": r.read_bool(),
        }


class SetBoolResCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_bool(d.get("success", False))
        w.write_string(d.get("message", ""))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "success": r.read_bool(),
            "message": r.read_string(),
        }


class TriggerReqCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        w = CDRWriter()
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        return {}


class TriggerResCodec(MessageCodec):
    def encode(self, data: Any) -> bytes:
        d = data if isinstance(data, dict) else {}
        w = CDRWriter()
        w.write_bool(d.get("success", False))
        w.write_string(d.get("message", ""))
        return w.to_bytes()

    def decode(self, payload: bytes) -> Dict[str, Any]:
        r = CDRReader(payload)
        return {
            "success": r.read_bool(),
            "message": r.read_string(),
        }


class FallbackCodec(MessageCodec):
    """Fallback codec for unmapped types: supports raw bytes or JSON/hex string."""

    def encode(self, data: Any) -> bytes:
        if isinstance(data, bytes):
            is_cdr = data.startswith(b"\x00\x01\x00\x00") or data.startswith(b"\x00\x00\x00\x00")
            if not is_cdr:
                return b"\x00\x01\x00\x00" + data
            return data
        if isinstance(data, str):
            try:
                # Try hex decode
                raw = bytes.fromhex(data)
                return self.encode(raw)
            except ValueError:
                encoded = data.encode("utf-8")
                return b"\x00\x01\x00\x00" + encoded
        if isinstance(data, dict):
            # Fallback encode as UTF-8 JSON payload
            encoded = json.dumps(data).encode("utf-8")
            return b"\x00\x01\x00\x00" + encoded
        return b"\x00\x01\x00\x00"

    def decode(self, payload: bytes) -> Dict[str, Any]:
        raw = payload[4:] if len(payload) >= 4 else payload
        # Try decoding as utf-8 json
        try:
            val = json.loads(raw.decode("utf-8"))
            if isinstance(val, dict):
                return val
            return {"data": val}
        except Exception:
            pass

        # Return hex representation
        return {
            "raw_hex": payload.hex(),
            "raw_length": len(payload),
        }
