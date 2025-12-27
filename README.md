<div align="center">

# CC Dashboard

### Mission Control for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-cc--dashboard-blue)](https://pypi.org/project/cc-dashboard/)

**A beautiful, real-time terminal dashboard for your Claude Code sessions.**

Track your AI coding costs, token usage, and productivity — all in one minimal, Apple-inspired TUI.

[Installation](#-quick-start) • [Features](#-features) • [Keyboard Shortcuts](#%EF%B8%8F-keyboard-shortcuts) • [Contributing](#-contributing)

---

</div>

## Quick Start

```bash
# Install with pipx (recommended)
pipx install cc-dashboard

# Or with pip
pip install cc-dashboard

# Launch the dashboard
ccd
```

That's it. One command, instant insights.

## Features

| Feature | Description |
|---------|-------------|
| **Cost Tracking** | Real USD costs using Anthropic's actual pricing |
| **Cache Toggle** | Switch between "With Cache" and "No Cache" views to see actual vs hypothetical costs |
| **Live Charts** | 8 beautiful charts: messages, tokens, cost, tools, hourly, daily, sessions, models |
| **Time Ranges** | Today, This Week, This Month, 3 Months, or All Time |
| **Auto-update** | Automatically checks GitHub for new versions |
| **4 Themes** | Dark, Midnight, Matrix, Dracula |
| **Startup Checks** | Validates your Claude Code setup on launch |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1-5` | Switch time range (Today/Week/Month/Quarter/All) |
| `c` | Toggle cache mode (With Cache / No Cache) |
| `t` | Cycle through themes |
| `u` | Update to latest version |
| `r` | Force refresh |
| `q` | Quit |

## Cache Mode

Press `c` to toggle between two views:

- **No Cache** (default): Shows what your usage would cost without caching — the hypothetical full price
- **With Cache**: Shows your actual billed cost with cache discounts applied

This helps you understand how much caching saves you.

## Themes

Press `t` to cycle through themes:

- **Dark** — Clean OLED-friendly black
- **Midnight** — Deep blue, GitHub-inspired
- **Matrix** — Classic green on black
- **Dracula** — Purple hacker vibes

## Cost Calculations

Uses current Anthropic API pricing (December 2025):

| Model | Input | Output |
|-------|-------|--------|
| Claude Opus 4.5 | $5.00/M | $25.00/M |
| Claude Opus 4.1 | $15.00/M | $75.00/M |
| Claude Sonnet 4.5 | $3.00/M | $15.00/M |
| Claude Haiku 4.5 | $0.80/M | $4.00/M |

Cache reads are 10% of input price. Cache writes are 125% of input price.

## Diagnostics

Run startup checks to verify your setup:

```bash
ccd --check
```

This validates:
- Claude Code directory exists
- Stats file is present and valid
- Required data fields are available

## Requirements

- **Python 3.10+**
- **Claude Code** installed with usage data (`~/.claude/stats-cache.json`)
- A terminal with Unicode support

Don't have Claude Code? Get it at [claude.ai/claude-code](https://claude.ai/claude-code)

## Development

```bash
# Clone the repo
git clone https://github.com/RedesignedRobot/cc-dashboard.git
cd cc-dashboard

# Install in dev mode
pip install -e ".[dev]"

# Run locally
ccd
```

## Contributing

Contributions are welcome!

**Ideas we'd love:**
- New themes
- Additional visualizations
- Export to CSV/HTML

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with care for the Claude Code community**

[Textual](https://textual.textualize.io/) • [Rich](https://rich.readthedocs.io/) • [Plotext](https://github.com/piccolomo/plotext)

</div>
