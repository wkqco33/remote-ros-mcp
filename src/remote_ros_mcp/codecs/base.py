"""Base classes and low-level CDR (Common Data Representation) helpers."""

import struct
from abc import ABC, abstractmethod
from typing import Any, Dict


class CodecError(Exception):
    """Raised when encoding or decoding a ROS2 message fails."""

    pass


class CDRWriter:
    """Helper to serialize values into Little-Endian CDR buffer."""

    def __init__(self, include_header: bool = True):
        self.buffer = bytearray()
        if include_header:
            # 4-byte standard CDR encapsulation header for Little Endian
            self.buffer.extend(b"\x00\x01\x00\x00")

    def _align(self, alignment: int):
        # Alignment is relative to payload after the 4-byte header
        header_len = 4
        current_payload_len = len(self.buffer) - header_len
        if current_payload_len < 0:
            return
        remainder = current_payload_len % alignment
        if remainder != 0:
            padding = alignment - remainder
            self.buffer.extend(b"\x00" * padding)

    def write_bool(self, val: bool):
        self.buffer.append(1 if val else 0)

    def write_int8(self, val: int):
        self.buffer.extend(struct.pack("<b", int(val)))

    def write_uint8(self, val: int):
        self.buffer.extend(struct.pack("<B", int(val)))

    def write_int16(self, val: int):
        self._align(2)
        self.buffer.extend(struct.pack("<h", int(val)))

    def write_uint16(self, val: int):
        self._align(2)
        self.buffer.extend(struct.pack("<H", int(val)))

    def write_int32(self, val: int):
        self._align(4)
        self.buffer.extend(struct.pack("<i", int(val)))

    def write_uint32(self, val: int):
        self._align(4)
        self.buffer.extend(struct.pack("<I", int(val)))

    def write_int64(self, val: int):
        self._align(8)
        self.buffer.extend(struct.pack("<q", int(val)))

    def write_uint64(self, val: int):
        self._align(8)
        self.buffer.extend(struct.pack("<Q", int(val)))

    def write_float32(self, val: float):
        self._align(4)
        self.buffer.extend(struct.pack("<f", float(val)))

    def write_float64(self, val: float):
        self._align(8)
        self.buffer.extend(struct.pack("<d", float(val)))

    def write_string(self, val: str):
        # CDR string: 4-byte length (including null terminator) + string bytes + null terminator
        encoded = str(val).encode("utf-8")
        str_len = len(encoded) + 1
        self.write_uint32(str_len)
        self.buffer.extend(encoded)
        self.buffer.append(0)

    def to_bytes(self) -> bytes:
        return bytes(self.buffer)


class CDRReader:
    """Helper to deserialize values from Little-Endian CDR buffer."""

    def __init__(self, data: bytes, strip_header: bool = True):
        self.data = data
        self.offset = 0
        if strip_header and len(data) >= 4:
            # Check encapsulation header
            # \x00\x01\x00\x00 (CDR_LE) or \x00\x00\x00\x00 (CDR_BE)
            self.offset = 4

    def _align(self, alignment: int):
        header_len = 4
        current_payload_pos = self.offset - header_len
        if current_payload_pos < 0:
            return
        remainder = current_payload_pos % alignment
        if remainder != 0:
            self.offset += alignment - remainder

    def read_bool(self) -> bool:
        if self.offset >= len(self.data):
            raise CodecError("Unexpected EOF reading bool")
        val = self.data[self.offset] != 0
        self.offset += 1
        return val

    def read_int8(self) -> int:
        if self.offset >= len(self.data):
            raise CodecError("Unexpected EOF reading int8")
        val = struct.unpack_from("<b", self.data, self.offset)[0]
        self.offset += 1
        return val

    def read_uint8(self) -> int:
        if self.offset >= len(self.data):
            raise CodecError("Unexpected EOF reading uint8")
        val = struct.unpack_from("<B", self.data, self.offset)[0]
        self.offset += 1
        return val

    def read_int16(self) -> int:
        self._align(2)
        if self.offset + 2 > len(self.data):
            raise CodecError("Unexpected EOF reading int16")
        val = struct.unpack_from("<h", self.data, self.offset)[0]
        self.offset += 2
        return val

    def read_uint16(self) -> int:
        self._align(2)
        if self.offset + 2 > len(self.data):
            raise CodecError("Unexpected EOF reading uint16")
        val = struct.unpack_from("<H", self.data, self.offset)[0]
        self.offset += 2
        return val

    def read_int32(self) -> int:
        self._align(4)
        if self.offset + 4 > len(self.data):
            raise CodecError("Unexpected EOF reading int32")
        val = struct.unpack_from("<i", self.data, self.offset)[0]
        self.offset += 4
        return val

    def read_uint32(self) -> int:
        self._align(4)
        if self.offset + 4 > len(self.data):
            raise CodecError("Unexpected EOF reading uint32")
        val = struct.unpack_from("<I", self.data, self.offset)[0]
        self.offset += 4
        return val

    def read_int64(self) -> int:
        self._align(8)
        if self.offset + 8 > len(self.data):
            raise CodecError("Unexpected EOF reading int64")
        val = struct.unpack_from("<q", self.data, self.offset)[0]
        self.offset += 8
        return val

    def read_uint64(self) -> int:
        self._align(8)
        if self.offset + 8 > len(self.data):
            raise CodecError("Unexpected EOF reading uint64")
        val = struct.unpack_from("<Q", self.data, self.offset)[0]
        self.offset += 8
        return val

    def read_float32(self) -> float:
        self._align(4)
        if self.offset + 4 > len(self.data):
            raise CodecError("Unexpected EOF reading float32")
        val = struct.unpack_from("<f", self.data, self.offset)[0]
        self.offset += 4
        return val

    def read_float64(self) -> float:
        self._align(8)
        if self.offset + 8 > len(self.data):
            raise CodecError("Unexpected EOF reading float64")
        val = struct.unpack_from("<d", self.data, self.offset)[0]
        self.offset += 8
        return val

    def read_string(self) -> str:
        str_len = self.read_uint32()
        if str_len == 0:
            return ""
        if self.offset + str_len > len(self.data):
            raise CodecError(f"Unexpected EOF reading string of length {str_len}")
        raw = self.data[self.offset : self.offset + str_len]
        self.offset += str_len
        # Drop trailing null terminator if present
        if raw.endswith(b"\x00"):
            raw = raw[:-1]
        return raw.decode("utf-8", errors="replace")


class MessageCodec(ABC):
    """Abstract base for encoding/decoding ROS2 types."""

    @abstractmethod
    def encode(self, data: Any) -> bytes:
        """Encode Python dict or primitive into CDR bytes."""
        pass

    @abstractmethod
    def decode(self, payload: bytes) -> Dict[str, Any]:
        """Decode CDR bytes into Python dict."""
        pass
