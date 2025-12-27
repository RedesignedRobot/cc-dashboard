# Changelog

All notable changes to CC Dashboard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-27

### Added
- 🎨 **Apple-inspired UI redesign**: Minimalist, sophisticated dashboard aesthetic
- 🔄 **Auto-update**: Checks GitHub for new versions, press `u` to update
- 💰 **Cache toggle**: Press `c` to switch between "With Cache" and "No Cache" cost views
- 📅 **All Time view**: Press `5` for full year (365 days) statistics
- ✅ **Startup checks**: Validates Claude Code installation and stats file on launch
- 🔍 **--check flag**: Run `ccd --check` to diagnose setup issues

### Changed
- Complete UI overhaul with generous whitespace and clean typography
- Token display now always shows units (e.g., "1.6B tokens" not "1.6B")
- Simplified Key Metrics panel: removed streaks, kept essential stats
- Cleaner header with spaced layout
- Charts update in real-time when toggling cache mode

### Fixed
- Cache mode toggle now correctly syncs across all panels and charts
- Consistent semantics: "No Cache" = hypothetical full cost, "With Cache" = actual cost

## [1.2.0] - 2025-12-27

### Added
- ⏱️ **Time range filtering**: View stats for Today, This Week, This Month, or Last 3 Months
- 🔢 **Quick range switching**: Press 1-4 to instantly switch time ranges
- 📊 **Dynamic chart titles**: Chart titles update to reflect selected time range
- 📍 **Range indicator in header**: Always see which time period you're viewing

### Changed
- All panels and charts now filter data based on selected time range
- Footer shows available key bindings including range keys

## [1.1.0] - 2025-12-27

### Added
- 📊 **8 diverse chart types**: Messages, Tokens, Cost, Tools (line charts), Hourly, Day of Week, Sessions, Model Distribution (bar charts)
- 📈 **20+ new statistics**: Avg tokens/message, cost/session, cache efficiency, streaks, productivity score
- 🎯 **Productivity score**: Composite 0-100 score based on usage patterns and efficiency
- 📅 **Streak tracking**: Current and longest consecutive usage days
- 🔥 **Day of week analysis**: Find your busiest coding days
- 💰 **Cost breakdown**: Per-model cost visualization with horizontal bars
- 📊 **Token breakdown**: Visual split of input, output, and cached tokens
- 🔄 **Week-over-week comparison**: Track usage trend changes

### Changed
- Complete UI redesign with infographic-style layout
- Added 4 stat panels at top: Stats, Token Breakdown, Model Costs, Productivity
- Two rows of 4 charts each (8 charts total)
- Line charts use braille markers for smoother visualization
- Progress bars for visual metrics (productivity score, cache efficiency)

## [1.0.0] - 2025-12-27

### Added
- 🎉 Initial public release as "CC Dashboard"
- Real-time terminal dashboard with auto-refresh
- Cost tracking using Anthropic's actual pricing
- 4 beautiful themes: Dark, Midnight, Matrix, Dracula
- Live theme switching with `t` key
- Daily message and token charts (21-day view)
- Hourly activity patterns
- Cost breakdown by model
- Cache savings visualization
- Helpful CLI with `--help` and `--version`
- Clear error messages when stats file is missing

### Technical
- Built with Textual TUI framework
- Uses textual-plotext for terminal charts
- Supports Python 3.10+
- Reads from `~/.claude/stats-cache.json`

## [0.2.0] - 2025-12-26

### Changed
- Rewrote from Rich + Typer to Textual framework
- Added visual charts and graphs
- Improved cost calculations

## [0.1.0] - 2025-12-26

### Added
- Initial bash script version
- Basic terminal colorization
- Auto-refresh capability
