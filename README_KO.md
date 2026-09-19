# remote-ros-mcp (한국어)

[English README](README.md) | [개발 가이드 (AGENTS.md)](AGENTS.md) | [변경 이력 (CHANGELOG.md)](CHANGELOG.md)

`remote-ros-mcp`는 LLM 코딩 에이전트(Claude Desktop, Cursor, Antigravity 등)가 원격 로봇 환경의 ROS2 생태계와 직접 상호작용하고, 코드를 검증/테스트할 수 있도록 돕는 **프로덕션 레벨 Model Context Protocol (MCP) 서버**입니다.

C++17 및 ROS2 Jazzy 기반의 고성능 gRPC API Gateway인 [`wrosbridge`](../wrosbridge)와 연동하여, 로컬 환경에 ROS2 런타임(rclpy/rclcpp) 설치 없이도 순수 TCP/gRPC를 통해 원격 로봇의 토픽, 서비스, 액션, 파라미터, TF, 그래프를 조회·조작하고 테스트할 수 있습니다.

---

## 🌟 주요 특징 (Key Features)

1. **Zero-Local-ROS2 Dependency (로컬 ROS2 의존성 완전 제거)**:
   - 개발자 머신이나 에이전트 컨테이너에 ROS2를 설치할 필요가 없습니다. 순수 gRPC + Python 환경에서 구동됩니다.
2. **LLM 친화형 양방향 CDR <-> JSON 코덱 엔진**:
   - `wrosbridge`의 Little-Endian CDR 바이너리 페이로드를 LLM 에이전트가 이해할 수 있는 정제된 Python Dict/JSON 객체로 자동 변환합니다.
   - `geometry_msgs` (Twist, Pose, Vector3, Quaternion 등), `std_msgs` (String, Bool, Int, Float 등), `std_srvs`, `example_interfaces` 표준 지원 및 미등록 타입에 대한 안전한 Fallback 제공.
3. **테스트 & 검증 특화 도구군 (Testing & Verification Suite)**:
   - LLM 에이전트가 로봇 제어 코드를 작성한 후 제대로 동작하는지 자체적으로 검증할 수 있는 전용 어설션 및 진단 도구 제공.
   - `ros2_assert_topic_published`: 특정 조건식(예: `msg['linear']['x'] > 0.5`)을 만족하는 메시지가 발행되었는지 검증.
   - `ros2_measure_topic_hz`: 토픽의 발행 빈도(Hz), 평균 주기, 지터(Jitter) 측정.
   - `ros2_mock_publish_sequence`: 피시험 노드의 반응을 유도하기 위한 가상 센서/토픽 데이터 시퀀스 주입.
   - `ros2_record_and_inspect`: 지정 시간 동안 토픽 데이터를 레코딩하고 통계 요약 반환.
4. **원스톱 ROS2 Action 제어**:
   - `ros2_action_send_goal`: 액션 목표 전송 후 완료까지 대기하며 최종 상태(SUCCEEDED, ABORTED 등)와 피드백을 단일 응답으로 요약 반환.
5. **다계층 보안 & 엔터프라이즈 거버넌스**:
   - TLS 상호 암호화 및 API Key(`x-api-key`) 인증 지원.
6. **독립 실행형 CLI 유틸리티**:
   - MCP 모드 외에도 `remote-ros-mcp test-connection`, `remote-ros-mcp inspect` 명령어로 단독 터미널 점검 가능 (`--json` 지원).

---

## 🛠 아키텍처 개요

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

## 🚀 빠른 시작 (Quick Start)

### 1. 사전 요구사항
- Python 3.11 이상
- [`uv`](https://github.com/astral-sh/uv) (권장) 또는 `pip`

### 2. 설정 파일 및 환경 설정
`remote-ros-mcp`는 OS별 표준 디렉토리에 위치하는 `config.json` 설정 파일과 환경 변수, CLI 인자를 계층적으로 지원합니다:
- **플랫폼별 기본 설정 파일 위치**:
  - Linux: `~/.config/remote-ros-mcp/config.json`
  - macOS: `~/Library/Application Support/remote-ros-mcp/config.json`
  - Windows: `%APPDATA%\remote-ros-mcp\config.json`
  - *경로 재정의 환경변수*: `REMOTE_ROS_CONFIG_PATH`

```bash
# 설정 파일 경로 확인 (remote-ros-mcp 또는 단축어 rrmcp 사용 가능)
uv run rrmcp config path

# 기본 설정 파일 초기화
uv run rrmcp config init

# 설정 값 변경 (host, port, api_key, use_tls, timeout_sec 등)
uv run rrmcp config set host 192.168.1.100
uv run rrmcp config set port 50051
uv run rrmcp config set use_tls false

# 현재 활성 설정 조회 (JSON 출력 지원)
uv run rrmcp config show
uv run rrmcp config show --json
```

### 3. 연결 상태 점검 (CLI)
```bash
# 연결 상태 테스트
uv run rrmcp test-connection

# 기계 판독용 JSON 출력
uv run rrmcp test-connection --json

# 원격 ROS2 그래프 (노드, 토픽, 서비스) 탐색
uv run rrmcp inspect --json
```

---

## 🤖 LLM 에이전트 연동 가이드

### 1. Claude Desktop 설정 (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "remote-ros": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/wkqco/Workspace/ros/remote-ros-mcp",
        "run",
        "remote-ros-mcp",
        "run"
      ],
      "env": {
        "ROS_BRIDGE_HOST": "127.0.0.1",
        "ROS_BRIDGE_PORT": "50051",
        "ROS_BRIDGE_API_KEY": "optional-api-key"
      }
    }
  }
}
```

### 2. Cursor / Antigravity 설정
MCP 구성 파일(`mcp.json` 등)에 다음과 같이 추가합니다:
```json
{
  "mcpServers": {
    "remote-ros": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/wkqco/Workspace/ros/remote-ros-mcp",
        "run",
        "remote-ros-mcp",
        "run"
      ]
    }
  }
}
```

---

## 📋 제공되는 MCP 도구 목록 (Tools)

| 분류 | 도구 이름 | 설명 |
|---|---|---|
| **상태 & 그래프** | `ros2_health_check` | wrosbridge 게이트웨이 연결 및 생존 상태 확인 |
| | `ros2_get_nodes` | 활성 ROS2 노드, 네임스페이스, pub/sub 토픽, 서비스 목록 조회 |
| | `ros2_get_topics` | 사용 가능한 토픽 및 발행/구독 노드 매핑 조회 |
| | `ros2_get_services` | 활성 ROS2 서비스 목록 조회 |
| | `ros2_get_parameters` | 특정 노드의 파라미터 값 읽기 |
| | `ros2_set_parameters` | 특정 노드의 파라미터 런타임 수정 |
| | `ros2_lookup_tf` | 기준 좌표계 간의 기하학적 변환(TF) 조회 |
| **데이터 교환** | `ros2_topic_publish` | JSON 데이터를 CDR로 변환하여 토픽 발행 |
| | `ros2_topic_echo` | 토픽 메시지를 N개 수집 또는 타임아웃까지 캡처하여 반환 |
| | `ros2_call_service` | ROS2 서비스 동기식 호출 및 응답 JSON 수신 |
| | `ros2_action_send_goal`| 액션 목표 전송 및 완료 대기(결과 및 피드백 요약 반환) |
| | `ros2_action_cancel_goal`| 실행 중인 액션 목표 취소 |
| **테스트 & 검증** | `ros2_assert_topic_published` | 조건식(`condition_expr`)을 만족하는 토픽 발행 여부 자동 검증 |
| | `ros2_measure_topic_hz` | 토픽 발행 빈도(Hz), 주기, 지터 통계 측정 |
| | `ros2_mock_publish_sequence` | 가상 센서/명령 시퀀스를 주입하여 노드 동작 반응 검증 |
| | `ros2_record_and_inspect` | N초 동안 토픽 데이터를 레코딩하고 미리보기/통계 요약 반환 |

---

## 🧪 테스트 및 코드 품질 (TDD)

이 프로젝트는 `ncli view 24` 엔지니어링 체크리스트 가이드라인을 엄격히 준수합니다.

```bash
# 전체 테스트 실행 (오프라인 Mock 서버 기반, 24개 테스트)
uv run pytest -v

# 테스트 커버리지 리포트
uv run pytest --cov=remote_ros_mcp --cov-report=term-missing

# 코드 린트 및 포맷팅 검사
uv run ruff check .
uv run ruff format --check .
```

---

## 📄 라이선스
Apache License 2.0. 자세한 사항은 [LICENSE](LICENSE)를 참조하세요.
