"""Tests for handler and theme registry systems (Phase 2)

Validates the registry patterns for handlers and themes.
"""

import pytest
from app.handlers import (
    get_handler,
    register_handler,
    list_handlers,
    list_handlers_with_descriptions,
    GraphHandler,
)
from app.themes import (
    get_theme,
    register_theme,
    list_themes,
    list_themes_with_descriptions,
    Theme,
)


@pytest.fixture
def clean_handler_registry():
    """Fixture to save and restore handler registry state"""
    # Import the private registry
    from app import handlers

    # Save current state
    original_handlers = handlers._HANDLERS.copy()

    yield

    # Restore original state
    handlers._HANDLERS.clear()
    handlers._HANDLERS.update(original_handlers)


@pytest.fixture
def clean_theme_registry():
    """Fixture to save and restore theme registry state"""
    # Import the private registry
    from app import themes

    # Save current state
    original_themes = themes._THEMES.copy()

    yield

    # Restore original state
    themes._THEMES.clear()
    themes._THEMES.update(original_themes)


# Handler Registry Tests


def test_get_handler_line():
    """Test getting line handler from registry"""
    handler = get_handler("line")
    assert handler is not None
    assert "LineGraphHandler" in type(handler).__name__


def test_get_handler_scatter():
    """Test getting scatter handler from registry"""
    handler = get_handler("scatter")
    assert handler is not None
    assert "ScatterGraphHandler" in type(handler).__name__


def test_get_handler_bar():
    """Test getting bar handler from registry"""
    handler = get_handler("bar")
    assert handler is not None
    assert "BarGraphHandler" in type(handler).__name__


def test_get_handler_case_insensitive():
    """Test handler lookup is case insensitive"""
    handler_lower = get_handler("line")
    handler_upper = get_handler("LINE")
    handler_mixed = get_handler("Line")

    assert isinstance(handler_lower, type(handler_upper))
    assert isinstance(handler_lower, type(handler_mixed))


def test_get_handler_unknown():
    """Test getting unknown handler raises ValueError"""
    with pytest.raises(ValueError, match="Unknown handler 'unknown'"):
        get_handler("unknown")


def test_get_handler_error_message_shows_available():
    """Test error message lists available handlers"""
    with pytest.raises(ValueError, match="Available handlers:.*line.*scatter.*bar"):
        get_handler("invalid")


def test_list_handlers():
    """Test listing all available handlers"""
    handlers = list_handlers()
    assert isinstance(handlers, list)
    assert "line" in handlers
    assert "scatter" in handlers
    assert "bar" in handlers
    assert len(handlers) >= 3


def test_list_handlers_with_descriptions():
    """Test listing handlers with descriptions"""
    handlers = list_handlers_with_descriptions()
    assert isinstance(handlers, dict)
    assert "line" in handlers
    assert "scatter" in handlers
    assert "bar" in handlers

    # Check descriptions are non-empty strings
    for name, description in handlers.items():
        assert isinstance(description, str)
        assert len(description) > 0


def test_register_custom_handler(clean_handler_registry):
    """Test registering a custom handler"""
    from matplotlib.axes import Axes
    from app.graph_params import GraphParams

    class CustomHandler(GraphHandler):
        def plot(self, ax: Axes, data: GraphParams) -> None:
            pass

        def get_description(self) -> str:
            return "Custom test handler for registry testing"

    # Register custom handler
    custom = CustomHandler()
    register_handler("custom_test_handler", custom)

    # Verify it's registered
    assert "custom_test_handler" in list_handlers()
    handler = get_handler("custom_test_handler")
    assert isinstance(handler, CustomHandler)
    assert handler.get_description() == "Custom test handler for registry testing"


# Theme Registry Tests


def test_get_theme_light():
    """Test getting light theme from registry"""
    theme = get_theme("light")
    assert theme is not None
    assert "LightTheme" in type(theme).__name__


def test_get_theme_dark():
    """Test getting dark theme from registry"""
    theme = get_theme("dark")
    assert theme is not None
    assert "DarkTheme" in type(theme).__name__


def test_get_theme_bizlight():
    """Test getting bizlight theme from registry"""
    theme = get_theme("bizlight")
    assert theme is not None
    assert "BizLightTheme" in type(theme).__name__


def test_get_theme_bizdark():
    """Test getting bizdark theme from registry"""
    theme = get_theme("bizdark")
    assert theme is not None
    assert "BizDarkTheme" in type(theme).__name__


def test_get_theme_default():
    """Test getting theme with no name defaults to light"""
    theme = get_theme()
    assert theme is not None
    assert "LightTheme" in type(theme).__name__


def test_get_theme_case_insensitive():
    """Test theme lookup is case insensitive"""
    theme_lower = get_theme("dark")
    theme_upper = get_theme("DARK")
    theme_mixed = get_theme("Dark")

    assert isinstance(theme_lower, type(theme_upper))
    assert isinstance(theme_lower, type(theme_mixed))


def test_get_theme_unknown_fallback():
    """Test getting unknown theme falls back to light theme"""
    # Theme registry has a safety fallback to light theme
    theme = get_theme("unknown")
    assert theme is not None
    # Should fall back to light theme
    assert "LightTheme" in type(theme).__name__


def test_get_theme_invalid_fallback():
    """Test getting invalid theme falls back to light theme"""
    # Theme registry has a safety fallback to light theme
    theme = get_theme("invalid")
    assert theme is not None
    # Should fall back to light theme
    assert "LightTheme" in type(theme).__name__


def test_list_themes():
    """Test listing all available themes"""
    themes = list_themes()
    assert isinstance(themes, list)
    assert "light" in themes
    assert "dark" in themes
    assert "bizlight" in themes
    assert "bizdark" in themes
    assert len(themes) >= 4


def test_list_themes_with_descriptions():
    """Test listing themes with descriptions"""
    themes = list_themes_with_descriptions()
    assert isinstance(themes, dict)
    assert "light" in themes
    assert "dark" in themes
    assert "bizlight" in themes
    assert "bizdark" in themes

    # Check descriptions are non-empty strings
    for name, description in themes.items():
        assert isinstance(description, str)
        assert len(description) > 0


def test_register_custom_theme(clean_theme_registry):
    """Test registering a custom theme"""
    from matplotlib.figure import Figure
    from matplotlib.axes import Axes

    class CustomTheme(Theme):
        def apply(self, fig: Figure, ax: Axes) -> None:
            pass

        def get_default_color(self) -> str:
            return "#FF0000"

        def get_colors(self) -> list[str]:
            return ["#FF0000", "#00FF00", "#0000FF"]

        def get_config(self) -> dict:
            return {"name": "custom"}

        def get_description(self) -> str:
            return "Custom test theme for registry testing"

    # Register custom theme
    custom = CustomTheme()
    register_theme("custom_test_theme", custom)

    # Verify it's registered
    assert "custom_test_theme" in list_themes()
    theme = get_theme("custom_test_theme")
    assert isinstance(theme, CustomTheme)
    assert theme.get_description() == "Custom test theme for registry testing"
    assert theme.get_default_color() == "#FF0000"


def test_handler_registry_singleton():
    """Test that handler registry returns same instance"""
    handler1 = get_handler("line")
    handler2 = get_handler("line")
    assert handler1 is handler2


def test_theme_registry_singleton():
    """Test that theme registry returns same instance"""
    theme1 = get_theme("light")
    theme2 = get_theme("light")
    assert theme1 is theme2


def test_handler_descriptions_are_unique():
    """Test that all handler descriptions are unique"""
    handlers = list_handlers_with_descriptions()
    descriptions = list(handlers.values())
    assert len(descriptions) == len(set(descriptions))


def test_theme_descriptions_are_unique():
    """Test that all theme descriptions are unique"""
    themes = list_themes_with_descriptions()
    descriptions = list(themes.values())
    assert len(descriptions) == len(set(descriptions))
