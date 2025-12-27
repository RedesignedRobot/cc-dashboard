"""Claude Stats Mission Control - A beautiful terminal dashboard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import humanize
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Static,
    Label,
    Digits,
    Sparkline,
    ProgressBar,
    RichLog,
    Rule,
)
from textual_plotext import PlotextPlot

from .parser import ClaudeStats


def format_tokens(n: int) -> str:
    """Format token count in human readable form."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_cost(n: float) -> str:
    """Format cost in USD."""
    if n >= 1000:
        return f"${n:,.0f}"
    if n >= 100:
        return f"${n:.1f}"
    if n >= 1:
        return f"${n:.2f}"
    return f"${n:.3f}"


class BigStat(Static):
    """A big statistic display with label and value."""

    def __init__(
        self,
        label: str,
        value: str = "0",
        sublabel: str = "",
        color: str = "green",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.stat_label = label
        self.stat_value = value
        self.stat_sublabel = sublabel
        self.stat_color = color

    def compose(self) -> ComposeResult:
        yield Static(self.stat_label, classes="stat-label")
        yield Static(self.stat_value, classes=f"stat-value {self.stat_color}")
        if self.stat_sublabel:
            yield Static(self.stat_sublabel, classes="stat-sublabel")

    def update_value(self, value: str, sublabel: str = "") -> None:
        self.stat_value = value
        self.stat_sublabel = sublabel
        value_widget = self.query_one(".stat-value", Static)
        value_widget.update(value)
        if sublabel:
            sublabel_widget = self.query_one(".stat-sublabel", Static)
            sublabel_widget.update(sublabel)


class CostPanel(Static):
    """Panel showing cost breakdown."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static("💰 COST BREAKDOWN", classes="panel-title")
        yield Static(id="cost-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        self.stats = stats
        content = self.query_one("#cost-content", Static)

        lines = []
        lines.append(f"[bold green]Total Cost:[/] {format_cost(stats.total_cost)}")
        lines.append(f"[dim]Avg/Day:[/] {format_cost(stats.avg_cost_per_day)}")
        lines.append("")

        # Cost by model
        for model_name, cost in sorted(stats.cost_by_model.items(), key=lambda x: -x[1]):
            if cost > 0.001:
                pct = (cost / stats.total_cost * 100) if stats.total_cost > 0 else 0
                lines.append(f"  {model_name}: {format_cost(cost)} ({pct:.0f}%)")

        lines.append("")
        lines.append(f"[bold cyan]Cache Savings:[/] {format_cost(stats.cache_savings)}")
        lines.append(f"[dim]Cache Hit Rate:[/] {stats.cache_hit_rate:.1f}%")

        content.update("\n".join(lines))


class TokenPanel(Static):
    """Panel showing token usage."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static("🔢 TOKEN USAGE", classes="panel-title")
        yield Static(id="token-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        self.stats = stats
        content = self.query_one("#token-content", Static)

        lines = []
        lines.append(f"[bold]Input:[/]  {format_tokens(stats.total_input_tokens)}")
        lines.append(f"[bold]Output:[/] {format_tokens(stats.total_output_tokens)}")
        lines.append(f"[bold]Total:[/]  {format_tokens(stats.total_tokens)}")
        lines.append("")
        lines.append(f"[dim]Cache Read:[/]  {format_tokens(stats.total_cache_read_tokens)}")
        lines.append(f"[dim]Cache Write:[/] {format_tokens(stats.total_cache_write_tokens)}")
        lines.append("")

        # Model breakdown
        lines.append("[bold]By Model:[/]")
        for usage in sorted(stats.model_usage.values(), key=lambda x: -x.output_tokens):
            if usage.output_tokens > 0:
                lines.append(f"  {usage.display_name}: {format_tokens(usage.output_tokens)}")

        content.update("\n".join(lines))


class ActivityPanel(Static):
    """Panel showing activity summary."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static("📊 ACTIVITY", classes="panel-title")
        yield Static(id="activity-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        self.stats = stats
        content = self.query_one("#activity-content", Static)

        # Get latest vs today
        latest = stats.latest_activity
        today = stats.today_activity

        lines = []

        # Today/Latest stats
        if today:
            lines.append(f"[bold green]Today:[/]")
            lines.append(f"  Messages: {today.messages:,}")
            lines.append(f"  Sessions: {today.sessions}")
            lines.append(f"  Tools: {today.tool_calls:,}")
        elif latest:
            lines.append(f"[bold yellow]Latest ({latest.date}):[/]")
            lines.append(f"  Messages: {latest.messages:,}")
            lines.append(f"  Sessions: {latest.sessions}")
            lines.append(f"  Tools: {latest.tool_calls:,}")
        else:
            lines.append("[dim]No activity data[/]")

        lines.append("")

        # Peak day
        if peak := stats.peak_day:
            lines.append(f"[bold magenta]Peak Day:[/] {peak.date}")
            lines.append(f"  {peak.messages:,} messages")

        # Trend
        trend_icons = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
        trend = stats.usage_trend
        if trend in trend_icons:
            lines.append(f"\n[bold]Trend:[/] {trend_icons[trend]} {trend.title()}")

        content.update("\n".join(lines))


class SessionPanel(Static):
    """Panel showing session info."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static("⏱️ SESSIONS", classes="panel-title")
        yield Static(id="session-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        self.stats = stats
        content = self.query_one("#session-content", Static)

        lines = []
        lines.append(f"[bold]Total:[/] {stats.total_sessions}")
        lines.append(f"[bold]Active Days:[/] {stats.active_days}")
        lines.append(f"[dim]Avg/Day:[/] {stats.avg_sessions_per_day:.1f}")
        lines.append("")

        if longest := stats.longest_session:
            lines.append(f"[bold cyan]Longest Session:[/]")
            lines.append(f"  Duration: {longest.duration_str}")
            lines.append(f"  Messages: {longest.message_count}")
            lines.append(f"  Date: {longest.timestamp.date()}")

        lines.append("")
        lines.append(f"[dim]Since: {stats.first_session_date}[/]")
        lines.append(f"[dim]({stats.days_since_start} days ago)[/]")

        content.update("\n".join(lines))


class HourlyPanel(Static):
    """Panel showing hourly activity distribution."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static("🕐 HOURLY ACTIVITY", classes="panel-title")
        yield Static(id="hourly-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        self.stats = stats
        content = self.query_one("#hourly-content", Static)

        hours, counts = stats.get_hour_series()
        max_count = max(counts) if counts else 1

        # Build sparkline-style display
        blocks = " ▁▂▃▄▅▆▇█"
        line = ""
        for h, count in zip(hours, counts):
            level = int((count / max_count) * 8) if max_count > 0 else 0
            char = blocks[level]
            # Color by time
            if 6 <= h < 12:
                line += f"[yellow]{char}[/]"
            elif 12 <= h < 18:
                line += f"[green]{char}[/]"
            elif 18 <= h < 22:
                line += f"[cyan]{char}[/]"
            else:
                line += f"[magenta]{char}[/]"

        lines = []
        lines.append(line)
        lines.append("[dim]0    6    12   18   23[/]")
        lines.append("")

        # Time of day breakdown
        tod = stats.activity_by_time_of_day
        total = sum(tod.values()) or 1
        lines.append(f"[yellow]Morning:[/] {tod['morning']} ({tod['morning']*100//total}%)")
        lines.append(f"[green]Afternoon:[/] {tod['afternoon']} ({tod['afternoon']*100//total}%)")
        lines.append(f"[cyan]Evening:[/] {tod['evening']} ({tod['evening']*100//total}%)")
        lines.append(f"[magenta]Night:[/] {tod['night']} ({tod['night']*100//total}%)")

        if peak := stats.peak_hour:
            lines.append(f"\n[bold]Peak Hour:[/] {peak}:00")

        content.update("\n".join(lines))


class MessagesChart(PlotextPlot):
    """Chart showing daily message counts."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def on_mount(self) -> None:
        if self.stats:
            self.update_chart(self.stats)

    def update_chart(self, stats: ClaudeStats) -> None:
        self.stats = stats
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dates, messages = stats.get_messages_series(21)

        if messages:
            plt.bar(dates, messages, color="cyan")
            plt.title("Daily Messages (Last 21 Days)")
            plt.xlabel("Date")
            plt.ylabel("Messages")

        self.refresh()


class TokensChart(PlotextPlot):
    """Chart showing daily token usage."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def on_mount(self) -> None:
        if self.stats:
            self.update_chart(self.stats)

    def update_chart(self, stats: ClaudeStats) -> None:
        self.stats = stats
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dates, tokens = stats.get_tokens_series(21)
        # Convert to K for readability
        tokens_k = [t / 1000 for t in tokens]

        if tokens_k:
            plt.bar(dates, tokens_k, color="green")
            plt.title("Daily Tokens (Last 21 Days)")
            plt.xlabel("Date")
            plt.ylabel("Tokens (K)")

        self.refresh()


class ModelChart(PlotextPlot):
    """Chart showing model distribution."""

    def __init__(self, stats: ClaudeStats | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def on_mount(self) -> None:
        if self.stats:
            self.update_chart(self.stats)

    def update_chart(self, stats: ClaudeStats) -> None:
        self.stats = stats
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dist = stats.get_model_distribution()
        # Filter out zero values
        dist = {k: v for k, v in dist.items() if v > 0}

        if dist:
            names = list(dist.keys())
            values = [v / 1_000_000 for v in dist.values()]  # Convert to M

            plt.bar(names, values, color="magenta")
            plt.title("Output Tokens by Model (M)")

        self.refresh()


class HeaderWidget(Static):
    """Custom header with live clock."""

    def compose(self) -> ComposeResult:
        yield Static(id="header-content")

    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1, self.update_time)

    def update_time(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        content = self.query_one("#header-content", Static)
        content.update(
            f"[bold white on blue] ⚡ CLAUDE CODE MISSION CONTROL [/]"
            f"[bold white on dark_blue]  {now}  [/]"
        )


class SummaryBar(Static):
    """Summary bar with key metrics."""

    def compose(self) -> ComposeResult:
        yield Static(id="summary-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        parts = [
            f"[bold]Messages:[/] [green]{stats.total_messages:,}[/]",
            f"[bold]Sessions:[/] [cyan]{stats.total_sessions}[/]",
            f"[bold]Tools:[/] [yellow]{stats.total_tool_calls:,}[/]",
            f"[bold]Cost:[/] [red]{format_cost(stats.total_cost)}[/]",
            f"[bold]Tokens:[/] [magenta]{format_tokens(stats.total_tokens)}[/]",
            f"[bold]Saved:[/] [green]{format_cost(stats.cache_savings)}[/]",
        ]
        content = self.query_one("#summary-content", Static)
        content.update("  │  ".join(parts))


class ClaudeStatsApp(App):
    """Claude Stats Mission Control Dashboard."""

    CSS = """
    Screen {
        background: $surface;
    }

    HeaderWidget {
        dock: top;
        height: 1;
        background: blue;
    }

    #header-content {
        text-align: center;
        width: 100%;
    }

    SummaryBar {
        dock: top;
        height: 1;
        background: $surface-darken-1;
        padding: 0 1;
    }

    #summary-content {
        text-align: center;
    }

    #main-grid {
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1;
        padding: 1;
    }

    .panel {
        border: solid $primary;
        padding: 0 1;
        height: 100%;
    }

    .panel-title {
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 0 1;
        margin-bottom: 1;
    }

    CostPanel {
        column-span: 1;
    }

    TokenPanel {
        column-span: 1;
    }

    ActivityPanel {
        column-span: 1;
    }

    SessionPanel {
        column-span: 1;
    }

    HourlyPanel {
        column-span: 1;
    }

    #charts-container {
        layout: grid;
        grid-size: 3 1;
        grid-gutter: 1;
        padding: 0 1;
        height: 16;
    }

    MessagesChart {
        border: solid $secondary;
    }

    TokensChart {
        border: solid $secondary;
    }

    ModelChart {
        border: solid $secondary;
    }

    .stat-label {
        color: $text-muted;
        text-style: bold;
    }

    .stat-value {
        text-style: bold;
    }

    .stat-sublabel {
        color: $text-muted;
        text-style: italic;
    }

    .green { color: green; }
    .red { color: red; }
    .cyan { color: cyan; }
    .yellow { color: yellow; }
    .magenta { color: magenta; }

    Footer {
        background: $surface-darken-2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    TITLE = "Claude Stats"
    SUB_TITLE = "Mission Control"

    stats: reactive[ClaudeStats | None] = reactive(None)

    def __init__(self, stats_file: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats_file = stats_file

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield SummaryBar()
        yield Container(
            CostPanel(classes="panel"),
            TokenPanel(classes="panel"),
            ActivityPanel(classes="panel"),
            SessionPanel(classes="panel"),
            HourlyPanel(classes="panel"),
            Static("[dim]Loading...[/]", classes="panel", id="placeholder"),
            id="main-grid",
        )
        yield Container(
            MessagesChart(),
            TokensChart(),
            ModelChart(),
            id="charts-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.load_stats()
        # Auto-refresh every 5 seconds
        self.set_interval(5, self.load_stats)

    def load_stats(self) -> None:
        try:
            self.stats = ClaudeStats.from_file(self.stats_file)
        except FileNotFoundError:
            self.notify("Stats file not found", severity="error")
        except Exception as e:
            self.notify(f"Error loading stats: {e}", severity="error")

    def watch_stats(self, stats: ClaudeStats | None) -> None:
        if stats is None:
            return

        # Update all panels
        self.query_one(SummaryBar).update_stats(stats)
        self.query_one(CostPanel).update_stats(stats)
        self.query_one(TokenPanel).update_stats(stats)
        self.query_one(ActivityPanel).update_stats(stats)
        self.query_one(SessionPanel).update_stats(stats)
        self.query_one(HourlyPanel).update_stats(stats)

        # Update charts
        self.query_one(MessagesChart).update_chart(stats)
        self.query_one(TokensChart).update_chart(stats)
        self.query_one(ModelChart).update_chart(stats)

        # Remove placeholder
        try:
            placeholder = self.query_one("#placeholder")
            placeholder.remove()
        except Exception:
            pass

    def action_refresh(self) -> None:
        self.load_stats()
        self.notify("Stats refreshed")


def main() -> None:
    """Entry point."""
    import sys

    stats_file = None
    if len(sys.argv) > 1:
        stats_file = Path(sys.argv[1])

    app = ClaudeStatsApp(stats_file=stats_file)
    app.run()


if __name__ == "__main__":
    main()
