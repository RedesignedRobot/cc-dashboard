# Contributing to Claude Stats

Thanks for your interest in contributing! This project is open to contributions of all kinds.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-scripts.git
   cd claude-scripts
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development

### Project Structure

```
claude-scripts/
├── src/claude_stats/
│   ├── __init__.py      # Package version
│   ├── app.py           # Main Textual application
│   ├── parser.py        # Stats parsing and cost calculations
│   └── themes.py        # Theme definitions
├── pyproject.toml       # Package configuration
├── requirements.txt     # Dependencies
└── README.md
```

### Running Locally

```bash
# Run the app directly
python -m claude_stats.app

# Or if installed
claude-stats
```

### Code Style

- Use type hints where possible
- Follow PEP 8 conventions
- Keep functions focused and well-documented

## What to Contribute

### Good First Issues

- Add new themes
- Improve chart visualizations
- Add new statistics/metrics
- Documentation improvements

### Feature Ideas

- Export functionality (CSV, JSON, HTML reports)
- Historical comparisons (week-over-week, month-over-month)
- Custom date range filtering
- Integration with other Claude tools

### Bug Reports

When reporting bugs, please include:
- Your Python version (`python --version`)
- Your terminal emulator
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test locally: `claude-stats`
4. Commit with clear messages
5. Push and create a Pull Request

### PR Guidelines

- Keep PRs focused on a single change
- Update documentation if needed
- Add yourself to contributors if this is your first PR

## Adding Themes

Themes are defined in `src/claude_stats/themes.py`. To add a new theme:

1. Create a new CSS string following the existing pattern
2. Add it to the `THEMES` dictionary
3. Test with the `t` key to cycle through themes

Example:
```python
MY_THEME = """
Screen {
    background: #your_color;
}
/* ... more CSS ... */
"""

THEMES["my_theme"] = MY_THEME
```

## Questions?

Open an issue on GitHub or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
