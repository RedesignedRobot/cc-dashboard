"""CLI interface for Claude Stats."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from .parser import ClaudeStats
from .dashboard import (
    render_dashboard,
    create_summary_table,
    create_models_table,
    create_activity_table,
    create_daily_chart,
    create_model_panel,
    create_hour_chart,
)

app = typer.Typer(
    name="claude-stats",
    help="Real-time dashboard for Claude Code usage statistics.",
    no_args_is_help=False,
)
console = Console()


def get_stats(path: Path | None = None) -> ClaudeStats:
    """Load stats, handling errors gracefully."""
    try:
        return ClaudeStats.from_file(path)
    except FileNotFoundError:
        console.print("[red]Error:[/] Stats file not found.")
        console.print("[dim]Make sure Claude Code is installed and you've used it at least once.[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/] Failed to parse stats: {e}")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    watch: Annotated[
        bool,
        typer.Option("--watch", "-w", help="Live dashboard with auto-refresh"),
    ] = False,
    refresh: Annotated[
        float,
        typer.Option("--refresh", "-r", help="Refresh interval in seconds"),
    ] = 1.0,
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """
    Display Claude Code usage statistics.

    Run without arguments for a quick summary.
    Use --watch for a live auto-refreshing dashboard.
    """
    # If a subcommand was invoked, don't run this
    if ctx.invoked_subcommand is not None:
        return

    stats = get_stats(stats_file)

    if watch:
        # Live dashboard mode
        console.print("[dim]Starting live dashboard... Press Ctrl+C to exit[/]")
        time.sleep(0.5)

        try:
            while True:
                stats = get_stats(stats_file)
                render_dashboard(stats, console)
                time.sleep(refresh)
        except KeyboardInterrupt:
            console.clear()
            console.print("[dim]👋 Goodbye![/]")
    else:
        # Quick summary mode
        render_dashboard(stats, console)


@app.command()
def summary(
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Show a compact summary table."""
    stats = get_stats(stats_file)
    console.print(create_summary_table(stats))


@app.command()
def models(
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Show detailed model usage statistics."""
    stats = get_stats(stats_file)
    console.print(create_models_table(stats))


@app.command()
def activity(
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Number of days to show"),
    ] = 14,
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Show daily activity history."""
    stats = get_stats(stats_file)
    console.print(create_activity_table(stats, days))


@app.command()
def hours(
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Show activity distribution by hour."""
    stats = get_stats(stats_file)
    console.print(create_hour_chart(stats))


@app.command()
def today(
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Show today's statistics."""
    stats = get_stats(stats_file)
    today_stats = stats.today_activity

    if not today_stats:
        console.print("[yellow]No activity recorded today yet.[/]")
        return

    from rich.table import Table
    from rich import box

    table = Table(title="Today's Activity", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Messages", f"{today_stats.messages:,}")
    table.add_row("Sessions", str(today_stats.sessions))
    table.add_row("Tool Calls", f"{today_stats.tool_calls:,}")

    console.print(table)


@app.command()
def export(
    output: Annotated[
        Path,
        typer.Argument(help="Output file path (.json or .csv)"),
    ],
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Number of days to export"),
    ] = 30,
    stats_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to stats-cache.json"),
    ] = None,
) -> None:
    """Export activity data to JSON or CSV."""
    stats = get_stats(stats_file)
    recent = stats.get_recent_activity(days)

    if output.suffix == ".json":
        import json
        data = [
            {
                "date": str(d.date),
                "messages": d.messages,
                "sessions": d.sessions,
                "tool_calls": d.tool_calls,
            }
            for d in recent
        ]
        output.write_text(json.dumps(data, indent=2))
        console.print(f"[green]Exported {len(data)} days to {output}[/]")

    elif output.suffix == ".csv":
        import csv
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "messages", "sessions", "tool_calls"])
            for d in recent:
                writer.writerow([d.date, d.messages, d.sessions, d.tool_calls])
        console.print(f"[green]Exported {len(recent)} days to {output}[/]")

    else:
        console.print("[red]Error:[/] Output file must be .json or .csv")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
