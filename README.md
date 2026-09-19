# remote-ros-mcp

[한국어 안내 (README_KO.md)](README_KO.md) | [Developer Guidelines (AGENTS.md)](AGENTS.md) | [Changelog](CHANGELOG.md)

`remote-ros-mcp` is a production-grade **Model Context Protocol (MCP)** server that empowers LLM coding agents (Claude Desktop, Cursor, Antigravity, etc.) to interact with, control, and verify remote ROS2 robotics applications.

Built to pair with the high-performance C++17/ROS2 Jazzy API Gateway [`wrosbridge`](../wrosbridge), it allows LLM agents to inspect topics, services, actions, parameters, TF transforms, and execute real-time automated verification suites without requiring any local ROS2 installation.

---

## 🌟 Highlights

- **Zero Local ROS2 Dependency**: Operates entirely over standard TCP/gRPC. No `rclpy` or ROS2 environment is required on the host or agent machine.
- **Bi-directional CDR <-> JSON Codec Engine**: Translates Little-Endian ROS2 CDR byte streams into clean, validated Python dictionaries/JSON for LLMs.
- **Testing & Verification Suite**:
  - `ros2_assert_topic_published`: Assert message arrival matching Python expressions (e.g. `msg['linear']['x'] > 0.5`).
  - `ros2_measure_topic_hz`: Real-time topic frequency, period, and jitter analysis.
  - `ros2_mock_publish_sequence`: Sequence injector to stimulate and test subscriber nodes.
  - `ros2_record_and_inspect`: Topic data recording and statistical summary.
- **One-stop ROS2 Action Support**: `ros2_action_send_goal` dispatches goals, monitors progress, and waits for final results.
- **Enterprise Security**: Full TLS encryption and API key header (`x-api-key`) authentication.
- **Standalone CLI**: Diagnoses remote nodes and topics directly via `remote-ros-mcp test-connection` and `remote-ros-mcp inspect` (`--json` supported).

---

## 🛠 Architecture

```text
[LLM Coding Agent (Cursor / Claude / Antigravity)]
                    │
                    │ MCP Protocol (JSON-RPC over stdio)
                    ▼
          ┌─────────────────────┐
          │   remote-ros-mcp    │
          │   (FastMCP Server)  │
          │ ┌─────────────────┐ │
          │ │ CDR <-> JSON    │ │
          │ │ Codec Engine    │ │
          │ └─────────────────┘ │
          └──────────┬──────────┘
                     │
                     │ gRPC + TLS / API-Key
                     ▼
          ┌─────────────────────┐
          │     wrosbridge      │
          │ (ROS2 Jazzy Gateway)│
          └──────────┬──────────┘
                     │
                     │ rclcpp (CDR)
                     ▼
          [ROS2 Robot Node Graph]
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### 2. Installation
```bash
git clone <repo-url> remote-ros-mcp
cd remote-ros-mcp
uv sync
```

### 3. Configuration Management
`remote-ros-mcp` adheres to OS-standard configuration paths (XDG on Linux, Application Support on macOS, AppData on Windows) with layered precedence: **CLI flags > Environment Variables > config.json > Defaults**.

- **Default Config Path**:
  - Linux: `~/.config/remote-ros-mcp/config.json`
  - macOS: `~/Library/Application Support/remote-ros-mcp/config.json`
  - Windows: `%APPDATA%\remote-ros-mcp\config.json`
  - *Override Variable*: `REMOTE_ROS_CONFIG_PATH`

```bash
# Print config path
uv run remote-ros-mcp config path

# Initialize default configuration
uv run remote-ros-mcp config init

# Set configuration parameters
uv run remote-ros-mcp config set host 192.168.1.100
uv run remote-ros-mcp config set port 50051

# View active configuration
uv run remote-ros-mcp config show --json
```

### 4. CLI Diagnostics
```bash
# Test connection health
uv run remote-ros-mcp test-connection

# Machine-readable JSON output
uv run remote-ros-mcp test-connection --json

# Discover active ROS2 graph
uv run remote-ros-mcp inspect --json
```

---

## 🤖 LLM Agent Integration

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "remote-ros": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remote-ros-mcp",
        "run",
        "remote-ros-mcp",
        "run"
      ],
      "env": {
        "ROS_BRIDGE_HOST": "127.0.0.1",
        "ROS_BRIDGE_PORT": "50051"
      }
    }
  }
}
```

---

## 📋 MCP Tools Reference

| Category | Tool | Description |
|---|---|---|
| **Graph & Introspection** | `ros2_health_check` | Verify wrosbridge connection and serving health |
| | `ros2_get_nodes` | List active nodes, namespaces, pub/sub topics, and services |
| | `ros2_get_topics` | List available topics with publisher/subscriber mapping |
| | `ros2_get_services` | List active services |
| | `ros2_get_parameters` | Read parameter values from a target node |
| | `ros2_set_parameters` | Update parameter values on a target node |
| | `ros2_lookup_tf` | Lookup geometric coordinate transform between two frames |
| **Data Exchange** | `ros2_topic_publish` | Publish JSON payload to a ROS2 topic |
| | `ros2_topic_echo` | Sample recent N messages or listen to live stream |
| | `ros2_call_service` | Call ROS2 service synchronously and receive JSON reply |
| | `ros2_action_send_goal` | Send action goal, await completion, and summarize feedback |
| | `ros2_action_cancel_goal` | Cancel active action goal |
| **Testing & Verification** | `ros2_assert_topic_published` | Assert message publication matching condition expression |
| | `ros2_measure_topic_hz` | Measure topic publishing rate (Hz), period, and jitter |
| | `ros2_mock_publish_sequence` | Inject simulated message sequence to verify subscriber behavior |
| | `ros2_record_and_inspect` | Record topic data for N seconds and return statistical summary |

---

## 🧪 Testing & Quality

Strict compliance with the `ncli view 24` engineering checklist:

```bash
# Run 24 unit & integration tests against in-memory mock server
uv run pytest -v

# Run with test coverage
uv run pytest --cov=remote_ros_mcp --cov-report=term-missing

# Lint & code format checks
uv run ruff check .
uv run ruff format --check .
```

---

## 📄 License
Apache License 2.0. See [LICENSE](LICENSE) for details.
