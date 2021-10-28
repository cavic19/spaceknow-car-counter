from abc import ABC, abstractproperty, abstractmethod
from geojson import GeoJSON
from enum import Enum, auto
from area import area
from collections import MutableSequence
from dataclasses import dataclass
from geojson import GeoJSON


@dataclass
class Feature:
    class_type: str
    count: int
    geometry: GeoJSON

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


# class Tiles(MutableSequence):
#     """Collection of coordinates. Each coresponds to a tile. (zoom, x, y)."""
#     def __init__(self, map_id: str,  list: list = []):
#         self.map_id = map_id
#         self._inner_list = list

#     def __len__(self):
#         return len(self._inner_list)

#     def __delitem__(self, index):
#         self._inner_list.__delitem__(index)

#     def insert(self, index, value):
#         self._inner_list.insert(index,value)
    
#     def __setitem__(self, index, value):
#         self._inner_list.__setitem__(index,value)

#     def __getitem__(self,index):
#         return self._inner_list.__getitem__(index)
#     def __str__(self):
#         return f'Id: "{self.map_id}", Tiles: {self._inner_list.__str__()}'




class ExceptionObserver(ABC):
    """Reacts on exceptions raised by observable."""
    @abstractmethod
    def __notify__(self, ex: Exception):
        pass

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






