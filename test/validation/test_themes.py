"""Tests for theme descriptions and theme listing functionality"""

from app.themes import (
    get_theme,
    list_themes_with_descriptions,
    LightTheme,
    DarkTheme,
    BizLightTheme,
    BizDarkTheme,
)


def test_all_themes_have_descriptions():
    """Test that all themes have descriptions"""
    themes = ["light", "dark", "bizlight", "bizdark"]

    for theme_name in themes:
        theme = get_theme(theme_name)
        description = theme.get_description()

        assert description is not None, f"Theme {theme_name} has no description"
        assert len(description) > 0, f"Theme {theme_name} has empty description"
        assert isinstance(description, str), f"Theme {theme_name} description is not a string"


def test_light_theme_description():
    """Test that light theme has appropriate description"""
    theme = LightTheme()
    description = theme.get_description()

    assert "bright" in description.lower() or "light" in description.lower()
    assert len(description) > 20  # Should be descriptive enough


def test_dark_theme_description():
    """Test that dark theme has appropriate description"""
    theme = DarkTheme()
    description = theme.get_description()

    assert "dark" in description.lower() or "eye strain" in description.lower()
    assert len(description) > 20


def test_bizlight_theme_description():
    """Test that business light theme has appropriate description"""
    theme = BizLightTheme()
    description = theme.get_description()

    assert "business" in description.lower() or "professional" in description.lower()
    assert len(description) > 20


def test_bizdark_theme_description():
    """Test that business dark theme has appropriate description"""
    theme = BizDarkTheme()
    description = theme.get_description()

    assert "business" in description.lower() or "professional" in description.lower()
    assert len(description) > 20


def test_list_themes_with_descriptions():
    """Test that list_themes_with_descriptions returns all themes"""
    themes_dict = list_themes_with_descriptions()

    # Check that we have all expected themes
    expected_themes = {"light", "dark", "bizlight", "bizdark"}
    assert set(themes_dict.keys()) == expected_themes

    # Check that all descriptions are non-empty strings
    for theme_name, description in themes_dict.items():
        assert isinstance(description, str)
        assert len(description) > 0
        assert description == get_theme(theme_name).get_description()


def test_list_themes_with_descriptions_format():
    """Test that descriptions are properly formatted"""
    themes_dict = list_themes_with_descriptions()

    for theme_name, description in themes_dict.items():
        # Description should not have trailing whitespace
        assert description == description.strip()

        # Description should start with a capital letter
        assert description[0].isupper()

        # Description should be at least 20 characters
        assert len(description) >= 20


def test_themes_with_descriptions_are_unique():
    """Test that each theme has a unique description"""
    themes_dict = list_themes_with_descriptions()
    descriptions = list(themes_dict.values())

    # All descriptions should be unique
    assert len(descriptions) == len(set(descriptions))
