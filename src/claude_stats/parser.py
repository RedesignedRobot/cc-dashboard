"""Parse Claude Code stats with comprehensive cost calculations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any
from enum import Enum


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

    def get_model_distribution(self) -> dict[str, int]:
        """Get token distribution by model for pie chart."""
        return {m.display_name: m.output_tokens for m in self.model_usage.values()}

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
