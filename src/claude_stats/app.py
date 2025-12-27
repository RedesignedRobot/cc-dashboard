"""Claude Stats Mission Control - A beautiful terminal dashboard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Static
from textual_plotext import PlotextPlot

from .parser import ClaudeStats
from .themes import THEMES, THEME_NAMES, THEME_DISPLAY_NAMES, get_next_theme


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


class HeaderWidget(Static):
    """Header with title and live clock."""

    def compose(self) -> ComposeResult:
        yield Static(id="header-content")

    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1, self.update_time)

    def update_time(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        content = self.query_one("#header-content", Static)
        content.update(
            f"[bold]⚡ CLAUDE CODE MISSION CONTROL[/]  [dim]│[/]  [bold]{now}[/]"
        )


class SummaryBar(Static):
    """Summary bar with key metrics."""

    def compose(self) -> ComposeResult:
        yield Static(id="summary-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        parts = [
            f"[bold]💬[/] [green]{stats.total_messages:,}[/] msgs",
            f"[bold]🔧[/] [yellow]{stats.total_tool_calls:,}[/] tools",
            f"[bold]💰[/] [red]{format_cost(stats.total_cost)}[/]",
            f"[bold]🎯[/] [cyan]{format_tokens(stats.total_tokens)}[/] tokens",
            f"[bold]💾[/] [green]{format_cost(stats.cache_savings)}[/] saved",
            f"[bold]📅[/] [magenta]{stats.active_days}[/] days",
        ]
        content = self.query_one("#summary-content", Static)
        content.update("  │  ".join(parts))


class CostTokenPanel(Static):
    """Combined cost and token metrics panel."""

    def compose(self) -> ComposeResult:
        yield Static("💰 COST & TOKENS", classes="panel-title")
        yield Static(id="panel-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        content = self.query_one("#panel-content", Static)

        lines = []

        # Cost section
        lines.append(f"[bold red]${stats.total_cost:,.2f}[/] total cost")
        lines.append(f"[dim]${stats.avg_cost_per_day:.2f}/day avg[/]")
        lines.append("")

        # Model costs
        for name, cost in sorted(stats.cost_by_model.items(), key=lambda x: -x[1]):
            if cost > 0.01:
                pct = (cost / stats.total_cost * 100) if stats.total_cost > 0 else 0
                bar_len = int(pct / 5)
                bar = "█" * bar_len
                lines.append(f"[cyan]{name}[/] [green]{bar}[/] {format_cost(cost)}")

        lines.append("")
        lines.append(f"[bold green]Cache savings: {format_cost(stats.cache_savings)}[/]")
        lines.append(f"[dim]Hit rate: {stats.cache_hit_rate:.1f}%[/]")

        content.update("\n".join(lines))


class ActivityPanel(Static):
    """Activity metrics panel."""

    def compose(self) -> ComposeResult:
        yield Static("📊 ACTIVITY", classes="panel-title")
        yield Static(id="panel-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        content = self.query_one("#panel-content", Static)

        latest = stats.latest_activity
        peak = stats.peak_day
        longest = stats.longest_session

        lines = []

        # Latest day
        if latest:
            lines.append(f"[bold yellow]Latest ({latest.date}):[/]")
            lines.append(f"  {latest.messages:,} msgs • {latest.sessions} sess • {latest.tool_calls:,} tools")

        lines.append("")

        # Peak
        if peak:
            lines.append(f"[bold magenta]Peak:[/] {peak.date} ({peak.messages:,} msgs)")

        # Longest session
        if longest:
            lines.append(f"[bold cyan]Longest:[/] {longest.duration_str} ({longest.message_count} msgs)")

        lines.append("")

        # Trend
        trend_icons = {"increasing": "📈 Increasing", "decreasing": "📉 Decreasing", "stable": "➡️ Stable"}
        trend = stats.usage_trend
        if trend in trend_icons:
            lines.append(f"[bold]Trend:[/] {trend_icons[trend]}")

        # Time of day
        lines.append("")
        tod = stats.activity_by_time_of_day
        total = sum(tod.values()) or 1
        peak_time = max(tod.keys(), key=lambda k: tod[k])
        lines.append(f"[bold]Most active:[/] {peak_time.title()}")

        content.update("\n".join(lines))


class MessagesChart(PlotextPlot):
    """Chart showing daily message counts."""

    def update_chart(self, stats: ClaudeStats) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dates, messages = stats.get_messages_series(21)

        if messages:
            plt.bar(dates, messages, color="cyan", fill=True)
            plt.title("Daily Messages")
            plt.xlabel("Date")

        self.refresh()


class TokensChart(PlotextPlot):
    """Chart showing daily token usage."""

    def update_chart(self, stats: ClaudeStats) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dates, tokens = stats.get_tokens_series(21)
        tokens_k = [t / 1000 for t in tokens]

        if tokens_k:
            plt.bar(dates, tokens_k, color="green", fill=True)
            plt.title("Daily Tokens (K)")
            plt.xlabel("Date")

        self.refresh()


class CostChart(PlotextPlot):
    """Chart showing cost by model."""

    def update_chart(self, stats: ClaudeStats) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        costs = stats.cost_by_model
        costs = {k: v for k, v in costs.items() if v > 0.01}

        if costs:
            names = list(costs.keys())
            values = list(costs.values())
            plt.bar(names, values, color="red", fill=True)
            plt.title("Cost by Model ($)")

        self.refresh()


class HourlyChart(PlotextPlot):
    """Chart showing hourly activity."""

    def update_chart(self, stats: ClaudeStats) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        hours, counts = stats.get_hour_series()

        if any(counts):
            plt.bar(hours, counts, color="magenta", fill=True)
            plt.title("Sessions by Hour")
            plt.xlabel("Hour")
            plt.xticks([0, 6, 12, 18, 23])

        self.refresh()


class ClaudeStatsApp(App):
    """Claude Stats Mission Control Dashboard."""

    CSS = """
    Screen {
        background: $background;
    }

    HeaderWidget {
        dock: top;
        height: 1;
        background: $panel;
    }

    #header-content {
        text-align: center;
        width: 100%;
        color: $primary;
    }

    SummaryBar {
        dock: top;
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    #summary-content {
        text-align: center;
    }

    #main-container {
        padding: 1;
    }

    #top-row {
        height: 12;
        layout: horizontal;
    }

    #middle-row {
        height: 1fr;
    }

    #bottom-row {
        height: 1fr;
    }

    .info-panel {
        border: solid $primary 30%;
        padding: 0 1;
        background: $surface;
    }

    .panel-title {
        text-style: bold;
        color: $text;
        background: $panel;
        padding: 0 1;
    }

    .chart-panel {
        border: solid $primary 30%;
        background: $background;
    }

    PlotextPlot {
        background: $background;
    }

    Footer {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "toggle_theme", "Theme"),
    ]

    TITLE = "Claude Stats"
    SUB_TITLE = "Mission Control"

    stats: reactive[ClaudeStats | None] = reactive(None)

    def __init__(self, stats_file: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats_file = stats_file
        self._current_theme_name = "stats-dark"

    def on_mount(self) -> None:
        # Register all custom themes
        for theme in THEMES.values():
            self.register_theme(theme)

        # Set initial theme
        self.theme = "stats-dark"

        self.load_stats()
        self.set_interval(5, self.load_stats)

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield SummaryBar()
        yield Container(
            Horizontal(
                CostTokenPanel(classes="info-panel"),
                ActivityPanel(classes="info-panel"),
                id="top-row",
            ),
            Horizontal(
                MessagesChart(classes="chart-panel"),
                TokensChart(classes="chart-panel"),
                id="middle-row",
            ),
            Horizontal(
                CostChart(classes="chart-panel"),
                HourlyChart(classes="chart-panel"),
                id="bottom-row",
            ),
            id="main-container",
        )
        yield Footer()

    def load_stats(self) -> None:
        try:
            self.stats = ClaudeStats.from_file(self.stats_file)
        except FileNotFoundError:
            self.notify("Stats file not found", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def watch_stats(self, stats: ClaudeStats | None) -> None:
        if stats is None:
            return

        self.query_one(SummaryBar).update_stats(stats)
        self.query_one(CostTokenPanel).update_stats(stats)
        self.query_one(ActivityPanel).update_stats(stats)
        self.query_one(MessagesChart).update_chart(stats)
        self.query_one(TokensChart).update_chart(stats)
        self.query_one(CostChart).update_chart(stats)
        self.query_one(HourlyChart).update_chart(stats)

    def action_refresh(self) -> None:
        self.load_stats()
        self.notify("Refreshed")

    def action_toggle_theme(self) -> None:
        next_theme = get_next_theme(self._current_theme_name)
        self._current_theme_name = next_theme
        self.theme = next_theme
        display_name = THEME_DISPLAY_NAMES.get(next_theme, next_theme)
        self.notify(f"Theme: {display_name}", timeout=1)


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
