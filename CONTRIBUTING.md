# Contributing to CC Dashboard

Thanks for your interest in contributing! We welcome contributions of all kinds.

## 🚀 Quick Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/cc-dashboard.git
cd cc-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install in dev mode
pip install -e ".[dev]"

# 4. Run the app
ccd
```

## 📁 Project Structure

```
cc-dashboard/
├── src/cc_dashboard/
│   ├── __init__.py      # Version info
│   ├── app.py           # Main Textual app
│   ├── parser.py        # Stats parsing & cost calculations
│   └── themes.py        # Theme definitions
├── pyproject.toml       # Package configuration
├── LICENSE              # MIT License
└── README.md
```

## 🎨 Adding Themes

Themes are the easiest way to contribute! Edit `src/cc_dashboard/themes.py`:

```python
from textual.theme import Theme

MY_THEME = Theme(
    name="stats-mytheme",
    primary="#YOUR_COLOR",
    secondary="#YOUR_COLOR",
    accent="#YOUR_COLOR",
    foreground="#YOUR_COLOR",
    background="#YOUR_COLOR",
    success="#YOUR_COLOR",
    warning="#YOUR_COLOR",
    error="#YOUR_COLOR",
    surface="#YOUR_COLOR",
    panel="#YOUR_COLOR",
    dark=True,  # or False for light themes
)

# Add to THEMES dict
THEMES["stats-mytheme"] = MY_THEME

# Add display name
THEME_DISPLAY_NAMES["stats-mytheme"] = "My Theme"
```

## 📝 Code Style

- Use type hints
- Follow PEP 8
- Keep functions focused
- Add docstrings for public functions

## 🐛 Bug Reports

When reporting bugs, please include:
- Python version (`python --version`)
- OS and terminal emulator
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## 💡 Feature Ideas

Before starting on a large feature, open an issue to discuss it first. Great contributions we'd love:

- **New visualizations** — Weekly trends, comparisons
- **Export functionality** — CSV, JSON, HTML reports
- **Date filtering** — View specific time ranges
- **More themes** — Light themes, custom color schemes

## 🔄 Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test locally with `ccd`
4. Commit with clear messages
5. Push and open a PR

### PR Guidelines

- Keep PRs focused on one change
- Update docs if needed
- Add yourself to contributors!

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Questions? Open an issue or reach out to the maintainers.
