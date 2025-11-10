from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from app.graph_params import GraphParams


class GraphHandler(ABC):
    """Base class for graph type handlers"""

    @abstractmethod
    def plot(self, ax: "Axes", data: "GraphParams") -> None:
        """Plot the graph on the given axes"""
        pass
