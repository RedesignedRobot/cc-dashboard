"""CC Dashboard - Mission Control for Claude Code."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Static
from textual_plotext import PlotextPlot

from . import __version__
from .parser import ClaudeStats, TimeRange
from .themes import THEMES, THEME_DISPLAY_NAMES, get_next_theme
from .updater import ReleaseInfo, check_for_update, perform_update, format_update_message

console = Console()


def format_tokens(n: int, show_unit: bool = True) -> str:
    """Format token count in human readable form with clear units."""
    unit = " tokens" if show_unit else ""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B{unit}"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M{unit}"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K{unit}"
    return f"{n:,}{unit}"


def format_cost(n: float) -> str:
    """Format cost in USD."""
    if n >= 1000:
        return f"${n:,.0f}"
    if n >= 100:
        return f"${n:.1f}"
    if n >= 1:
        return f"${n:.2f}"
    return f"${n:.3f}"


def make_progress_bar(value: float, max_val: float = 100, width: int = 20, filled: str = "█", empty: str = "░") -> str:
    """Create an ASCII progress bar."""
    if max_val == 0:
        pct = 0.0
    else:
        pct = min(value / max_val, 1.0)
    filled_len = int(pct * width)
    return filled * filled_len + empty * (width - filled_len)


class HeaderWidget(Static):
    """Header - Apple-inspired clean design."""

    time_range: reactive[TimeRange] = reactive(TimeRange.QUARTER)
    show_actual_cost: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static(id="header-content")

    def on_mount(self) -> None:
        self.update_header()
        self.set_interval(1, self.update_header)

    def update_header(self) -> None:
        now = datetime.now().strftime("%H:%M")
        content = self.query_one("#header-content", Static)

        # Clean, minimal cache indicator
        if self.show_actual_cost:
            cache_label = "[green]With Cache[/]"
        else:
            cache_label = "[red]No Cache[/]"

        # Spacious, clean layout
        content.update(
            f"[bold white]CC Dashboard[/]"
            f"          "
            f"[bold]{self.time_range.display}[/]"
            f"          "
            f"{cache_label}"
            f"          "
            f"[dim]{now}[/]"
        )

    def watch_time_range(self, time_range: TimeRange) -> None:
        self.update_header()

    def watch_show_actual_cost(self, show: bool) -> None:
        self.update_header()


class MetricCard(Static):
    """A compact metric card with icon, value, and label."""

    def __init__(self, icon: str, label: str, value: str = "—", **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.label = label
        self._value = value

    def compose(self) -> ComposeResult:
        yield Static(id="metric-content")

    def on_mount(self) -> None:
        self.update_display()

    def update_value(self, value: str) -> None:
        self._value = value
        self.update_display()

    def update_display(self) -> None:
        content = self.query_one("#metric-content", Static)
        content.update(f"{self.icon} [bold]{self._value}[/]\n[dim]{self.label}[/]")


class ProgressCard(Static):
    """A card with a progress bar and percentage."""

    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self._value = 0.0

    def compose(self) -> ComposeResult:
        yield Static(id="progress-content")

    def on_mount(self) -> None:
        self.update_display()

    def update_value(self, value: float) -> None:
        self._value = value
        self.update_display()

    def update_display(self) -> None:
        content = self.query_one("#progress-content", Static)
        bar = make_progress_bar(self._value, 100, 15)
        color = "green" if self._value >= 70 else "yellow" if self._value >= 40 else "red"
        content.update(f"[{color}]{bar}[/] [bold]{self._value:.1f}%[/]\n[dim]{self.label}[/]")


class StatsPanel(Static):
    """Panel showing key statistics - Apple-inspired minimal design."""

    def compose(self) -> ComposeResult:
        yield Static(id="stats-content")

    def update_stats(self, stats: ClaudeStats, show_actual_cost: bool = False) -> None:
        """Update stats display with clean, minimal Apple-style aesthetics."""
        content = self.query_one("#stats-content", Static)

        if stats is None:
            content.update("[dim]Loading...[/]")
            return

        # Determine cost display based on cache mode
        if show_actual_cost:
            display_cost = stats.total_cost
            cost_color = "green"
            cache_note = f"[dim]saved ${stats.cache_savings:,.0f}[/]"
        else:
            display_cost = stats.cost_without_cache
            cost_color = "red"
            cache_note = f"[dim]without cache[/]"

        # Apple-style: Big bold numbers, clear labels, generous spacing
        # Each metric on its own line with clear units
        lines = [
            "",
            f"[bold {cost_color}]  ${display_cost:,.2f}[/]",
            f"  [dim]Total Cost[/]  {cache_note}",
            "",
            f"[bold white]  {stats.total_messages:,}[/]          [bold white]{stats.total_sessions:,}[/]          [bold white]{stats.total_tool_calls:,}[/]",
            f"  [dim]Messages[/]           [dim]Sessions[/]          [dim]Tool Calls[/]",
            "",
            f"[bold cyan]  {format_tokens(stats.total_tokens_with_cache)}[/]",
            f"  [dim]Total Tokens[/]",
            "",
        ]

        content.update("\n".join(lines))


class TokenBreakdownPanel(Static):
    """Visual breakdown of token types - clean design."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Token Breakdown[/]", classes="panel-title")
        yield Static(id="tokens-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        content = self.query_one("#tokens-content", Static)

        total = stats.total_tokens_with_cache or 1
        tokens = stats.tokens_by_type

        lines = [""]
        colors = {"Input": "cyan", "Output": "green", "Cache Read": "yellow", "Cache Write": "magenta"}

        for name, count in tokens.items():
            pct = (count / total) * 100
            bar = make_progress_bar(pct, 100, 15)
            color = colors.get(name, "white")
            # Show tokens with clear unit
            lines.append(f"  [{color}]{name:12}[/] {bar} [bold]{format_tokens(count, show_unit=False)}[/]")

        lines.append("")

        content.update("\n".join(lines))


class ModelCostPanel(Static):
    """Cost breakdown by model - clean design."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Cost by Model[/]", classes="panel-title")
        yield Static(id="cost-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        content = self.query_one("#cost-content", Static)

        costs = stats.cost_by_model
        total = stats.total_cost or 1

        lines = [""]
        colors = ["cyan", "green", "yellow", "magenta"]

        for i, (name, cost) in enumerate(sorted(costs.items(), key=lambda x: -x[1])):
            if cost > 0.01:
                pct = (cost / total) * 100
                bar = make_progress_bar(pct, 100, 12)
                color = colors[i % len(colors)]
                lines.append(f"  [{color}]{name:10}[/] {bar} [bold]{format_cost(cost)}[/]")

        lines.append("")

        content.update("\n".join(lines))


class ProductivityPanel(Static):
    """Productivity metrics - clean design."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Efficiency[/]", classes="panel-title")
        yield Static(id="prod-content")

    def update_stats(self, stats: ClaudeStats) -> None:
        content = self.query_one("#prod-content", Static)

        score = stats.productivity_score
        cache = stats.cache_efficiency

        score_bar = make_progress_bar(score, 100, 15)
        cache_bar = make_progress_bar(cache, 100, 15)

        score_color = "green" if score >= 70 else "yellow" if score >= 40 else "red"
        cache_color = "green" if cache >= 80 else "yellow" if cache >= 50 else "red"

        lines = [
            "",
            f"  [dim]Score[/]    [{score_color}]{score_bar}[/] [bold]{score}[/]",
            f"  [dim]Cache[/]    [{cache_color}]{cache_bar}[/] [bold]{cache:.0f}%[/]",
            "",
        ]

        content.update("\n".join(lines))


class MessagesLineChart(PlotextPlot):
    """Line chart for daily/hourly messages."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        # Use hourly data for Today, daily data for other ranges
        if time_range == TimeRange.TODAY:
            hours, messages = stats.get_hourly_messages()
            title = "Messages by Hour (Today)"
        else:
            _, messages = stats.get_messages_series(time_range.days)
            title = f"Messages ({time_range.display})"

        if messages and any(messages):
            plt.plot(messages, color="cyan", marker="braille")
            plt.scatter(messages, color="cyan", marker="dot")
            plt.title(title)

        self.refresh()


class TokensLineChart(PlotextPlot):
    """Line chart for daily/hourly tokens."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange, show_actual_cost: bool = False) -> None:
        """Update tokens chart.

        Args:
            stats: The ClaudeStats object
            time_range: Time range to display
            show_actual_cost: True = WITH CACHE (show all tokens including cache)
                              False = NO CACHE (show base tokens only)
        """
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        # Safety check
        if stats is None:
            self.refresh()
            return

        # Use hourly data for Today, daily data for other ranges
        if time_range == TimeRange.TODAY:
            _, tokens = stats.get_hourly_tokens()
            title = "Tokens/Hour"
        else:
            _, tokens = stats.get_tokens_series(time_range.days)
            title = f"Tokens ({time_range.display})"

        # CACHE LOGIC for tokens:
        # show_actual_cost=True  -> "With Cache" -> show total tokens INCLUDING cache
        # show_actual_cost=False -> "No Cache"   -> show base tokens only (input+output)
        if show_actual_cost and stats.total_tokens > 0:
            # WITH CACHE: Scale up to include cache tokens
            scale = stats.total_tokens_with_cache / stats.total_tokens
            tokens = [int(t * scale) for t in tokens]
            title = f"All Tokens ({time_range.display})"

        # Convert to millions for display
        tokens_m = [t / 1_000_000 for t in tokens]

        if tokens_m and any(tokens_m):
            plt.plot(tokens_m, color="green", marker="braille")
            plt.title(title)

        self.refresh()


class CostLineChart(PlotextPlot):
    """Cumulative cost line chart."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange, show_actual_cost: bool = False) -> None:
        """Update cost chart.

        Args:
            stats: The ClaudeStats object
            time_range: Time range to display
            show_actual_cost: True = WITH CACHE (show actual billed cost - lower)
                              False = NO CACHE (show hypothetical full cost - higher)
        """
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        # Safety check
        if stats is None:
            self.refresh()
            return

        # Use hourly data for Today, daily data for other ranges
        if time_range == TimeRange.TODAY:
            _, costs = stats.get_hourly_cost()
            title = "Cost/Hour"
        else:
            _, costs = stats.get_cumulative_cost(time_range.days)
            title = f"Cost ({time_range.display})"

        # CACHE LOGIC for cost:
        # show_actual_cost=True  -> "With Cache" -> show actual cost (with cache discounts)
        # show_actual_cost=False -> "No Cache"   -> show hypothetical cost (no cache discounts)
        if not show_actual_cost and stats.total_cost > 0:
            # NO CACHE: Scale up to show what it would cost without caching
            scale = stats.cost_without_cache / stats.total_cost
            costs = [c * scale for c in costs]
            title = f"Cost No Cache ({time_range.display})"

        if costs and any(costs):
            plt.plot(costs, color="red", marker="braille")
            plt.title(title)

        self.refresh()


class HourlyBarChart(PlotextPlot):
    """Hourly activity bar chart."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        hours, counts = stats.get_hour_series()

        if any(counts):
            plt.bar(hours, counts, color="magenta", fill=True)
            plt.title("Sessions by Hour")
            plt.xticks([0, 6, 12, 18, 23])

        self.refresh()


class DayOfWeekChart(PlotextPlot):
    """Day of week distribution chart."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        days, counts = stats.get_day_of_week_distribution()

        if any(counts):
            plt.bar(days, counts, color="yellow", fill=True)
            plt.title("Messages by Day")

        self.refresh()


class ToolsLineChart(PlotextPlot):
    """Tool calls trend chart."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        # Use hourly data for Today, daily data for other ranges
        if time_range == TimeRange.TODAY:
            hours, tools = stats.get_hourly_tools()
            title = "Tools by Hour (Today)"
        else:
            _, tools = stats.get_tools_series(time_range.days)
            title = f"Tools ({time_range.display})"

        if tools and any(tools):
            plt.plot(tools, color="orange", marker="braille")
            plt.title(title)

        self.refresh()


class SessionsBarChart(PlotextPlot):
    """Sessions bar chart."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        # Use hourly data for Today, daily data for other ranges
        if time_range == TimeRange.TODAY:
            hours, sessions = stats.get_hourly_sessions()
            title = "Sessions by Hour (Today)"
        else:
            _, sessions = stats.get_sessions_series(time_range.days)
            title = f"Sessions ({time_range.display})"

        if sessions and any(sessions):
            plt.bar(range(len(sessions)), sessions, color="cyan", fill=True)
            plt.title(title)

        self.refresh()


class ModelDistributionChart(PlotextPlot):
    """Model usage distribution as horizontal bar."""

    def update_chart(self, stats: ClaudeStats, time_range: TimeRange) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.theme("dark")

        dist = stats.get_model_distribution()
        dist = {k: v for k, v in dist.items() if v > 0}

        if dist:
            names = list(dist.keys())
            values = [v / 1_000_000 for v in dist.values()]  # Convert to millions
            plt.bar(names, values, color="blue", orientation="horizontal", width=0.6)
            plt.title("Model Output (M tokens)")

        self.refresh()


class CCDashboardApp(App):
    """CC Dashboard - Mission Control for Claude Code."""

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

    #main-container {
        padding: 0 1;
    }

    #top-section {
        height: auto;
        max-height: 12;
    }

    #charts-section {
        height: 1fr;
    }

    #row1, #row2, #row3 {
        height: 1fr;
    }

    .stats-panel {
        border: solid $primary 30%;
        padding: 0 1;
        background: $surface;
        height: 100%;
    }

    .panel-title {
        text-style: bold;
        color: $text;
        background: $panel;
        padding: 0 1;
        margin-bottom: 1;
    }

    .chart-panel {
        border: solid $primary 20%;
        background: $background;
    }

    .metric-card {
        border: solid $primary 20%;
        padding: 0 1;
        background: $surface;
        height: 4;
        content-align: center middle;
        text-align: center;
    }

    PlotextPlot {
        background: $background;
    }

    Footer {
        background: $surface;
    }

    #metric-content, #progress-content {
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "toggle_theme", "Theme"),
        Binding("c", "toggle_cache_mode", "Cache"),
        Binding("u", "do_update", "Update"),
        Binding("1", "range_today", "Today"),
        Binding("2", "range_week", "Week"),
        Binding("3", "range_month", "Month"),
        Binding("4", "range_quarter", "3 Months"),
        Binding("5", "range_all", "All Time"),
    ]

    TITLE = "CC Dashboard"
    SUB_TITLE = "Mission Control for Claude Code"

    stats: reactive[ClaudeStats | None] = reactive(None)
    time_range: reactive[TimeRange] = reactive(TimeRange.QUARTER)
    # CACHE MODE SEMANTICS:
    # show_actual_cost=False (default) -> "No Cache" mode -> show hypothetical full cost (higher)
    # show_actual_cost=True            -> "With Cache" mode -> show actual billed cost (lower)
    show_actual_cost: reactive[bool] = reactive(False)

    def __init__(self, stats_file: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats_file = stats_file
        self._current_theme_name = "stats-dark"
        self._raw_stats: ClaudeStats | None = None
        self._available_update: ReleaseInfo | None = None

    def on_mount(self) -> None:
        # Register all custom themes
        for theme in THEMES.values():
            self.register_theme(theme)

        # Set initial theme
        self.theme = "stats-dark"

        self.load_stats()
        self.set_interval(5, self.load_stats)

        # Check for updates in background (non-blocking)
        self.run_worker(self._check_for_updates, thread=True)

    def compose(self) -> ComposeResult:
        yield HeaderWidget()
        yield Container(
            # Top section: Key metrics panels
            Horizontal(
                StatsPanel(classes="stats-panel"),
                Vertical(
                    TokenBreakdownPanel(classes="stats-panel"),
                    id="token-section",
                ),
                Vertical(
                    ModelCostPanel(classes="stats-panel"),
                    ProductivityPanel(classes="stats-panel"),
                    id="cost-section",
                ),
                id="top-section",
            ),
            # Charts section
            Container(
                Horizontal(
                    MessagesLineChart(classes="chart-panel"),
                    TokensLineChart(classes="chart-panel"),
                    CostLineChart(classes="chart-panel"),
                    ToolsLineChart(classes="chart-panel"),
                    id="row1",
                ),
                Horizontal(
                    HourlyBarChart(classes="chart-panel"),
                    DayOfWeekChart(classes="chart-panel"),
                    SessionsBarChart(classes="chart-panel"),
                    ModelDistributionChart(classes="chart-panel"),
                    id="row2",
                ),
                id="charts-section",
            ),
            id="main-container",
        )
        yield Footer()

    def load_stats(self) -> None:
        try:
            self._raw_stats = ClaudeStats.from_file(self.stats_file)
            self._apply_time_filter()
        except FileNotFoundError:
            self.notify("Stats file not found. Use Claude Code first!", severity="error")
        except Exception as e:
            self.notify(f"Error loading stats: {e}", severity="error")

    def _apply_time_filter(self) -> None:
        """Apply the current time range filter to stats."""
        if self._raw_stats is None:
            return
        self.stats = self._raw_stats.filter_by_range(self.time_range)
        # Update header with current range and cache mode
        try:
            header = self.query_one(HeaderWidget)
            header.time_range = self.time_range
            header.show_actual_cost = self.show_actual_cost
        except Exception:
            pass

    def watch_time_range(self, time_range: TimeRange) -> None:
        """React to time range changes."""
        self._apply_time_filter()

    def watch_show_actual_cost(self, show: bool) -> None:
        """React to cache mode changes.

        show=True  -> "With Cache" (actual billed cost)
        show=False -> "No Cache" (hypothetical full cost)
        """
        # Update header
        try:
            header = self.query_one(HeaderWidget)
            header.show_actual_cost = show
        except Exception:
            pass
        # Refresh stats display
        if self.stats:
            self._update_displays()

    def action_toggle_cache_mode(self) -> None:
        """Toggle between cache/no-cache cost view."""
        self.show_actual_cost = not self.show_actual_cost
        if self.show_actual_cost:
            self.notify("💰 WITH CACHE (actual cost)", timeout=2)
        else:
            self.notify("💸 NO CACHE (hypothetical)", timeout=2)

    def _set_range(self, time_range: TimeRange) -> None:
        """Set time range and notify."""
        self.time_range = time_range
        self.notify(f"📊 {self.time_range.display}", timeout=1)

    def action_range_today(self) -> None:
        self._set_range(TimeRange.TODAY)

    def action_range_week(self) -> None:
        self._set_range(TimeRange.WEEK)

    def action_range_month(self) -> None:
        self._set_range(TimeRange.MONTH)

    def action_range_quarter(self) -> None:
        self._set_range(TimeRange.QUARTER)

    def action_range_all(self) -> None:
        self._set_range(TimeRange.ALL_TIME)

    def watch_stats(self, stats: ClaudeStats | None) -> None:
        if stats is None:
            return
        self._update_displays()

    def _update_displays(self) -> None:
        """Update all display panels and charts with current stats and settings.

        CACHE MODE SEMANTICS (used consistently across all components):
        - show_actual_cost=True  -> "With Cache" -> actual billed cost (lower), all tokens
        - show_actual_cost=False -> "No Cache"   -> hypothetical full cost (higher), base tokens
        """
        stats = self.stats
        if stats is None:
            return

        # Get current cache mode setting
        # True = WITH CACHE (actual cost)
        # False = NO CACHE (hypothetical cost)
        cache_mode = self.show_actual_cost

        # Update all panels (StatsPanel needs cache mode)
        self.query_one(StatsPanel).update_stats(stats, cache_mode)
        self.query_one(TokenBreakdownPanel).update_stats(stats)
        self.query_one(ModelCostPanel).update_stats(stats)
        self.query_one(ProductivityPanel).update_stats(stats)

        # Update all charts with time range and cache mode
        tr = self.time_range
        self.query_one(MessagesLineChart).update_chart(stats, tr)
        self.query_one(TokensLineChart).update_chart(stats, tr, cache_mode)
        self.query_one(CostLineChart).update_chart(stats, tr, cache_mode)
        self.query_one(ToolsLineChart).update_chart(stats, tr)
        self.query_one(HourlyBarChart).update_chart(stats, tr)
        self.query_one(DayOfWeekChart).update_chart(stats, tr)
        self.query_one(SessionsBarChart).update_chart(stats, tr)
        self.query_one(ModelDistributionChart).update_chart(stats, tr)

    def action_refresh(self) -> None:
        self.load_stats()
        self.notify("Refreshed")

    def action_toggle_theme(self) -> None:
        next_theme = get_next_theme(self._current_theme_name)
        self._current_theme_name = next_theme
        self.theme = next_theme
        display_name = THEME_DISPLAY_NAMES.get(next_theme, next_theme)
        self.notify(f"Theme: {display_name}", timeout=1)

    def _check_for_updates(self) -> None:
        """Background worker to check for updates."""
        release = check_for_update()
        if release:
            self._available_update = release
            self.call_from_thread(self._show_update_notification)

    def _show_update_notification(self) -> None:
        """Show update notification to user."""
        if self._available_update:
            self.notify(
                f"Update available: v{self._available_update.version} (press 'u')",
                title="New Version",
                timeout=10,
            )

    def action_do_update(self) -> None:
        """Perform the update when user presses 'u'."""
        if not self._available_update:
            self.notify("Already up to date!", timeout=2)
            return

        self.notify("Updating... please wait", timeout=0)
        self.run_worker(self._perform_update, thread=True)

    def _perform_update(self) -> None:
        """Background worker to perform update."""
        success, message = perform_update()
        self.call_from_thread(lambda: self.notify(message, timeout=10))


def run_startup_checks() -> tuple[bool, list[str]]:
    """Run comprehensive startup checks.

    Returns:
        (success, list of warning/error messages)
    """
    messages = []
    claude_dir = Path.home() / ".claude"

    # Check 1: Claude Code directory exists
    if not claude_dir.exists():
        messages.append("[red]✗[/] Claude Code not installed (~/.claude not found)")
        messages.append("  Install from: [cyan]https://claude.ai/claude-code[/]")
        return False, messages

    messages.append("[green]✓[/] Claude Code directory found")

    # Check 2: Stats file exists
    stats_file = claude_dir / "stats-cache.json"
    if not stats_file.exists():
        messages.append("[red]✗[/] Stats file not found")
        messages.append("  Use Claude Code to generate usage data first")
        return False, messages

    messages.append("[green]✓[/] Stats file found")

    # Check 3: Stats file is valid JSON
    try:
        import json
        with open(stats_file) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            messages.append("[red]✗[/] Stats file is not valid JSON object")
            return False, messages
        messages.append("[green]✓[/] Stats file is valid JSON")
    except json.JSONDecodeError as e:
        messages.append(f"[red]✗[/] Stats file has invalid JSON: {e}")
        return False, messages
    except Exception as e:
        messages.append(f"[red]✗[/] Error reading stats file: {e}")
        return False, messages

    # Check 4: Required keys present
    required_keys = ["totalSessions", "totalMessages", "modelUsage"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        messages.append(f"[yellow]![/] Stats file missing keys: {missing_keys}")
    else:
        messages.append("[green]✓[/] Stats file has required data")

    # Check 5: Has some data
    if data.get("totalSessions", 0) == 0:
        messages.append("[yellow]![/] No sessions recorded yet - use Claude Code first")

    return True, messages


def check_stats_file(path: Path | None) -> Path:
    """Check if stats file exists and return the path."""
    if path is None:
        path = Path.home() / ".claude" / "stats-cache.json"

    if not path.exists():
        console.print("[bold red]⚡ CC Dashboard - Startup Check Failed[/]")
        console.print()
        success, messages = run_startup_checks()
        for msg in messages:
            console.print(f"  {msg}")
        console.print()
        if not success:
            console.print("[yellow]To fix:[/]")
            console.print("  1. Install Claude Code: [cyan]https://claude.ai/claude-code[/]")
            console.print("  2. Use Claude Code for a bit to generate usage data")
            console.print("  3. Run [bold]ccd[/] again")
            console.print()
            sys.exit(1)

    return path


def main() -> None:
    """Entry point for CC Dashboard."""
    parser = argparse.ArgumentParser(
        prog="ccd",
        description="⚡ CC Dashboard - Mission Control for Claude Code",
        epilog="Press 1-5 for time ranges, 'c' for cache toggle, 't' for themes, 'r' to refresh, 'q' to quit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "stats_file",
        nargs="?",
        type=Path,
        help="Path to stats-cache.json (default: ~/.claude/stats-cache.json)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run startup checks and exit",
    )

    args = parser.parse_args()

    # If --check flag, just run checks and exit
    if args.check:
        console.print("[bold]⚡ CC Dashboard - Startup Checks[/]")
        console.print()
        success, messages = run_startup_checks()
        for msg in messages:
            console.print(f"  {msg}")
        console.print()
        sys.exit(0 if success else 1)

    # Check stats file exists
    stats_file = check_stats_file(args.stats_file)

    # Launch the dashboard
    app = CCDashboardApp(stats_file=stats_file)
    app.run()


if __name__ == "__main__":
    main()
