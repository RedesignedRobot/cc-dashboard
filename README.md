<div align="center">

# ⚡ CC Dashboard

### Mission Control for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-cc--dashboard-blue)](https://pypi.org/project/cc-dashboard/)

**A beautiful, real-time terminal dashboard for your Claude Code sessions.**

Track your AI coding costs, token usage, and productivity — all in one gorgeous TUI.

[Installation](#-quick-start) • [Features](#-features) • [Themes](#-themes) • [Contributing](#-contributing)

---

</div>

## 🚀 Quick Start

```bash
# Install with pipx (recommended)
pipx install cc-dashboard

# Or with pip
pip install cc-dashboard

# Launch the dashboard
ccd
```

That's it. One command, instant insights.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💰 **Cost Tracking** | Real USD costs using Anthropic's actual pricing |
| 📊 **Live Charts** | Daily messages, tokens, hourly patterns, model breakdown |
| 🎨 **4 Themes** | Dark, Midnight, Matrix, Dracula — press `t` to switch |
| 💾 **Cache Insights** | See how much you're saving with prompt caching |
| 🔄 **Auto-refresh** | Updates every 5 seconds, or press `r` to refresh |
| ⚡ **Instant Launch** | Opens in under a second |

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `t` | Cycle through themes |
| `r` | Force refresh |
| `q` | Quit |

## 🎨 Themes

Press `t` to cycle through themes in real-time:

- **Dark** — Pitch black OLED-friendly
- **Midnight** — Deep blue, GitHub-inspired
- **Matrix** — Classic green on black
- **Dracula** — Purple hacker vibes

## 💰 Cost Calculations

Uses current Anthropic API pricing (December 2025):

| Model | Input | Output |
|-------|-------|--------|
| Claude Opus 4.5 | $5.00/M | $25.00/M |
| Claude Opus 4.1 | $15.00/M | $75.00/M |
| Claude Sonnet 4.5 | $3.00/M | $15.00/M |
| Claude Haiku 4.5 | $0.80/M | $4.00/M |

Cache reads are 10% of input price. Cache writes are 125% of input price.

## 📋 Requirements

- **Python 3.10+**
- **Claude Code** installed with usage data (`~/.claude/stats-cache.json`)
- A terminal with Unicode support

Don't have Claude Code? Get it at [claude.ai/claude-code](https://claude.ai/claude-code)

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/RedesignedRobot/cc-dashboard.git
cd cc-dashboard

# Install in dev mode
pip install -e ".[dev]"

# Run locally
ccd
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ideas we'd love:**
- New themes
- Additional charts/visualizations
- Export to CSV/HTML
- Date range filtering
- Week-over-week comparisons

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the Claude Code community**

[Textual](https://textual.textualize.io/) • [Rich](https://rich.readthedocs.io/) • [Plotext](https://github.com/piccolomo/plotext)

</div>
