from abc import ABC, abstractproperty, abstractmethod
from geojson import GeoJSON
from enum import Enum, auto
from area import area
from typing import Type, TypeVar, Generic

class TaskingStatus(Enum):
    NEW = auto()
    PROCESSING = auto()
    RESOLVED = auto()
    FAILED = auto()

class GeoJSONExtentValidator:
    def __init__(self, minArea: float):
        self.__minArea = minArea

    def validate(self, extent: GeoJSON) -> None:
        if area(extent) <= self.__minArea:
            raise ValueError("Extent's area can't be 0!")



