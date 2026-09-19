# AGENTS.md

Welcome! This document provides technical guidelines and developer protocols for AI agents and human contributors working on `remote-ros-mcp`.

---

## 1. Project Mission & Architecture

`remote-ros-mcp` is a production-grade **Model Context Protocol (MCP)** server designed to empower LLM coding agents working on ROS2 robotics systems. It bridges between LLM development environments and a remote robot running `wrosbridge` (C++17/ROS2 Jazzy gRPC Gateway).

### Key Architectural Tenets
1. **Separation of Concerns**:
   - `grpc_client`: Clean gRPC transport layer communicating with `wrosbridge.v1` Protobuf services.
   - `codecs`: Robust bidirectional CDR (Common Data Representation) <-> Python Dict/JSON serialization.
   - `mcp_server`: FastMCP tools and resource endpoints consumed by AI agents.
   - `testing`: Dedicated assertion, mocking, frequency measurement, and inspection toolsets.
   - `cli`: Standalone CLI for diagnostics and verification without an MCP host.
2. **Zero-Local-ROS2 Dependency**:
   - The MCP host environment does NOT require ROS2 (rclpy/rclcpp) installed locally. All communication is pure gRPC over TCP with optional TLS and API Key authentication.
3. **LLM-Friendly Interfaces**:
   - No raw bytes exposed to LLM prompts unless requested. All payloads are parsed into standard JSON objects.
   - Timeouts, cancellations, and long-running streaming operations are wrapped in safe request-response or sampling semantics.

---

## 2. Directory Layout

```text
remote-ros-mcp/
├── AGENTS.md                  # Developer & Agent guidelines
├── pyproject.toml             # uv & project dependencies
├── README.md / README_KO.md   # Documentation
├── CHANGELOG.md               # Semantic versioning change log
├── proto/                     # wrosbridge Protobuf definitions
│   └── wrosbridge/v1/
├── scripts/
│   └── generate_protos.py     # Script to generate Python gRPC stubs
├── src/
│   └── remote_ros_mcp/
│       ├── __init__.py
│       ├── cli.py             # CLI entrypoint
│       ├── config.py          # Environment & connection settings
│       ├── proto/             # Compiled protobuf stubs (wrosbridge_pb2)
│       ├── codecs/            # ROS2 CDR <-> JSON encoders/decoders
│       │   ├── base.py
│       │   ├── standard.py    # std_msgs, geometry_msgs, sensor_msgs, etc.
│       │   └── registry.py
│       ├── client/            # wrosbridge gRPC client wrappers
│       │   ├── client.py
│       │   ├── health.py
│       │   ├── admin.py
│       │   ├── topic.py
│       │   ├── service.py
│       │   └── action.py
│       ├── server/            # FastMCP server definition & tools
│       │   ├── app.py
│       │   ├── tools_graph.py
│       │   ├── tools_data.py
│       │   ├── tools_action.py
│       │   └── tools_test.py  # Verification & test tools
│       └── utils/
│           ├── errors.py
│           └── ring_buffer.py
└── tests/
    ├── conftest.py
    ├── mock_server.py         # Mock wrosbridge gRPC server for testing
    ├── test_codecs.py
    ├── test_client.py
    ├── test_tools.py
    ├── test_verification.py
    └── test_cli.py
```

---

## 3. TDD & Testing Protocols

1. **Test-First Discipline**:
   - Every tool, codec, and client method must have comprehensive unit tests.
   - Use `tests/mock_server.py` to simulate all `wrosbridge.v1` gRPC endpoints (`Health`, `AdminService`, `TopicService`, `ServiceService`, `ActionService`).
   - Run tests via `uv run pytest` before committing or finalizing any feature.
2. **Deterministic & Fast**:
   - Do NOT depend on a live robot or network connectivity for unit tests. All tests must pass in an isolated CI/offline environment.
3. **Coverage & Edge Cases**:
   - Test invalid payloads, unsupported message types, timeout expirations, connection cancellations, and malformed inputs.

---

## 4. Code Quality & Standards

1. **Linting & Formatting**:
   - Code must format cleanly with `ruff check .` and `ruff format .`.
   - Maintain static typing consistency with `mypy src`.
2. **Comment & Documentation Hygiene**:
   - Comments must be concise and explain *why*, not *what*.
   - Never leave agent monologues, debugging breadcrumbs, or unmaintained comments in the codebase.
   - Keep docstrings compliant with Google Python style.
3. **CLI Design Guidelines (`clig.dev`)**:
   - Output clean machine-readable data to `stdout` (support `--json`).
   - Route diagnostic logs and progress indicators strictly to `stderr`.
   - Use non-zero exit codes for failures: `0` (Success), `1` (General error), `2` (Invalid argument / configuration).
   - Ensure non-interactive safe execution (`--no-input`).

---

## 5. Security & Error Handling

1. **Never Log Sensitive Credentials**:
   - Do not print API keys or token strings in logs or stdout.
2. **Standardized Error Responses**:
   - Follow standard gRPC status mapping and clear error messages with actionable hints for LLM agents.
   - Catch network errors and wrap them in friendly `BridgeConnectionError`, `CodecError`, or `ServiceUnavailableError`.
