"""CLI interface for remote-ros-mcp."""

import json
import sys
from dataclasses import asdict

import click
from rich.console import Console

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.config import (
    BridgeConfig,
    get_config_path,
    load_config_file,
    save_config_file,
)
from remote_ros_mcp.server.app import create_mcp_server

console = Console(stderr=True)


@click.group()
@click.option("--host", default=None, help="wrosbridge host (env: ROS_BRIDGE_HOST)")
@click.option("--port", default=None, type=int, help="wrosbridge port (env: ROS_BRIDGE_PORT)")
@click.option("--api-key", default=None, help="API key (env: ROS_BRIDGE_API_KEY)")
@click.option("--tls/--no-tls", default=None, help="Enable TLS connection")
@click.option("--timeout", default=None, type=float, help="Timeout in seconds")
@click.pass_context
def cli(ctx, host, port, api_key, tls, timeout):
    """remote-ros-mcp: MCP server and verification tools for ROS2 robotics development."""
    ctx.ensure_object(dict)
    cli_overrides = {}
    if host is not None:
        cli_overrides["host"] = host
    if port is not None:
        cli_overrides["port"] = port
    if api_key is not None:
        cli_overrides["api_key"] = api_key
    if tls is not None:
        cli_overrides["use_tls"] = tls
    if timeout is not None:
        cli_overrides["timeout_sec"] = timeout

    cfg = BridgeConfig.load(cli_overrides=cli_overrides)
    ctx.obj["config"] = cfg
    ctx.obj["cli_overrides"] = cli_overrides


# -------------------------------------------------------------
# Config Subcommands (init, path, show, set)
# -------------------------------------------------------------


@cli.group(name="config")
def config_group():
    """Manage configuration file for remote-ros-mcp."""
    pass


@config_group.command(name="path")
def config_path():
    """Display the platform-specific path of the configuration file."""
    p = get_config_path()
    click.echo(str(p))


@config_group.command(name="init")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration file")
def config_init(force):
    """Initialize a default configuration file."""
    p = get_config_path()
    if p.exists() and not force:
        console.print(f"[bold yellow]Config file already exists at {p}[/bold yellow]")
        console.print("Use --force to overwrite with defaults.")
        return

    defaults = BridgeConfig.default_dict()
    save_config_file(defaults, p)
    console.print(f"[bold green]✓ Created configuration file at {p}[/bold green]")


@config_group.command(name="show")
@click.option("--json", "as_json", is_flag=True, help="Output configuration as JSON")
@click.option("--file-only", is_flag=True, help="Show only values stored in config file")
@click.pass_context
def config_show(ctx, as_json, file_only):
    """Show current configuration values."""
    if file_only:
        data = load_config_file()
    else:
        cfg: BridgeConfig = ctx.obj["config"]
        data = asdict(cfg)

    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        p = get_config_path()
        console.print(f"[bold cyan]remote-ros-mcp Configuration[/bold cyan] (source: {p})")
        for k, v in data.items():
            console.print(f"  {k}: [bold]{v}[/bold]")


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value in the configuration file.

    Example: remote-ros-mcp config set host 192.168.1.100
    """
    defaults = BridgeConfig.default_dict()
    if key not in defaults:
        console.print(f"[bold red]Error: Unknown configuration key '{key}'[/bold red]")
        console.print(f"Allowed keys: {', '.join(defaults.keys())}")
        sys.exit(2)

    data = load_config_file()
    if not data:
        data = defaults

    # Type casting based on default types
    default_val = defaults[key]
    if isinstance(default_val, bool):
        parsed_val = value.lower() in ("true", "1", "yes", "y", "t")
    elif isinstance(default_val, int):
        try:
            parsed_val = int(value)
        except ValueError:
            console.print(f"[bold red]Error: '{value}' is not a valid integer[/bold red]")
            sys.exit(2)
    elif isinstance(default_val, float):
        try:
            parsed_val = float(value)
        except ValueError:
            console.print(f"[bold red]Error: '{value}' is not a valid float[/bold red]")
            sys.exit(2)
    elif value.lower() in ("null", "none"):
        parsed_val = None
    else:
        parsed_val = value

    data[key] = parsed_val
    save_config_file(data)
    p = get_config_path()
    console.print(f"[bold green]✓ Set '{key}' = {parsed_val}[/bold green] in {p}")


# -------------------------------------------------------------
# Runtime & Diagnostic Commands
# -------------------------------------------------------------


@cli.command(name="run")
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio"]),
    help="MCP transport protocol",
)
@click.pass_context
def run_server(ctx, transport):
    """Run MCP server for LLM agent pairs via stdio."""
    cfg: BridgeConfig = ctx.obj["config"]
    console.print(
        f"[bold green]Starting remote-ros-mcp server[/bold green] connected to {cfg.target}..."
    )
    mcp = create_mcp_server(config=cfg)
    mcp.run(transport=transport)


@cli.command(name="test-connection")
@click.option("--json", "as_json", is_flag=True, help="Output machine-readable JSON")
@click.pass_context
def test_connection(ctx, as_json):
    """Test connection and health of remote wrosbridge gateway."""
    cfg: BridgeConfig = ctx.obj["config"]
    client = WrosbridgeClient.from_config(cfg)
    try:
        res = client.check_health()
        if as_json:
            click.echo(json.dumps(res, indent=2))
        else:
            if res.get("serving"):
                console.print(f"[bold green]✓ Connected to wrosbridge at {cfg.target}[/bold green]")
                console.print(f"Status: {res.get('status')}")
            else:
                status = res.get("status")
                console.print(
                    f"[bold yellow]! Connected to {cfg.target} but status: {status}[/bold yellow]"
                )
        sys.exit(0)
    except Exception as e:
        if as_json:
            click.echo(json.dumps({"serving": False, "error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]✗ Failed to connect to {cfg.target}: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="inspect")
@click.option("--json", "as_json", is_flag=True, help="Output machine-readable JSON")
@click.pass_context
def inspect_graph(ctx, as_json):
    """Inspect active ROS2 nodes, topics, and services."""
    cfg: BridgeConfig = ctx.obj["config"]
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
            click.echo(json.dumps(data, indent=2))
        else:
            console.print(f"[bold cyan]ROS2 Graph Summary ({cfg.target})[/bold cyan]")
            console.print(f"Nodes ({len(nodes)}): {', '.join(n['name'] for n in nodes)}")
            console.print(f"Topics ({len(topics)}): {', '.join(t['topic'] for t in topics)}")
            console.print(f"Services ({len(services)}): {', '.join(services)}")
        sys.exit(0)
    except Exception as e:
        if as_json:
            click.echo(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]Failed to inspect graph: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
