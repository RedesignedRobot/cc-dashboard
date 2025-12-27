# Claude Stats

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Mission Control Dashboard** for [Claude Code](https://claude.ai/claude-code) usage statistics.

A beautiful, real-time terminal dashboard that shows you everything about your Claude Code usage - messages, costs, tokens, trends, and more.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Claude+Stats+Dashboard)

## Features

- 📊 **Live Dashboard** - Auto-refreshing TUI with charts and graphs
- 💰 **Cost Tracking** - Real USD cost calculations using Anthropic pricing
- 🎯 **Token Analytics** - Input, output, cache read/write breakdowns
- 📈 **Visual Charts** - Daily message trends, token usage, hourly patterns
- 🎨 **Themes** - Multiple themes including pitch-black for OLED terminals
- 💾 **Cache Insights** - See how much you're saving with prompt caching

## Installation

### Using pipx (Recommended)

```bash
pipx install git+https://github.com/RedesignedRobot/claude-scripts.git
```

### Using pip

```bash
pip install git+https://github.com/RedesignedRobot/claude-scripts.git
```

### From Source

```bash
git clone https://github.com/RedesignedRobot/claude-scripts.git
cd claude-scripts
pip install -e .
```

### Requirements

- Python 3.10 or higher
- Claude Code installed with usage history (`~/.claude/stats-cache.json`)
- Terminal with Unicode support

## Usage

Simply run:

```bash
claude-stats
```

The dashboard launches and auto-refreshes every 5 seconds.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `t` | Cycle through themes |
| `r` | Force refresh data |
| `q` | Quit |

### Themes

Press `t` to cycle through available themes:

- **dark** - Pitch black background (perfect for OLED)
- **midnight** - Deep blue tones (GitHub-inspired)
- **matrix** - Green on black
- **dracula** - Purple tones

## What You'll See

### Summary Bar
Key metrics at a glance: messages, tools, cost, tokens, cache savings, active days.

### Panels
- **Cost & Tokens** - Total cost, daily average, per-model breakdown, cache savings
- **Activity** - Latest day stats, peak day, longest session, usage trend

### Charts
- **Daily Messages** - Bar chart of message volume (21 days)
- **Daily Tokens** - Token usage trend
- **Cost by Model** - Which models are costing the most
- **Hourly Activity** - When you code most often

## Cost Calculations

Uses current Anthropic API pricing (December 2025):

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| Opus 4.5 | $5.00 | $25.00 |
| Opus 4.1 | $15.00 | $75.00 |
| Sonnet 4.5 | $3.00 | $15.00 |
| Haiku 4.5 | $0.80 | $4.00 |

Cache pricing:
- Cache reads: 10% of input price
- Cache writes: 125% of input price

## Configuration

### Custom Stats File

```bash
claude-stats /path/to/stats-cache.json
```

### Environment

The app reads from `~/.claude/stats-cache.json` by default. This file is created and maintained by Claude Code.

## Customization

### Adding Themes

Create your own themes in `src/claude_stats/themes.py`:

```python
MY_THEME = """
Screen {
    background: #your_color;
}
/* ... Textual CSS ... */
"""

THEMES["my_theme"] = MY_THEME
THEME_NAMES.append("my_theme")
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Ideas for contributions:
- New themes
- Additional charts/visualizations
- Export functionality (CSV, HTML reports)
- Date range filtering
- Week-over-week comparisons

## Dependencies

- [Textual](https://textual.textualize.io/) - TUI framework
- [textual-plotext](https://github.com/Textualize/textual-plotext/) - Terminal charts
- [Rich](https://rich.readthedocs.io/) - Rich text formatting
- [humanize](https://python-humanize.readthedocs.io/) - Human-readable formatting

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built for users of [Claude Code](https://claude.ai/claude-code)
- Powered by [Anthropic's Claude](https://www.anthropic.com/)
- TUI framework by [Textualize](https://www.textualize.io/)
