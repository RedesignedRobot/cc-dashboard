# Claude Stats

Real-time terminal dashboard for Claude Code usage statistics.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Live Dashboard** - Auto-refreshing terminal UI with colorized stats
- **Multiple Views** - Summary, models, activity, hourly distribution
- **Export** - Export data to JSON or CSV
- **Subcommands** - Focused views for specific metrics

## Installation

```bash
# Install from source
pip install -e .

# Or with pipx for isolated install
pipx install .
```

## Usage

### Live Dashboard

```bash
# Quick view (single render)
claude-stats

# Live auto-refresh mode
claude-stats --watch
claude-stats -w

# Custom refresh rate (default: 1 second)
claude-stats -w --refresh 2
```

### Subcommands

```bash
# Compact summary table
claude-stats summary

# Model usage breakdown
claude-stats models

# Daily activity (default: 14 days)
claude-stats activity
claude-stats activity --days 30

# Today's stats only
claude-stats today

# Hourly distribution
claude-stats hours

# Export data
claude-stats export data.json --days 30
claude-stats export data.csv --days 7
```

### Options

```
--watch, -w       Live dashboard with auto-refresh
--refresh, -r     Refresh interval in seconds (default: 1.0)
--file, -f        Custom path to stats-cache.json
```

## What It Shows

- **Sessions** - Total coding sessions with Claude
- **Messages** - Total message exchanges
- **Tool Calls** - How often Claude used tools (file edits, commands, etc.)
- **Model Usage** - Breakdown by model (Opus, Sonnet, Haiku) with token counts
- **Activity Charts** - Daily message volume with color-coded intensity
- **Hour Distribution** - When you're most active during the day
- **Peak Day** - Your most productive day
- **Longest Session** - Duration and message count

## Requirements

- Python 3.10+
- Claude Code installed (`~/.claude/stats-cache.json` must exist)

## License

MIT
