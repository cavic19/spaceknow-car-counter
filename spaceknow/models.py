from abc import ABC, abstractproperty, abstractmethod
from geojson import GeoJSON
from enum import Enum, auto
from area import area
from typing import Type, TypeVar, Generic
from collections import MutableSequence
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

class Tiles(MutableSequence):
    """Collection of coordinates. Each coresponds to a tile. (zoom, x, y)."""
    def __init__(self, map_id: str, list: list = []):
        self.map_id = map_id
        self._inner_list = list

    def __len__(self):
        return len(self._inner_list)

    def __delitem__(self, index):
        self._inner_list.__delitem__(index - 1)

    def insert(self, index, value):
        self._inner_list.insert(index - 1,value)
    
    def __setitem__(self, index, value):
        self._inner_list.__setitem__(index - 1,value)

    def __getitem__(self,index):
        return self._inner_list.__getitem__(index - 1)
    def __str__(self):
        return f'Id: "{self.map_id}", Tiles: {self._inner_list.__str__()}'


