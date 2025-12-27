# Changelog

All notable changes to CC Dashboard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
