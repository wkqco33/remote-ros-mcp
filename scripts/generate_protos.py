#!/usr/bin/env python3
"""Generate Python gRPC & Protobuf stubs from proto files."""

import re
import sys
from pathlib import Path

from grpc_tools import protoc

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = PROJECT_ROOT / "proto"
OUT_DIR = PROJECT_ROOT / "src" / "remote_ros_mcp" / "proto"


def main():
    target_dir = OUT_DIR / "wrosbridge" / "v1"
    target_dir.mkdir(parents=True, exist_ok=True)

    proto_files = [
        PROTO_DIR / "wrosbridge" / "v1" / "common.proto",
        PROTO_DIR / "wrosbridge" / "v1" / "health.proto",
        PROTO_DIR / "wrosbridge" / "v1" / "topic.proto",
        PROTO_DIR / "wrosbridge" / "v1" / "service.proto",
        PROTO_DIR / "wrosbridge" / "v1" / "action.proto",
        PROTO_DIR / "wrosbridge" / "v1" / "admin.proto",
    ]

    import grpc_tools

    grpc_proto_dir = Path(grpc_tools.__file__).resolve().parent / "_proto"

    print(f"Compiling protos from {PROTO_DIR} to {OUT_DIR}...")

    args = [
        "protoc",
        f"-I{PROTO_DIR}",
        f"-I{grpc_proto_dir}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
    ] + [str(p) for p in proto_files]

    ret = protoc.main(args)
    if ret != 0:
        print(f"Error: protoc returned {ret}", file=sys.stderr)
        sys.exit(ret)

    # Ensure __init__.py exists
    (OUT_DIR / "__init__.py").touch(exist_ok=True)
    (OUT_DIR / "wrosbridge" / "__init__.py").touch(exist_ok=True)
    (OUT_DIR / "wrosbridge" / "v1" / "__init__.py").touch(exist_ok=True)

    # Fix relative imports in generated grpc files
    # e.g., 'from wrosbridge.v1 import common_pb2' ->
    # 'from remote_ros_mcp.proto.wrosbridge.v1 import common_pb2'
    for pb2_grpc_file in target_dir.glob("*_pb2_grpc.py"):
        content = pb2_grpc_file.read_text()
        content = re.sub(
            r"from wrosbridge\.v1 import (\w+)_pb2 as",
            r"from remote_ros_mcp.proto.wrosbridge.v1 import \1_pb2 as",
            content,
        )
        content = re.sub(
            r"import wrosbridge\.v1\.(\w+)_pb2 as",
            r"from remote_ros_mcp.proto.wrosbridge.v1 import \1_pb2 as",
            content,
        )
        pb2_grpc_file.write_text(content)

    for pb2_file in target_dir.glob("*_pb2.py"):
        content = pb2_file.read_text()
        content = re.sub(
            r"from wrosbridge\.v1 import (\w+)_pb2 as",
            r"from remote_ros_mcp.proto.wrosbridge.v1 import \1_pb2 as",
            content,
        )
        content = re.sub(
            r"import wrosbridge\.v1\.(\w+)_pb2 as",
            r"from remote_ros_mcp.proto.wrosbridge.v1 import \1_pb2 as",
            content,
        )
        pb2_file.write_text(content)

    print("Protobuf compilation completed successfully.")


if __name__ == "__main__":
    main()
