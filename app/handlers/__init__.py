from typing import Dict
from app.handlers.base import GraphHandler
from app.handlers.line import LineGraphHandler
from app.handlers.scatter import ScatterGraphHandler
from app.handlers.bar import BarGraphHandler

# Registry of available handlers
_HANDLERS: Dict[str, GraphHandler] = {
    "line": LineGraphHandler(),
    "scatter": ScatterGraphHandler(),
    "bar": BarGraphHandler(),
}


def get_handler(name: str) -> GraphHandler:
    """
    Get a handler by name

    Args:
        name: Handler name (line, scatter, bar)

    Returns:
        GraphHandler instance

    Raises:
        ValueError: If handler name is not found
    """
    handler_name = name.lower() if name else ""
    handler = _HANDLERS.get(handler_name)

    if handler is None:
        available = ", ".join(_HANDLERS.keys())
        raise ValueError(f"Unknown handler '{name}'. Available handlers: {available}")

    return handler


def register_handler(name: str, handler: GraphHandler) -> None:
    """
    Register a custom handler

    Args:
        name: Handler name
        handler: GraphHandler instance
    """
    _HANDLERS[name.lower()] = handler


def list_handlers() -> list[str]:
    """Get a list of available handler names"""
    return list(_HANDLERS.keys())


def list_handlers_with_descriptions() -> dict[str, str]:
    """
    Get all available graph handlers with their descriptions.

    Returns:
        Dict mapping handler names to their descriptions
    """
    return {name: handler.get_description() for name, handler in _HANDLERS.items()}


__all__ = [
    "GraphHandler",
    "LineGraphHandler",
    "ScatterGraphHandler",
    "BarGraphHandler",
    "get_handler",
    "register_handler",
    "list_handlers",
    "list_handlers_with_descriptions",
]
