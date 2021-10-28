from abc import ABC, abstractproperty, abstractmethod
from geojson import GeoJSON
from enum import Enum, auto
from area import area
from collections import MutableSequence
from dataclasses import dataclass
from geojson import GeoJSON, Polygon


@dataclass
class Feature:
    """Dataclass being returned by KrakenApi.get_detections."""
    class_type: str
    """Determines object classification"""
    count: int
    """Number of objects"""
    geometry: Polygon
    """Polygon representing found object."""

    def __str__(self) -> str:
        return f'class: {self.class_type}, count: {self.count}, geometry: {str(self.geometry)}'

@dataclass
class Credentials:
    username: str
    password: str


class TaskingStatus(Enum):
    NEW = auto()
    PROCESSING = auto()
    RESOLVED = auto()
    FAILED = auto()

class GeoJSONExtentValidator:
    def __init__(self, minArea: float):
        self.__minArea = minArea

    def validate(self, extent: GeoJSON) -> None:
        """Validates the presented extent in acordance with spaceknow API requirments.

        Raises:
            ValueError: In a case of not valid extent.
        """
        if area(extent) <= self.__minArea:
            raise ValueError("Extent's area can't be 0!")



class ExceptionObserver(ABC):
    """Reacts on exceptions raised by observable."""
    @abstractmethod
    def __notify__(self, ex: Exception):
        pass


# Part of a observer pattern
class Observable():
    __observers__: list[ExceptionObserver]

    def __init__(self):
        self.__observers__ = []
        
    def __add_observer__(self, observer: ExceptionObserver) -> None:
        self.__observers__.append(observer)

    def __remove_observer__(self, observer: ExceptionObserver) -> None:
        self.__observers__.remove(observer)

    def __remove_all_observers__(self):
        self.__observers__.clear()

    def __notify_observers__(self, ex: Exception) -> None:
        for observer in self.__observers__:
            observer.__notify__(ex)






