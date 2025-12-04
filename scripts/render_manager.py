#!/usr/bin/env python3
"""Render Manager CLI

Command-line utility to manage graph rendering including handler and theme discovery,
parameter inspection, and validation capabilities for the gofr-plot service.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.handlers import list_handlers_with_descriptions
from app.themes import list_themes
from app.logger import ConsoleLogger
import logging


def list_handler_types(args):
    """List all available graph handler types"""
    logger = ConsoleLogger(name="render_manager", level=logging.INFO)

    try:
        handlers = list_handlers_with_descriptions()

        if not handlers:
            logger.info("No handlers found.")
            return 0

        logger.info(f"{len(handlers)} Graph Handler(s) Available:")

        if args.verbose:
            logger.info(f"{'Handler Type':<15} {'Description'}")
            logger.info("-" * 80)
            for handler_type, description in handlers.items():
                logger.info(f"{handler_type:<15} {description}")
        else:
            for handler_type in handlers.keys():
                logger.info(handler_type)

        return 0

    except Exception as e:
        logger.error(f"Error listing handlers: {str(e)}")
        return 1


def list_theme_types(args):
    """List all available themes"""
    logger = ConsoleLogger(name="render_manager", level=logging.INFO)

    try:
        themes = list_themes()

        if not themes:
            logger.info("No themes found.")
            return 0

        logger.info(f"{len(themes)} Theme(s) Available:")

        if args.verbose:
            # Import get_theme to access theme objects
            from app.themes import get_theme

            logger.info(f"{'Theme Name':<15} {'Background':<12} {'Grid':<10} {'Text Color'}")
            logger.info("-" * 80)
            for theme_name in themes:
                try:
                    theme = get_theme(theme_name)
                    bg = getattr(theme, "background_color", "N/A")
                    grid = getattr(theme, "grid_color", "N/A")
                    text = getattr(theme, "text_color", "N/A")
                    logger.info(f"{theme_name:<15} {bg:<12} {grid:<10} {text}")
                except Exception:
                    logger.info(f"{theme_name:<15} (details unavailable)")
        else:
            for theme_name in themes:
                logger.info(theme_name)

        return 0
    except Exception as e:
        logger.error(f"Error listing themes: {str(e)}")
        return 1


def get_theme_details(args):
    """Get detailed information about a specific theme"""
    logger = ConsoleLogger(name="render_manager", level=logging.INFO)

    try:
        from app.themes import get_theme

        theme = get_theme(args.theme_name)

        logger.info(f"Theme: {args.theme_name}")
        logger.info("Configuration:")

        # Display all theme attributes
        attrs = [
            "background_color",
            "grid_color",
            "text_color",
            "default_color",
            "colors",
            "font_family",
            "font_size",
        ]

        for attr in attrs:
            if hasattr(theme, attr):
                value = getattr(theme, attr)
                if isinstance(value, list):
                    logger.info(f"  {attr:<20} {', '.join(str(v) for v in value[:5])}")
                else:
                    logger.info(f"  {attr:<20} {value}")

        return 0

    except ValueError:
        logger.error(f"Theme '{args.theme_name}' not found")
        logger.info("Available themes:")
        for theme in list_themes():
            logger.info(f"  - {theme}")
        return 1
    except Exception as e:
        logger.error(f"Error getting theme details: {str(e)}")
        return 1


def get_handler_details(args):
    """Get detailed information about a specific handler"""
    logger = ConsoleLogger(name="render_manager", level=logging.INFO)

    try:
        handlers = list_handlers_with_descriptions()

        if args.handler_type not in handlers:
            logger.error(f"Handler '{args.handler_type}' not found")
            logger.info("Available handlers:")
            for handler in handlers.keys():
                logger.info(f"  - {handler}")
            return 1

        logger.info(f"Handler: {args.handler_type}")
        logger.info(f"Description: {handlers[args.handler_type]}")

        # Import handler class to get more details
        from app.handlers import LineGraphHandler, ScatterGraphHandler, BarGraphHandler

        handler_classes = {
            "line": LineGraphHandler,
            "scatter": ScatterGraphHandler,
            "bar": BarGraphHandler,
        }

        if args.handler_type in handler_classes:
            handler_class = handler_classes[args.handler_type]
            logger.info(f"Class: {handler_class.__name__}")

            # Show supported parameters from GraphParams
            logger.info("\nSupported Parameters:")
            params = [
                ("title", "Graph title", "required"),
                ("x", "X-axis values", "optional"),
                ("y1-y5", "Y-axis datasets", "at least y1 required"),
                ("label1-label5", "Dataset labels", "optional"),
                ("color1-color5", "Dataset colors", "optional"),
                ("xlabel", "X-axis label", "optional"),
                ("ylabel", "Y-axis label", "optional"),
                ("type", "Graph type (line/scatter/bar)", "required"),
                ("format", "Output format (png/jpg/svg/pdf)", "optional"),
                ("theme", "Visual theme", "optional"),
                ("line_width", "Line width for line plots", "optional"),
                ("marker_size", "Marker size", "optional"),
                ("alpha", "Transparency (0-1)", "optional"),
                ("xmin/xmax/ymin/ymax", "Axis limits", "optional"),
                ("x_major_ticks/y_major_ticks", "Major tick spacing", "optional"),
                ("x_minor_ticks/y_minor_ticks", "Minor tick spacing", "optional"),
            ]

            for param_name, param_desc, param_req in params:
                logger.info(f"  {param_name:<25} {param_desc:<40} [{param_req}]")

        return 0

    except Exception as e:
        logger.error(f"Error getting handler details: {str(e)}")
        return 1


def validate_graph_params(args):
    """Validate graph parameters against expected schema"""
    logger = ConsoleLogger(name="render_manager", level=logging.INFO)

    try:
        from app.graph_params import GraphParams
        from app.validation.validator import GraphDataValidator

        # Parse parameters as key=value pairs
        params = {}
        if args.parameters:
            for param_str in args.parameters:
                if "=" in param_str:
                    key, value = param_str.split("=", 1)
                    # Try to parse as list if it looks like one
                    if value.startswith("[") and value.endswith("]"):
                        try:
                            import json

                            value = json.loads(value)
                        except:  # noqa: E722 - intentionally broad
                            pass
                    # Try to parse as number
                    elif value.replace(".", "", 1).replace("-", "", 1).isdigit():
                        value = float(value) if "." in value else int(value)
                    params[key] = value
                else:
                    logger.error(f"Invalid parameter format: {param_str}. Use key=value")
                    return 1

        # Set defaults
        if "title" not in params:
            params["title"] = "Validation Test"
        if "type" not in params:
            params["type"] = "line"
        if "y1" not in params and "y" not in params:
            logger.error("At least one dataset (y1 or y) is required")
            return 1

        # Create GraphParams
        try:
            graph_data = GraphParams(**params)
        except Exception as e:
            logger.error(f"Failed to create GraphParams: {str(e)}")
            return 1

        # Validate
        validator = GraphDataValidator()
        result = validator.validate(graph_data)

        if result.is_valid:
            logger.info("✓ Graph parameters are valid")
            logger.info("Provided parameters:")
            for key, value in params.items():
                display_value = (
                    value
                    if not isinstance(value, list) or len(value) < 10
                    else f"[{len(value)} values]"
                )
                logger.info(f"  {key}: {display_value}")
            return 0
        else:
            logger.error("✗ Graph parameters are invalid:")
            for error in result.errors:
                logger.error(f"  - {error.field}: {error.message}")
                logger.error(f"    Expected: {error.expected}")
                if error.suggestions:
                    logger.error("    Suggestions:")
                    for suggestion in error.suggestions:
                        logger.error(f"      • {suggestion}")
            return 1

    except Exception as e:
        logger.error(f"Error validating parameters: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="gofr-plot Render Manager - Manage graph handlers and themes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all graph handlers
  python render_manager.py handlers
  python render_manager.py handlers -v

  # Get handler details
  python render_manager.py handler-info line
  python render_manager.py handler-info scatter

  # List all themes
  python render_manager.py themes
  python render_manager.py themes -v

  # Get theme details
  python render_manager.py theme-info light
  python render_manager.py theme-info dark

  # Validate graph parameters
  python render_manager.py validate title="Sales" type=line y1="[10,20,30,40]"
  python render_manager.py validate title="Test" y1="[1,2,3]" theme=dark format=svg

Environment Variables:
    GOFR_PLOT_DATA_DIR      Override project data directory
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Handlers subcommand
    handlers_parser = subparsers.add_parser(
        "handlers",
        help="List available graph handlers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="List all available graph handler types (line, scatter, bar)",
    )
    handlers_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )

    # Handler info subcommand
    handler_info_parser = subparsers.add_parser(
        "handler-info",
        help="Get details about a specific handler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Get detailed information about a graph handler",
    )
    handler_info_parser.add_argument("handler_type", help="Handler type (line, scatter, bar)")

    # Themes subcommand
    themes_parser = subparsers.add_parser(
        "themes",
        help="List available themes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="List all available visual themes",
    )
    themes_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )

    # Theme info subcommand
    theme_info_parser = subparsers.add_parser(
        "theme-info",
        help="Get details about a specific theme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Get detailed information about a theme",
    )
    theme_info_parser.add_argument("theme_name", help="Theme name (light, dark, bizlight, bizdark)")

    # Validate parameters subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate graph parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Validate parameters against GraphParams schema",
    )
    validate_parser.add_argument(
        "parameters", nargs="*", help="Parameters as key=value pairs (use [1,2,3] for lists)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "handlers":
        return list_handler_types(args)
    elif args.command == "handler-info":
        return get_handler_details(args)
    elif args.command == "themes":
        return list_theme_types(args)
    elif args.command == "theme-info":
        return get_theme_details(args)
    elif args.command == "validate":
        return validate_graph_params(args)
    else:
        logger = ConsoleLogger(name="render_manager", level=logging.INFO)
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
