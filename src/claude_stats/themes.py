"""Theme definitions for Claude Stats."""

from textual.theme import Theme

# Custom themes using Textual's Theme system
DARK_THEME = Theme(
    name="stats-dark",
    primary="#00d4ff",
    secondary="#4ecdc4",
    accent="#ff6b6b",
    foreground="#ffffff",
    background="#000000",
    success="#00ff00",
    warning="#ffe66d",
    error="#ff6b6b",
    surface="#0a0a0a",
    panel="#1a1a2e",
    dark=True,
)

MIDNIGHT_THEME = Theme(
    name="stats-midnight",
    primary="#58a6ff",
    secondary="#8b949e",
    accent="#f78166",
    foreground="#c9d1d9",
    background="#0d1117",
    success="#3fb950",
    warning="#d29922",
    error="#f85149",
    surface="#161b22",
    panel="#21262d",
    dark=True,
)

MATRIX_THEME = Theme(
    name="stats-matrix",
    primary="#00ff00",
    secondary="#00dd00",
    accent="#00bb00",
    foreground="#00ff00",
    background="#000000",
    success="#00ff00",
    warning="#00dd00",
    error="#00aa00",
    surface="#000800",
    panel="#001100",
    dark=True,
)

DRACULA_THEME = Theme(
    name="stats-dracula",
    primary="#bd93f9",
    secondary="#ff79c6",
    accent="#8be9fd",
    foreground="#f8f8f2",
    background="#282a36",
    success="#50fa7b",
    warning="#ffb86c",
    error="#ff5555",
    surface="#21222c",
    panel="#44475a",
    dark=True,
)

# All available themes
THEMES = {
    "stats-dark": DARK_THEME,
    "stats-midnight": MIDNIGHT_THEME,
    "stats-matrix": MATRIX_THEME,
    "stats-dracula": DRACULA_THEME,
}

THEME_NAMES = list(THEMES.keys())

# Display names for notifications
THEME_DISPLAY_NAMES = {
    "stats-dark": "Dark",
    "stats-midnight": "Midnight",
    "stats-matrix": "Matrix",
    "stats-dracula": "Dracula",
}


def get_next_theme(current: str) -> str:
    """Get the next theme in rotation."""
    try:
        idx = THEME_NAMES.index(current)
        next_idx = (idx + 1) % len(THEME_NAMES)
        return THEME_NAMES[next_idx]
    except ValueError:
        return THEME_NAMES[0]
