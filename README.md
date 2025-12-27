# Claude Stats

**Mission Control Dashboard** for Claude Code usage statistics.

A beautiful, real-time terminal dashboard that shows you everything about your Claude Code usage - messages, costs, tokens, trends, and more.

## Features

- **Live Dashboard** - Auto-refreshing TUI with charts and graphs
- **Cost Tracking** - Real USD cost calculations using Anthropic pricing
- **Token Analytics** - Input, output, cache read/write breakdowns
- **Visual Charts** - Daily message trends, token usage, model distribution
- **Activity Insights** - Hourly patterns, peak usage, session analysis
- **Cache Savings** - See how much you're saving with prompt caching

## Installation

```bash
# Using pipx (recommended)
pipx install .

# Or using pip
pip install .
```

## Usage

Just run:

```bash
claude-stats
```

That's it! The dashboard will launch and auto-refresh every 5 seconds.

### Keyboard Shortcuts

- `r` - Force refresh
- `q` - Quit

## What You'll See

### Summary Bar
- Total messages, sessions, tool calls
- Total cost in USD
- Total tokens processed
- Cache savings

### Panels
- **Cost Breakdown** - Total cost, daily average, cost by model, cache savings
- **Token Usage** - Input/output tokens, cache stats, per-model breakdown
- **Activity** - Today's stats (or latest day), peak day, usage trend
- **Sessions** - Total sessions, longest session, active days
- **Hourly Activity** - When you code most, time-of-day distribution

### Charts
- **Daily Messages** - Bar chart of last 21 days
- **Daily Tokens** - Token usage trend
- **Model Distribution** - Output tokens by model

## Pricing

Cost calculations use current Anthropic pricing (December 2025):

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| Opus 4.5 | $5.00 | $25.00 |
| Sonnet 4.5 | $3.00 | $15.00 |
| Haiku 4.5 | $0.80 | $4.00 |

Cache reads are 10% of input price. Cache writes are 125% of input price.

## Requirements

- Python 3.10+
- Claude Code installed with usage history (`~/.claude/stats-cache.json`)
- Terminal with Unicode support (most modern terminals)

## License

MIT
