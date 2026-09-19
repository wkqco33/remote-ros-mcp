# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-20

### Added
- **Command Alias `rrmcp`**: Added `rrmcp` entrypoint alias in `pyproject.toml` for fast invocation (`uv run rrmcp ...`).
- **Comprehensive `.gitignore` Generated via `iggen`**: Standardized multi-platform rules for Linux, macOS, Windows, Python, and VS Code.
- **Configuration File Management (`remote-ros-mcp config`)**:
  - Platform-standard configuration directory resolution (XDG on Linux, Application Support on macOS, AppData on Windows).
  - Subcommands: `init` (create default file), `path` (print location), `show` (display active/file config with `--json`), `set` (modify and type-cast settings).
  - Layered configuration hierarchy: `CLI Flags > Environment Variables > config.json > Defaults`.
- **MCP Server Core**: FastMCP-based standard Model Context Protocol server exposing ROS2 robotics endpoints via stdio transport.
- **wrosbridge gRPC Gateway Integration**:
  - Full client support for `Health`, `AdminService`, `TopicService`, `ServiceService`, and `ActionService`.
  - Secure transport via optional TLS and API Key header (`x-api-key`) authentication.
- **Bidirectional ROS2 CDR Codec Engine**:
  - Low-level `CDRWriter` and `CDRReader` supporting Little-Endian CDR serialization.
  - Native standard codecs for `std_msgs` (String, Bool, Int32/64, Float32/64), `geometry_msgs` (Twist, Vector3, Point, Pose, Quaternion), `std_srvs` (SetBool, Trigger), and `example_interfaces` (AddTwoInts).
  - Robust `FallbackCodec` for arbitrary payloads and schema-less message handling.
- **Graph & Introspection Tools**:
  - `ros2_health_check`: Verify remote gateway status.
  - `ros2_get_nodes`: Discover active ROS2 nodes, namespaces, pub/sub topics, and services.
  - `ros2_get_topics`: Discover topic list and publisher/subscriber mapping.
  - `ros2_get_services`: List available services.
  - `ros2_get_parameters` / `ros2_set_parameters`: Real-time node parameter management.
  - `ros2_lookup_tf`: Geometric coordinate transformation lookup between reference frames.
- **Data Exchange Tools**:
  - `ros2_topic_publish`: Publish JSON payloads directly to ROS2 topics.
  - `ros2_topic_echo`: Sample recent N messages or listen to live topic streams.
  - `ros2_call_service`: Synchronously invoke ROS2 services with timeout protection.
  - `ros2_action_send_goal`: Asynchronous goal dispatch and automated completion waiting for ROS2 Actions.
  - `ros2_action_cancel_goal`: Cancel executing action goals.
- **Testing & Verification Suite**:
  - `ros2_assert_topic_published`: Python condition-based topic publication assertion for automated code validation.
  - `ros2_measure_topic_hz`: Publishing frequency (Hz), average period, and jitter measurements.
  - `ros2_mock_publish_sequence`: Sequence injector to stimulate and verify subscriber node behavior.
  - `ros2_record_and_inspect`: Topic data recorder and preview summarizer.
- **MCP Resources**:
  - `ros2://health`: Gateway connection and serving status.
  - `ros2://graph/nodes`: Live ROS2 graph nodes.
  - `ros2://graph/topics`: Live ROS2 topic list.
- **CLI Utility**:
  - `remote-ros-mcp run`: Launch MCP stdio server.
  - `remote-ros-mcp test-connection`: Standalone health & connection diagnostics (`--json` supported).
  - `remote-ros-mcp inspect`: Standalone node, topic, and service discovery (`--json` supported).
- **Testing Infrastructure**:
  - In-memory `MockWrosbridgeServer` enabling 100% offline, deterministic TDD test suite.
