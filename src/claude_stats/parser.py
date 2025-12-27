"""Parse Claude Code stats from the cache file."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Any


@dataclass
class DailyActivity:
    """Activity for a single day."""
    date: date
    messages: int
    sessions: int
    tool_calls: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DailyActivity:
        return cls(
            date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            messages=data.get("messageCount", 0),
            sessions=data.get("sessionCount", 0),
            tool_calls=data.get("toolCallCount", 0),
        )


@dataclass
class ModelUsage:
    """Usage statistics for a specific model."""
    name: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def display_name(self) -> str:
        """Human-friendly model name."""
        name_map = {
            "claude-opus-4-5-20251101": "Opus 4.5",
            "claude-sonnet-4-5-20250929": "Sonnet 4.5",
            "claude-haiku-4-5-20251001": "Haiku 4.5",
            "claude-opus-4-1-20250805": "Opus 4.1",
        }
        return name_map.get(self.name, self.name)


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
    """Complete Claude Code statistics."""
    total_sessions: int
    total_messages: int
    first_session_date: date | None
    last_computed_date: date | None
    daily_activity: list[DailyActivity]
    model_usage: dict[str, ModelUsage]
    longest_session: LongestSession | None
    hour_counts: dict[int, int]

    @property
    def total_tool_calls(self) -> int:
        return sum(d.tool_calls for d in self.daily_activity)

    @property
    def peak_day(self) -> DailyActivity | None:
        if not self.daily_activity:
            return None
        return max(self.daily_activity, key=lambda d: d.messages)

    @property
    def today_activity(self) -> DailyActivity | None:
        today = date.today()
        for activity in self.daily_activity:
            if activity.date == today:
                return activity
        return None

    @property
    def total_output_tokens(self) -> int:
        return sum(m.output_tokens for m in self.model_usage.values())

    @property
    def total_cache_reads(self) -> int:
        return sum(m.cache_read_tokens for m in self.model_usage.values())

    @property
    def active_days(self) -> int:
        return len(self.daily_activity)

    @property
    def avg_messages_per_day(self) -> float:
        if not self.active_days:
            return 0
        return self.total_messages / self.active_days

    def get_recent_activity(self, days: int = 14) -> list[DailyActivity]:
        """Get the most recent N days of activity."""
        return self.daily_activity[-days:]

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
        # Parse daily activity
        daily_activity = [
            DailyActivity.from_dict(d) for d in data.get("dailyActivity", [])
        ]

        # Parse model usage
        model_usage = {}
        for model_id, usage in data.get("modelUsage", {}).items():
            model_usage[model_id] = ModelUsage(
                name=model_id,
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
        )
