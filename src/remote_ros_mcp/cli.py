"""CLI interface for remote-ros-mcp implemented with wpycli, wpyconf, and wpylog."""

import json
import sys
from dataclasses import asdict
from typing import Any, Dict

from wpycli import Command, CommandContext, exact_args

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.config import (
    BridgeConfig,
    get_config_path,
    load_config_file,
    save_config_file,
)
from remote_ros_mcp.server.app import create_mcp_server
from remote_ros_mcp.utils.logger import get_logger, setup_logger

logger = get_logger("remote_ros_mcp.cli")


def _get_cli_overrides(ctx: CommandContext) -> Dict[str, Any]:
    """Extract CLI overrides from flags."""
    overrides: Dict[str, Any] = {}
    host = ctx.flags.get("host")
    if host is not None:
        overrides["host"] = host

    port = ctx.flags.get("port")
    if port is not None:
        overrides["port"] = int(port)

    api_key = ctx.flags.get("api-key")
    if api_key is not None:
        overrides["api_key"] = api_key

    tls = ctx.flags.get("tls")
    if tls:
        overrides["use_tls"] = True

    timeout = ctx.flags.get("timeout")
    if timeout is not None:
        overrides["timeout_sec"] = float(timeout)

    return overrides


# -------------------------------------------------------------
# Command Handlers
# -------------------------------------------------------------


def handle_run(ctx: CommandContext) -> int:
    """Handle 'run' command: launch FastMCP server."""
    overrides = _get_cli_overrides(ctx)
    cfg = BridgeConfig.load(cli_overrides=overrides)
    transport = str(ctx.flags.get("transport") or "stdio")

    logger.info("Starting remote-ros-mcp server connected to %s...", cfg.target)
    ctx.stderr.write(
        ctx.terminal.panel("remote-ros-mcp", f"Starting MCP server connected to {cfg.target}")
        + "\n"
    )
    mcp = create_mcp_server(config=cfg)
    mcp.run(transport=transport)
    return 0


def handle_test_connection(ctx: CommandContext) -> int:
    """Handle 'test-connection' command."""
    as_json = bool(ctx.flags.get("json"))
    overrides = _get_cli_overrides(ctx)
    cfg = BridgeConfig.load(cli_overrides=overrides)
    client = WrosbridgeClient.from_config(cfg)

    try:
        res = client.check_health()
        if as_json:
            ctx.stdout.write(json.dumps(res, indent=2) + "\n")
        else:
            if res.get("serving"):
                ctx.stderr.write(
                    f"✓ Successfully connected to wrosbridge at {cfg.target}\n"
                    f"Status: {res.get('status')}\n"
                )
            else:
                ctx.stderr.write(f"! Connected to {cfg.target} but status: {res.get('status')}\n")
        return 0
    except Exception as e:
        logger.error("Failed to connect to wrosbridge at %s: %s", cfg.target, e)
        if as_json:
            ctx.stdout.write(json.dumps({"serving": False, "error": str(e)}, indent=2) + "\n")
        else:
            ctx.stderr.write(f"✗ Failed to connect to wrosbridge at {cfg.target}: {e}\n")
        return 1


def handle_inspect(ctx: CommandContext) -> int:
    """Handle 'inspect' command: query graph metadata."""
    as_json = bool(ctx.flags.get("json"))
    overrides = _get_cli_overrides(ctx)
    cfg = BridgeConfig.load(cli_overrides=overrides)
    client = WrosbridgeClient.from_config(cfg)

    try:
        nodes = client.get_nodes()
        topics = client.get_topics()
        services = client.get_services()
        data = {
            "target": cfg.target,
            "nodes_count": len(nodes),
            "topics_count": len(topics),
            "services_count": len(services),
            "nodes": nodes,
            "topics": topics,
            "services": services,
        }
        if as_json:
            ctx.stdout.write(json.dumps(data, indent=2) + "\n")
        else:
            ctx.stderr.write(
                f"ROS2 Graph Summary ({cfg.target})\n"
                f"Nodes ({len(nodes)}): {', '.join(n['name'] for n in nodes)}\n"
                f"Topics ({len(topics)}): {', '.join(t['topic'] for t in topics)}\n"
                f"Services ({len(services)}): {', '.join(services)}\n"
            )
        return 0
    except Exception as e:
        logger.error("Failed to inspect graph: %s", e)
        if as_json:
            ctx.stdout.write(json.dumps({"error": str(e)}, indent=2) + "\n")
        else:
            ctx.stderr.write(f"✗ Failed to inspect graph: {e}\n")
        return 1


# -------------------------------------------------------------
# Config Subcommands
# -------------------------------------------------------------


def handle_config_path(ctx: CommandContext) -> int:
    """Print configuration file path."""
    p = get_config_path()
    ctx.stdout.write(str(p) + "\n")
    return 0


def handle_config_init(ctx: CommandContext) -> int:
    """Initialize default configuration file."""
    force = bool(ctx.flags.get("force"))
    p = get_config_path()
    if p.exists() and not force:
        ctx.stderr.write(
            f"Config file already exists at {p}\nUse --force to overwrite with defaults.\n"
        )
        return 0

    defaults = BridgeConfig.default_dict()
    save_config_file(defaults, p)
    ctx.stderr.write(f"✓ Created configuration file at {p}\n")
    return 0


def handle_config_show(ctx: CommandContext) -> int:
    """Show current configuration values."""
    as_json = bool(ctx.flags.get("json"))
    file_only = bool(ctx.flags.get("file-only"))

    if file_only:
        data = load_config_file()
    else:
        overrides = _get_cli_overrides(ctx)
        cfg = BridgeConfig.load(cli_overrides=overrides)
        data = asdict(cfg)

    if as_json:
        ctx.stdout.write(json.dumps(data, indent=2) + "\n")
    else:
        p = get_config_path()
        ctx.stderr.write(f"remote-ros-mcp Configuration (source: {p})\n")
        for k, v in data.items():
            ctx.stderr.write(f"  {k}: {v}\n")
    return 0


def handle_config_set(ctx: CommandContext) -> int:
    """Set a configuration value."""
    key = ctx.args[0]
    value = ctx.args[1]
    defaults = BridgeConfig.default_dict()

    if key not in defaults:
        allowed = ", ".join(defaults.keys())
        ctx.stderr.write(f"Error: Unknown configuration key '{key}'\nAllowed keys: {allowed}\n")
        return 2

    data = load_config_file()
    if not data:
        data = defaults

    default_val = defaults[key]
    parsed_val: Any
    if isinstance(default_val, bool):
        parsed_val = value.lower() in ("true", "1", "yes", "y", "t")
    elif isinstance(default_val, int):
        try:
            parsed_val = int(value)
        except ValueError:
            ctx.stderr.write(f"Error: '{value}' is not a valid integer\n")
            return 2
    elif isinstance(default_val, float):
        try:
            parsed_val = float(value)
        except ValueError:
            ctx.stderr.write(f"Error: '{value}' is not a valid float\n")
            return 2
    elif value.lower() in ("null", "none"):
        parsed_val = None
    else:
        parsed_val = value

    data[key] = parsed_val
    save_config_file(data)
    p = get_config_path()
    ctx.stderr.write(f"✓ Set '{key}' = {parsed_val} in {p}\n")
    return 0


# -------------------------------------------------------------
# CLI Builder
# -------------------------------------------------------------


def build_cli() -> Command:
    """Build root Command tree using wpycli."""
    root = Command(
        use="rrmcp",
        short="remote-ros-mcp: Model Context Protocol server for ROS2 robotics development.",
        aliases=["remote-ros-mcp"],
    )

    # Persistent connection flags
    root.add_persistent_string_flag("host", help="wrosbridge gateway host (env: ROS_BRIDGE_HOST)")
    root.add_persistent_int_flag("port", help="wrosbridge gateway port (env: ROS_BRIDGE_PORT)")
    root.add_persistent_string_flag("api-key", help="API key (env: ROS_BRIDGE_API_KEY)")
    root.add_persistent_bool_flag("tls", help="Enable TLS connection")
    root.add_persistent_float_flag("timeout", help="Timeout in seconds")
    root.add_persistent_string_flag(
        "log-level",
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    # Subcommand: run
    run_cmd = Command(
        use="run",
        short="Run MCP server for LLM agent pairs via stdio.",
        run=handle_run,
    )
    run_cmd.add_string_flag(
        "transport",
        default="stdio",
        choices=["stdio"],
        help="MCP transport protocol",
    )
    root.add_command(run_cmd)

    # Subcommand: test-connection
    test_cmd = Command(
        use="test-connection",
        short="Test connection and health of remote wrosbridge gateway.",
        run=handle_test_connection,
    )
    test_cmd.add_bool_flag("json", default=False, help="Output machine-readable JSON")
    root.add_command(test_cmd)

    # Subcommand: inspect
    inspect_cmd = Command(
        use="inspect",
        short="Inspect active ROS2 nodes, topics, and services.",
        run=handle_inspect,
    )
    inspect_cmd.add_bool_flag("json", default=False, help="Output machine-readable JSON")
    root.add_command(inspect_cmd)

    # Subcommand group: config
    config_cmd = Command(
        use="config",
        short="Manage configuration file for remote-ros-mcp.",
    )

    config_path_cmd = Command(
        use="path",
        short="Display the platform-specific path of the configuration file.",
        run=handle_config_path,
    )
    config_cmd.add_command(config_path_cmd)

    config_init_cmd = Command(
        use="init",
        short="Initialize default configuration file.",
        run=handle_config_init,
    )
    config_init_cmd.add_bool_flag(
        "force", shorthand="f", default=False, help="Overwrite existing config"
    )
    config_cmd.add_command(config_init_cmd)

    config_show_cmd = Command(
        use="show",
        short="Show current configuration values.",
        run=handle_config_show,
    )
    config_show_cmd.add_bool_flag("json", default=False, help="Output configuration as JSON")
    config_show_cmd.add_bool_flag(
        "file-only", default=False, help="Show only values stored in config file"
    )
    config_cmd.add_command(config_show_cmd)

    config_set_cmd = Command(
        use="set <key> <value>",
        short="Set a configuration value in the configuration file.",
        args_validator=exact_args(2),
        run=handle_config_set,
    )
    config_cmd.add_command(config_set_cmd)

    root.add_command(config_cmd)
    return root


def cli():
    """Main CLI entrypoint."""
    setup_logger()
    cmd = build_cli()
    sys.exit(cmd.execute(sys.argv[1:]))


if __name__ == "__main__":
    cli()
