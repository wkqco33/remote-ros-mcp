"""CLI interface for remote-ros-mcp."""

import json
import sys

import click
from rich.console import Console

from remote_ros_mcp.client import WrosbridgeClient
from remote_ros_mcp.config import BridgeConfig
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
    cfg = BridgeConfig.from_env()
    if host:
        cfg.host = host
    if port:
        cfg.port = port
    if api_key:
        cfg.api_key = api_key
    if tls is not None:
        cfg.use_tls = tls
    if timeout:
        cfg.timeout_sec = timeout
    ctx.obj["config"] = cfg


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
