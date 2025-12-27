"""Parse Claude Code stats with comprehensive cost calculations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any
from enum import Enum


class TimeRange(Enum):
    """Time ranges for filtering statistics."""
    TODAY = ("today", "Today", 1)
    WEEK = ("week", "This Week", 7)
    MONTH = ("month", "This Month", 30)
    QUARTER = ("quarter", "Last 3 Months", 90)
    ALL_TIME = ("all", "All Time", 365)

    def __init__(self, key: str, display: str, days: int):
        self.key = key
        self.display = display
        self.days = days

    @classmethod
    def next(cls, current: "TimeRange") -> "TimeRange":
        """Get the next time range in the cycle."""
        members = list(cls)
        idx = members.index(current)
        return members[(idx + 1) % len(members)]


class Model(Enum):
    """Claude models with pricing info (per million tokens, December 2025)."""
    # Format: (input_price, output_price, cache_write_multiplier, cache_read_multiplier)
    OPUS_4_5 = ("claude-opus-4-5-20251101", 5.00, 25.00, 1.25, 0.10)
    OPUS_4_1 = ("claude-opus-4-1-20250805", 15.00, 75.00, 1.25, 0.10)
    SONNET_4_5 = ("claude-sonnet-4-5-20250929", 3.00, 15.00, 1.25, 0.10)
    HAIKU_4_5 = ("claude-haiku-4-5-20251001", 0.80, 4.00, 1.25, 0.10)

    def __init__(self, model_id: str, input_price: float, output_price: float,
                 cache_write_mult: float, cache_read_mult: float):
        self.model_id = model_id
        self.input_price = input_price  # per million tokens
        self.output_price = output_price
        self.cache_write_mult = cache_write_mult
        self.cache_read_mult = cache_read_mult

    @classmethod
    def from_id(cls, model_id: str) -> Model | None:
        for model in cls:
            if model.model_id == model_id:
                return model
        return None

    @property
    def display_name(self) -> str:
        names = {
            "claude-opus-4-5-20251101": "Opus 4.5",
            "claude-opus-4-1-20250805": "Opus 4.1",
            "claude-sonnet-4-5-20250929": "Sonnet 4.5",
            "claude-haiku-4-5-20251001": "Haiku 4.5",
        }
        return names.get(self.model_id, self.model_id)


@dataclass
class DailyActivity:
    """Activity metrics for a single day."""
    date: date
    messages: int
    sessions: int
    tool_calls: int
    tokens_by_model: dict[str, int] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return sum(self.tokens_by_model.values())

    @classmethod
    def from_dict(cls, data: dict[str, Any], tokens_data: dict[str, int] | None = None) -> DailyActivity:
        return cls(
            date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            messages=data.get("messageCount", 0),
            sessions=data.get("sessionCount", 0),
            tool_calls=data.get("toolCallCount", 0),
            tokens_by_model=tokens_data or {},
        )


@dataclass
class ModelUsage:
    """Complete usage and cost statistics for a model."""
    model_id: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int

    @property
    def model(self) -> Model | None:
        return Model.from_id(self.model_id)

    @property
    def display_name(self) -> str:
        if model := self.model:
            return model.display_name
        return self.model_id

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def total_tokens_including_cache(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_read_tokens + self.cache_creation_tokens

    def calculate_cost(self) -> float:
        """Calculate total cost in USD."""
        model = self.model
        if not model:
            return 0.0

        # Regular input/output
        input_cost = (self.input_tokens / 1_000_000) * model.input_price
        output_cost = (self.output_tokens / 1_000_000) * model.output_price

        # Cache costs
        cache_write_cost = (self.cache_creation_tokens / 1_000_000) * model.input_price * model.cache_write_mult
        cache_read_cost = (self.cache_read_tokens / 1_000_000) * model.input_price * model.cache_read_mult

        return input_cost + output_cost + cache_write_cost + cache_read_cost

    @property
    def cost_breakdown(self) -> dict[str, float]:
        """Get detailed cost breakdown."""
        model = self.model
        if not model:
            return {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}

        return {
            "input": (self.input_tokens / 1_000_000) * model.input_price,
            "output": (self.output_tokens / 1_000_000) * model.output_price,
            "cache_write": (self.cache_creation_tokens / 1_000_000) * model.input_price * model.cache_write_mult,
            "cache_read": (self.cache_read_tokens / 1_000_000) * model.input_price * model.cache_read_mult,
        }


@dataclass
class LongestSession:
    """Information about the longest session."""
    session_id: str
    duration_ms: int
    message_count: int
    timestamp: datetime

    @property
    def duration_hours(self) -> float:
        return self.duration_ms / 3_600_000

    @property
    def duration_str(self) -> str:
        hours = self.duration_ms // 3_600_000
        minutes = (self.duration_ms % 3_600_000) // 60_000
        return f"{hours}h {minutes}m"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LongestSession | None:
        if not data:
            return None
        return cls(
            session_id=data.get("sessionId", ""),
            duration_ms=data.get("duration", 0),
            message_count=data.get("messageCount", 0),
            timestamp=datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00")),
        )


@dataclass
class ClaudeStats:
    """Complete Claude Code statistics with cost calculations."""
    total_sessions: int
    total_messages: int
    first_session_date: date | None
    last_computed_date: date | None
    daily_activity: list[DailyActivity]
    model_usage: dict[str, ModelUsage]
    longest_session: LongestSession | None
    hour_counts: dict[int, int]
    raw_data: dict[str, Any] = field(default_factory=dict)

    # ===== Aggregate Properties =====

    @property
    def total_tool_calls(self) -> int:
        return sum(d.tool_calls for d in self.daily_activity)

    @property
    def active_days(self) -> int:
        return len(self.daily_activity)

    @property
    def total_cost(self) -> float:
        """Total cost in USD."""
        return sum(m.calculate_cost() for m in self.model_usage.values())

    @property
    def cost_by_model(self) -> dict[str, float]:
        """Cost breakdown by model."""
        return {m.display_name: m.calculate_cost() for m in self.model_usage.values()}

    # ===== Token Statistics =====

    @property
    def total_input_tokens(self) -> int:
        return sum(m.input_tokens for m in self.model_usage.values())

    @property
    def total_output_tokens(self) -> int:
        return sum(m.output_tokens for m in self.model_usage.values())

    @property
    def total_cache_read_tokens(self) -> int:
        return sum(m.cache_read_tokens for m in self.model_usage.values())

    @property
    def total_cache_write_tokens(self) -> int:
        return sum(m.cache_creation_tokens for m in self.model_usage.values())

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_tokens_with_cache(self) -> int:
        return self.total_tokens + self.total_cache_read_tokens + self.total_cache_write_tokens

    @property
    def cache_hit_rate(self) -> float:
        """Percentage of input tokens that came from cache."""
        total_input = self.total_input_tokens + self.total_cache_read_tokens
        if total_input == 0:
            return 0.0
        return (self.total_cache_read_tokens / total_input) * 100

    @property
    def cache_savings(self) -> float:
        """Estimated cost savings from cache in USD."""
        # What it would have cost without cache (at full input price)
        savings = 0.0
        for usage in self.model_usage.values():
            if model := usage.model:
                # Full price vs cache read price
                full_cost = (usage.cache_read_tokens / 1_000_000) * model.input_price
                cache_cost = (usage.cache_read_tokens / 1_000_000) * model.input_price * model.cache_read_mult
                savings += (full_cost - cache_cost)
        return savings

    @property
    def cost_without_cache(self) -> float:
        """Hypothetical cost if no caching was used (full input price for all tokens)."""
        return self.total_cost + self.cache_savings

    @property
    def avg_cost_per_session_no_cache(self) -> float:
        """Average cost per session without cache discount."""
        if not self.total_sessions:
            return 0
        return self.cost_without_cache / self.total_sessions

    # ===== Daily/Activity Statistics =====

    @property
    def peak_day(self) -> DailyActivity | None:
        if not self.daily_activity:
            return None
        return max(self.daily_activity, key=lambda d: d.messages)

    @property
    def today_activity(self) -> DailyActivity | None:
        """Get today's activity if available."""
        today = date.today()
        for activity in self.daily_activity:
            if activity.date == today:
                return activity
        return None

    @property
    def yesterday_activity(self) -> DailyActivity | None:
        """Get yesterday's activity if available."""
        yesterday = date.today() - timedelta(days=1)
        for activity in self.daily_activity:
            if activity.date == yesterday:
                return activity
        return None

    @property
    def latest_activity(self) -> DailyActivity | None:
        """Get the most recent day's activity."""
        if not self.daily_activity:
            return None
        return self.daily_activity[-1]

    @property
    def avg_messages_per_day(self) -> float:
        if not self.active_days:
            return 0
        return self.total_messages / self.active_days

    @property
    def avg_sessions_per_day(self) -> float:
        if not self.active_days:
            return 0
        return self.total_sessions / self.active_days

    @property
    def avg_tools_per_day(self) -> float:
        if not self.active_days:
            return 0
        return self.total_tool_calls / self.active_days

    @property
    def avg_cost_per_day(self) -> float:
        if not self.active_days:
            return 0
        return self.total_cost / self.active_days

    @property
    def avg_tokens_per_message(self) -> float:
        """Average tokens used per message."""
        if not self.total_messages:
            return 0
        return self.total_tokens / self.total_messages

    @property
    def avg_tokens_per_session(self) -> float:
        """Average tokens used per session."""
        if not self.total_sessions:
            return 0
        return self.total_tokens / self.total_sessions

    @property
    def avg_messages_per_session(self) -> float:
        """Average messages per session."""
        if not self.total_sessions:
            return 0
        return self.total_messages / self.total_sessions

    @property
    def avg_cost_per_session(self) -> float:
        """Average cost per session."""
        if not self.total_sessions:
            return 0
        return self.total_cost / self.total_sessions

    @property
    def avg_tools_per_session(self) -> float:
        """Average tool calls per session."""
        if not self.total_sessions:
            return 0
        return self.total_tool_calls / self.total_sessions

    @property
    def input_output_ratio(self) -> float:
        """Ratio of input to output tokens."""
        if not self.total_output_tokens:
            return 0
        return self.total_input_tokens / self.total_output_tokens

    @property
    def cache_efficiency(self) -> float:
        """How much of potential cache was utilized (0-100%)."""
        total_cacheable = self.total_input_tokens + self.total_cache_read_tokens
        if not total_cacheable:
            return 0
        return (self.total_cache_read_tokens / total_cacheable) * 100

    @property
    def cost_saved_percentage(self) -> float:
        """Percentage of potential cost saved through caching."""
        potential_cost = self.total_cost + self.cache_savings
        if not potential_cost:
            return 0
        return (self.cache_savings / potential_cost) * 100

    @property
    def longest_streak(self) -> int:
        """Longest consecutive days streak."""
        if not self.daily_activity:
            return 0

        streak = 1
        max_streak = 1
        sorted_days = sorted(self.daily_activity, key=lambda x: x.date)

        for i in range(1, len(sorted_days)):
            if (sorted_days[i].date - sorted_days[i-1].date).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1

        return max_streak

    @property
    def current_streak(self) -> int:
        """Current consecutive days streak (ending today or yesterday)."""
        if not self.daily_activity:
            return 0

        sorted_days = sorted(self.daily_activity, key=lambda x: x.date, reverse=True)
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Check if most recent is today or yesterday
        if sorted_days[0].date not in (today, yesterday):
            return 0

        streak = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i-1].date - sorted_days[i].date).days == 1:
                streak += 1
            else:
                break

        return streak

    @property
    def busiest_day_of_week(self) -> str:
        """Day of week with most activity."""
        if not self.daily_activity:
            return "N/A"

        day_counts: dict[int, int] = {}
        for d in self.daily_activity:
            weekday = d.date.weekday()
            day_counts[weekday] = day_counts.get(weekday, 0) + d.messages

        if not day_counts:
            return "N/A"

        busiest = max(day_counts.keys(), key=lambda k: day_counts[k])
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days[busiest]

    @property
    def weekend_vs_weekday_ratio(self) -> float:
        """Ratio of weekend to weekday activity."""
        if not self.daily_activity:
            return 0

        weekend = sum(d.messages for d in self.daily_activity if d.date.weekday() >= 5)
        weekday = sum(d.messages for d in self.daily_activity if d.date.weekday() < 5)

        if not weekday:
            return 0
        return weekend / weekday

    @property
    def model_switching_frequency(self) -> float:
        """Percentage of days with multi-model usage."""
        if not self.daily_activity:
            return 0

        multi_model_days = sum(1 for d in self.daily_activity if len(d.tokens_by_model) > 1)
        return (multi_model_days / len(self.daily_activity)) * 100

    @property
    def tokens_by_type(self) -> dict[str, int]:
        """Token breakdown by type for visualization."""
        return {
            "Input": self.total_input_tokens,
            "Output": self.total_output_tokens,
            "Cache Read": self.total_cache_read_tokens,
            "Cache Write": self.total_cache_write_tokens,
        }

    @property
    def week_over_week_change(self) -> float:
        """Percentage change in messages this week vs last week."""
        if len(self.daily_activity) < 14:
            return 0

        this_week = sum(d.messages for d in self.daily_activity[-7:])
        last_week = sum(d.messages for d in self.daily_activity[-14:-7])

        if not last_week:
            return 0
        return ((this_week - last_week) / last_week) * 100

    @property
    def productivity_score(self) -> int:
        """A composite productivity score 0-100 based on various metrics."""
        # Weighted score based on:
        # - Active days consistency
        # - Cache efficiency
        # - Messages per session
        # - Current streak

        score = 0

        # Active days ratio (max 30 points)
        if self.days_since_start > 0:
            active_ratio = min(self.active_days / self.days_since_start, 1.0)
            score += int(active_ratio * 30)

        # Cache efficiency (max 25 points)
        score += int(min(self.cache_efficiency, 100) / 4)

        # Messages per session efficiency (max 25 points) - optimal ~50 msgs/session
        mps = min(self.avg_messages_per_session / 50, 1.0)
        score += int(mps * 25)

        # Current streak bonus (max 20 points)
        score += min(self.current_streak * 2, 20)

        return min(score, 100)

    @property
    def usage_trend(self) -> str:
        """Compare recent usage to average."""
        if len(self.daily_activity) < 7:
            return "insufficient_data"
        recent = self.daily_activity[-7:]
        older = self.daily_activity[:-7]
        if not older:
            return "insufficient_data"

        recent_avg = sum(d.messages for d in recent) / len(recent)
        older_avg = sum(d.messages for d in older) / len(older)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        return "stable"

    # ===== Time-Based Statistics =====

    @property
    def peak_hour(self) -> int | None:
        if not self.hour_counts:
            return None
        return max(self.hour_counts.keys(), key=lambda h: self.hour_counts[h])

    @property
    def activity_by_time_of_day(self) -> dict[str, int]:
        """Aggregate sessions by time of day."""
        morning = sum(self.hour_counts.get(h, 0) for h in range(6, 12))  # 6am-12pm
        afternoon = sum(self.hour_counts.get(h, 0) for h in range(12, 18))  # 12pm-6pm
        evening = sum(self.hour_counts.get(h, 0) for h in range(18, 22))  # 6pm-10pm
        night = sum(self.hour_counts.get(h, 0) for h in list(range(22, 24)) + list(range(0, 6)))  # 10pm-6am
        return {"morning": morning, "afternoon": afternoon, "evening": evening, "night": night}

    @property
    def days_since_start(self) -> int:
        if not self.first_session_date:
            return 0
        return (date.today() - self.first_session_date).days

    # ===== Data Retrieval Methods =====

    def get_recent_activity(self, days: int = 14) -> list[DailyActivity]:
        """Get the most recent N days of activity."""
        return self.daily_activity[-days:]

    def get_messages_series(self, days: int = 30) -> tuple[list[str], list[int]]:
        """Get date labels and message counts for charting."""
        recent = self.get_recent_activity(days)
        dates = [d.date.strftime("%m/%d") for d in recent]
        messages = [d.messages for d in recent]
        return dates, messages

    def get_sessions_series(self, days: int = 30) -> tuple[list[str], list[int]]:
        """Get date labels and session counts for charting."""
        recent = self.get_recent_activity(days)
        dates = [d.date.strftime("%m/%d") for d in recent]
        sessions = [d.sessions for d in recent]
        return dates, sessions

    def get_tokens_series(self, days: int = 30) -> tuple[list[str], list[int]]:
        """Get date labels and token counts for charting."""
        recent = self.get_recent_activity(days)
        dates = [d.date.strftime("%m/%d") for d in recent]
        tokens = [d.total_tokens for d in recent]
        return dates, tokens

    def get_hour_series(self) -> tuple[list[int], list[int]]:
        """Get hour labels and counts for charting."""
        hours = list(range(24))
        counts = [self.hour_counts.get(h, 0) for h in hours]
        return hours, counts

    def get_hourly_messages(self) -> tuple[list[str], list[int]]:
        """Get hourly message distribution for Today view (24 data points)."""
        hours = [f"{h:02d}:00" for h in range(24)]
        total_sessions = sum(self.hour_counts.values()) or 1

        # Use today's data if available, otherwise use most recent day
        activity = self.today_activity or self.latest_activity
        today_msgs = activity.messages if activity else 0

        # Distribute messages proportionally by session distribution
        counts = []
        for h in range(24):
            session_ratio = self.hour_counts.get(h, 0) / total_sessions
            counts.append(int(today_msgs * session_ratio))
        return hours, counts

    def get_hourly_tokens(self) -> tuple[list[str], list[int]]:
        """Get hourly token distribution for Today view (24 data points)."""
        hours = [f"{h:02d}:00" for h in range(24)]
        total_sessions = sum(self.hour_counts.values()) or 1

        # Use today's data if available, otherwise use most recent day
        activity = self.today_activity or self.latest_activity
        today_tokens = activity.total_tokens if activity else 0

        # Distribute tokens proportionally by session distribution
        counts = []
        for h in range(24):
            session_ratio = self.hour_counts.get(h, 0) / total_sessions
            counts.append(int(today_tokens * session_ratio))
        return hours, counts

    def get_hourly_tools(self) -> tuple[list[str], list[int]]:
        """Get hourly tool calls distribution for Today view (24 data points)."""
        hours = [f"{h:02d}:00" for h in range(24)]
        total_sessions = sum(self.hour_counts.values()) or 1

        # Use today's data if available, otherwise use most recent day
        activity = self.today_activity or self.latest_activity
        today_tools = activity.tool_calls if activity else 0

        # Distribute tool calls proportionally by session distribution
        counts = []
        for h in range(24):
            session_ratio = self.hour_counts.get(h, 0) / total_sessions
            counts.append(int(today_tools * session_ratio))
        return hours, counts

    def get_hourly_cost(self) -> tuple[list[str], list[float]]:
        """Get hourly cost distribution for Today view (24 data points)."""
        hours = [f"{h:02d}:00" for h in range(24)]
        total_sessions = sum(self.hour_counts.values()) or 1

        # Estimate today's cost from total
        if self.active_days > 0:
            today_cost = self.total_cost / self.active_days
        else:
            today_cost = 0.0

        costs: list[float] = []
        cumulative = 0.0
        for h in range(24):
            session_ratio = self.hour_counts.get(h, 0) / total_sessions
            cumulative += today_cost * session_ratio
            costs.append(cumulative)
        return hours, costs

    def get_hourly_sessions(self) -> tuple[list[str], list[int]]:
        """Get hourly session counts for Today view (24 data points)."""
        hours = [f"{h:02d}:00" for h in range(24)]
        total_sessions = sum(self.hour_counts.values()) or 1

        # Use today's data if available, otherwise use most recent day
        activity = self.today_activity or self.latest_activity
        today_sessions = activity.sessions if activity else 0

        # Scale hourly pattern to today's session count
        counts = []
        for h in range(24):
            session_ratio = self.hour_counts.get(h, 0) / total_sessions
            counts.append(int(today_sessions * session_ratio))
        return hours, counts

    def get_model_distribution(self) -> dict[str, int]:
        """Get token distribution by model for pie chart."""
        return {m.display_name: m.output_tokens for m in self.model_usage.values()}

    def get_tools_series(self, days: int = 30) -> tuple[list[str], list[int]]:
        """Get date labels and tool call counts for charting."""
        recent = self.get_recent_activity(days)
        dates = [d.date.strftime("%m/%d") for d in recent]
        tools = [d.tool_calls for d in recent]
        return dates, tools

    def get_day_of_week_distribution(self) -> tuple[list[str], list[int]]:
        """Get activity distribution by day of week."""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        counts = [0] * 7
        for d in self.daily_activity:
            counts[d.date.weekday()] += d.messages
        return days, counts

    def get_session_duration_distribution(self) -> list[float]:
        """Get estimated session durations for histogram."""
        # Estimate based on messages per session ratio
        if not self.total_sessions or not self.longest_session:
            return []

        avg_duration = self.longest_session.duration_ms / 2  # rough estimate
        # Generate estimated durations
        durations = []
        for activity in self.daily_activity[-30:]:
            if activity.sessions > 0:
                est_duration = (activity.messages / self.avg_messages_per_session) * avg_duration
                for _ in range(activity.sessions):
                    durations.append(est_duration / 60000)  # convert to minutes
        return durations

    def get_cost_series(self, days: int = 21) -> tuple[list[str], list[float]]:
        """Get daily cost estimates for charting."""
        recent = self.get_recent_activity(days)
        dates = [d.date.strftime("%m/%d") for d in recent]
        # Estimate daily cost based on token distribution
        total_tokens = sum(d.total_tokens for d in recent)
        costs = []
        for d in recent:
            if total_tokens > 0:
                ratio = d.total_tokens / total_tokens if total_tokens else 0
                costs.append(self.total_cost * ratio * (len(recent) / self.active_days))
            else:
                costs.append(0)
        return dates, costs

    def get_hourly_heatmap_data(self) -> list[list[int]]:
        """Get 7x24 heatmap data for day-of-week vs hour activity."""
        # Initialize 7 days x 24 hours matrix
        heatmap = [[0] * 24 for _ in range(7)]

        # We only have aggregate hour data, so distribute it
        for hour, count in self.hour_counts.items():
            # Distribute evenly across days of week
            per_day = count // 7
            for day in range(7):
                heatmap[day][hour] = per_day

        return heatmap

    def get_cumulative_cost(self, days: int = 30) -> tuple[list[str], list[float]]:
        """Get cumulative cost over time."""
        dates, daily_costs = self.get_cost_series(days)
        cumulative: list[float] = []
        total = 0.0
        for cost in daily_costs:
            total += cost
            cumulative.append(total)
        return dates, cumulative

    def get_efficiency_metrics(self) -> dict[str, float]:
        """Get efficiency-related metrics for display."""
        return {
            "tokens_per_msg": self.avg_tokens_per_message,
            "msgs_per_session": self.avg_messages_per_session,
            "cost_per_session": self.avg_cost_per_session,
            "tools_per_session": self.avg_tools_per_session,
            "cache_hit_rate": self.cache_hit_rate,
            "cost_saved_pct": self.cost_saved_percentage,
        }

    def get_streak_data(self) -> dict[str, int]:
        """Get streak-related statistics."""
        return {
            "current": self.current_streak,
            "longest": self.longest_streak,
            "active_days": self.active_days,
            "total_days": self.days_since_start,
        }

    def get_comparison_data(self) -> dict[str, Any]:
        """Get comparison statistics."""
        return {
            "wow_change": self.week_over_week_change,
            "trend": self.usage_trend,
            "productivity": self.productivity_score,
        }

    # ===== Filtering Methods =====

    def filter_by_range(self, time_range: TimeRange) -> "ClaudeStats":
        """Create a new ClaudeStats filtered to the specified time range."""
        cutoff = date.today() - timedelta(days=time_range.days)

        # Filter daily activity
        filtered_activity = [d for d in self.daily_activity if d.date >= cutoff]

        # Calculate filtered totals
        filtered_messages = sum(d.messages for d in filtered_activity)
        filtered_sessions = sum(d.sessions for d in filtered_activity)

        # For model usage, we need to estimate based on the time proportion
        # Since we don't have per-day model breakdown, we'll scale proportionally
        if self.active_days > 0:
            ratio = len(filtered_activity) / self.active_days
        else:
            ratio = 0

        filtered_model_usage = {}
        for model_id, usage in self.model_usage.items():
            filtered_model_usage[model_id] = ModelUsage(
                model_id=model_id,
                input_tokens=int(usage.input_tokens * ratio),
                output_tokens=int(usage.output_tokens * ratio),
                cache_read_tokens=int(usage.cache_read_tokens * ratio),
                cache_creation_tokens=int(usage.cache_creation_tokens * ratio),
            )

        # Keep hour counts unscaled - they represent the session pattern,
        # not absolute counts. Used by hourly distribution methods.
        filtered_hours = self.hour_counts.copy()

        return ClaudeStats(
            total_sessions=filtered_sessions,
            total_messages=filtered_messages,
            first_session_date=self.first_session_date,
            last_computed_date=self.last_computed_date,
            daily_activity=filtered_activity,
            model_usage=filtered_model_usage,
            longest_session=self.longest_session,
            hour_counts=filtered_hours,
            raw_data=self.raw_data,
        )

    # ===== Loading Methods =====

    @classmethod
    def from_file(cls, path: Path | None = None) -> ClaudeStats:
        """Load stats from the Claude Code cache file."""
        if path is None:
            path = Path.home() / ".claude" / "stats-cache.json"

        if not path.exists():
            raise FileNotFoundError(f"Stats file not found: {path}")

        with open(path) as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaudeStats:
        """Parse stats from a dictionary."""
        # Build token lookup by date
        token_by_date: dict[str, dict[str, int]] = {}
        for entry in data.get("dailyModelTokens", []):
            token_by_date[entry["date"]] = entry.get("tokensByModel", {})

        # Parse daily activity with tokens
        daily_activity = []
        for d in data.get("dailyActivity", []):
            date_str = d["date"]
            tokens = token_by_date.get(date_str, {})
            daily_activity.append(DailyActivity.from_dict(d, tokens))

        # Parse model usage
        model_usage = {}
        for model_id, usage in data.get("modelUsage", {}).items():
            model_usage[model_id] = ModelUsage(
                model_id=model_id,
                input_tokens=usage.get("inputTokens", 0),
                output_tokens=usage.get("outputTokens", 0),
                cache_read_tokens=usage.get("cacheReadInputTokens", 0),
                cache_creation_tokens=usage.get("cacheCreationInputTokens", 0),
            )

        # Parse dates
        first_session = None
        if first_str := data.get("firstSessionDate"):
            first_session = datetime.fromisoformat(first_str.replace("Z", "+00:00")).date()

        last_computed = None
        if last_str := data.get("lastComputedDate"):
            last_computed = datetime.strptime(last_str, "%Y-%m-%d").date()

        # Parse hour counts
        hour_counts = {int(k): v for k, v in data.get("hourCounts", {}).items()}

        return cls(
            total_sessions=data.get("totalSessions", 0),
            total_messages=data.get("totalMessages", 0),
            first_session_date=first_session,
            last_computed_date=last_computed,
            daily_activity=daily_activity,
            model_usage=model_usage,
            longest_session=LongestSession.from_dict(data.get("longestSession", {})),
            hour_counts=hour_counts,
            raw_data=data,
        )
