"""Rich-based dashboard rendering for Claude Stats."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich import box

if TYPE_CHECKING:
    from .parser import ClaudeStats, DailyActivity


def format_number(n: int) -> str:
    """Format number with commas."""
    return f"{n:,}"


def format_tokens(n: int) -> str:
    """Format token count in human readable form."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def create_header(stats: ClaudeStats) -> Panel:
    """Create the header panel with summary stats."""
    now = datetime.now().strftime("%H:%M:%S")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column(style="green")
    table.add_column(style="bold")
    table.add_column(style="green")
    table.add_column(style="bold")
    table.add_column(style="green")
    table.add_column(style="bold")
    table.add_column(style="yellow")

    table.add_row(
        "Sessions:", format_number(stats.total_sessions),
        "Messages:", format_number(stats.total_messages),
        "Tools:", format_number(stats.total_tool_calls),
        "Since:", str(stats.first_session_date) if stats.first_session_date else "N/A",
    )

    # Second row with peak and longest
    peak = stats.peak_day
    longest = stats.longest_session

    table2 = Table(show_header=False, box=None, padding=(0, 2))
    table2.add_column(style="bold")
    table2.add_column(style="magenta")
    table2.add_column(style="bold")
    table2.add_column(style="magenta")

    peak_str = f"{peak.date} ({format_number(peak.messages)} msgs)" if peak else "N/A"
    longest_str = f"{longest.duration_hours:.1f}h ({longest.message_count} msgs)" if longest else "N/A"

    table2.add_row(
        "Peak:", peak_str,
        "Longest:", longest_str,
    )

    content = Group(table, table2)

    return Panel(
        content,
        title=f"[bold white on blue] ⚡ CLAUDE CODE STATS [/] [dim]⟳ {now}[/]",
        border_style="cyan",
    )


def create_today_panel(stats: ClaudeStats) -> Panel:
    """Create the today's activity panel."""
    today = stats.today_activity
    today_str = datetime.now().strftime("%b %d")

    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Metric", style="bold", width=10)
    table.add_column("Bar", width=40)
    table.add_column("Value", style="white", justify="right", width=10)

    msgs = today.messages if today else 0
    sessions = today.sessions if today else 0
    tools = today.tool_calls if today else 0

    max_msgs = max(1000, msgs)
    max_sessions = 20
    max_tools = max(300, tools)

    # Messages bar
    msg_pct = min(100, (msgs / max_msgs) * 100)
    table.add_row(
        "Messages",
        f"[green]{'█' * int(msg_pct / 2.5)}[/][dim]{'░' * (40 - int(msg_pct / 2.5))}[/]",
        format_number(msgs),
    )

    # Sessions bar
    sess_pct = min(100, (sessions / max_sessions) * 100)
    table.add_row(
        "Sessions",
        f"[blue]{'█' * int(sess_pct / 2.5)}[/][dim]{'░' * (40 - int(sess_pct / 2.5))}[/]",
        str(sessions),
    )

    # Tools bar
    tool_pct = min(100, (tools / max_tools) * 100)
    table.add_row(
        "Tools",
        f"[magenta]{'█' * int(tool_pct / 2.5)}[/][dim]{'░' * (40 - int(tool_pct / 2.5))}[/]",
        format_number(tools),
    )

    return Panel(
        table,
        title=f"[bold yellow]▸ TODAY[/] [dim]({today_str})[/]",
        border_style="dim",
    )


def create_daily_chart(stats: ClaudeStats, days: int = 14) -> Panel:
    """Create the daily activity chart."""
    recent = stats.get_recent_activity(days)

    if not recent:
        return Panel("[dim]No activity data[/]", title="[bold cyan]▸ RECENT ACTIVITY[/]")

    max_msgs = max(d.messages for d in recent)
    bar_width = 50

    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Date", style="dim", width=6)
    table.add_column("Bar", width=bar_width)
    table.add_column("Count", style="dim", justify="right", width=8)

    for day in recent:
        pct = day.messages / max_msgs if max_msgs > 0 else 0
        bar_len = int(pct * bar_width)

        # Color based on intensity
        if pct > 0.75:
            color = "red"
        elif pct > 0.5:
            color = "yellow"
        else:
            color = "green"

        date_str = day.date.strftime("%m/%d")
        bar = f"[{color}]{'█' * bar_len}[/]"

        table.add_row(date_str, bar, format_number(day.messages))

    return Panel(
        table,
        title=f"[bold cyan]▸ LAST {days} DAYS[/]",
        border_style="dim",
    )


def create_model_panel(stats: ClaudeStats) -> Panel:
    """Create the model usage panel."""
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Model", style="bold", width=12)
    table.add_column("Bar", width=40)
    table.add_column("Tokens", style="white", justify="right", width=12)
    table.add_column("Pct", style="dim", justify="right", width=6)

    total = stats.total_output_tokens or 1

    # Sort by output tokens descending
    models = sorted(
        stats.model_usage.values(),
        key=lambda m: m.output_tokens,
        reverse=True,
    )

    colors = ["red", "yellow", "green", "blue"]

    for i, model in enumerate(models):
        pct = model.output_tokens / total
        bar_len = int(pct * 40)
        color = colors[i % len(colors)]

        bar = f"[{color}]{'█' * bar_len}[/][dim]{'░' * (40 - bar_len)}[/]"

        table.add_row(
            model.display_name,
            bar,
            format_number(model.output_tokens),
            f"({pct * 100:.0f}%)",
        )

    # Cache info
    cache_text = Text(f"\nCache reads: {format_tokens(stats.total_cache_reads)} tokens", style="dim")

    content = Group(table, cache_text)

    return Panel(
        content,
        title="[bold magenta]▸ MODEL USAGE[/] [dim](output tokens)[/]",
        border_style="dim",
    )


def create_hour_chart(stats: ClaudeStats) -> Panel:
    """Create the activity by hour chart."""
    hours = stats.hour_counts
    max_count = max(hours.values()) if hours else 1

    # Build sparkline
    blocks = " ▁▂▃▄▅▆▇█"

    sparkline = Text()
    for hour in range(24):
        count = hours.get(hour, 0)
        level = int((count / max_count) * 8) if max_count > 0 else 0
        char = blocks[level]

        # Color by time of day
        if 9 <= hour < 17:
            color = "yellow"
        elif 17 <= hour < 22:
            color = "green"
        elif hour >= 22 or hour < 2:
            color = "magenta"
        else:
            color = "dim"

        sparkline.append(char, style=color)

    labels = Text("0     6     12    18    23", style="dim")

    content = Group(Text("  ") + sparkline, Text("  ") + labels)

    return Panel(
        content,
        title="[bold blue]▸ ACTIVITY BY HOUR[/]",
        border_style="dim",
    )


def render_dashboard(stats: ClaudeStats, console: Console | None = None) -> None:
    """Render the complete dashboard."""
    if console is None:
        console = Console()

    console.clear()
    console.print(create_header(stats))
    console.print(create_today_panel(stats))
    console.print(create_daily_chart(stats))
    console.print(create_model_panel(stats))
    console.print(create_hour_chart(stats))
    console.print("\n[dim]Press Ctrl+C to exit • Data: ~/.claude/stats-cache.json[/]")


def create_summary_table(stats: ClaudeStats) -> Table:
    """Create a summary table for non-live view."""
    table = Table(title="Claude Code Usage Summary", box=box.ROUNDED)

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Sessions", format_number(stats.total_sessions))
    table.add_row("Total Messages", format_number(stats.total_messages))
    table.add_row("Total Tool Calls", format_number(stats.total_tool_calls))
    table.add_row("Active Days", str(stats.active_days))
    table.add_row("Avg Messages/Day", f"{stats.avg_messages_per_day:.0f}")

    if stats.first_session_date:
        table.add_row("First Session", str(stats.first_session_date))

    if peak := stats.peak_day:
        table.add_row("Peak Day", f"{peak.date} ({format_number(peak.messages)} msgs)")

    if longest := stats.longest_session:
        table.add_row("Longest Session", f"{longest.duration_hours:.1f}h ({longest.message_count} msgs)")

    return table


def create_models_table(stats: ClaudeStats) -> Table:
    """Create a detailed models table."""
    table = Table(title="Model Usage", box=box.ROUNDED)

    table.add_column("Model", style="cyan")
    table.add_column("Input", justify="right", style="green")
    table.add_column("Output", justify="right", style="yellow")
    table.add_column("Cache Read", justify="right", style="blue")
    table.add_column("Cache Create", justify="right", style="magenta")

    for model in sorted(stats.model_usage.values(), key=lambda m: m.output_tokens, reverse=True):
        table.add_row(
            model.display_name,
            format_tokens(model.input_tokens),
            format_tokens(model.output_tokens),
            format_tokens(model.cache_read_tokens),
            format_tokens(model.cache_creation_tokens),
        )

    return table


def create_activity_table(stats: ClaudeStats, days: int = 14) -> Table:
    """Create a detailed activity table."""
    table = Table(title=f"Last {days} Days Activity", box=box.ROUNDED)

    table.add_column("Date", style="cyan")
    table.add_column("Messages", justify="right", style="green")
    table.add_column("Sessions", justify="right", style="blue")
    table.add_column("Tool Calls", justify="right", style="yellow")

    for day in reversed(stats.get_recent_activity(days)):
        table.add_row(
            str(day.date),
            format_number(day.messages),
            str(day.sessions),
            format_number(day.tool_calls),
        )

    return table
