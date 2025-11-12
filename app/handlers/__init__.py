from app.handlers.base import GraphHandler
from app.handlers.line import LineGraphHandler
from app.handlers.scatter import ScatterGraphHandler
from app.handlers.bar import BarGraphHandler

__all__ = [
    "GraphHandler",
    "LineGraphHandler",
    "ScatterGraphHandler",
    "BarGraphHandler",
    "list_handlers_with_descriptions",
]


def list_handlers_with_descriptions() -> dict[str, str]:
    """
    Get all available graph handlers with their descriptions.

    Returns:
        Dict mapping handler names to their descriptions
    """
    return {
        "line": LineGraphHandler().get_description(),
        "scatter": ScatterGraphHandler().get_description(),
        "bar": BarGraphHandler().get_description(),
    }
