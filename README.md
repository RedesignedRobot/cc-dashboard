# Claude Scripts

Personal utility scripts for Claude Code.

## claude-stats

Real-time terminal dashboard for Claude Code usage statistics.

### Installation

```bash
# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$PATH:$HOME/Documents/Code/ClaudeScripts"
```

### Usage

```bash
claude-stats              # Run live dashboard (1s refresh)
CLAUDE_STATS_REFRESH=5 claude-stats   # Custom refresh rate
```

### Features

- Live auto-refreshing display
- Daily message/session/tool charts
- Model usage breakdown (Opus, Sonnet, Haiku)
- Activity by hour visualization
- Today's stats with progress bars
- Color-coded intensity indicators
