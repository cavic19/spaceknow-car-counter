from datetime import datetime
from typing import Callable, Tuple, Union

from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi
from spaceknow.authorization import AuthorizationService
from spaceknow.errors import AuthorizationException, NoEntriesException
from spaceknow.models import Credentials, Feature, Observable, ExceptionObserver
from spaceknow.control import TaskingManager
from geojson import GeoJSON
from PIL.Image import Image
import itertools
from spaceknow.visualization import highlight_cars_on_tile, merge_images

#TODO: pridas flag true/false podle toho jestli chces logging nebo ne 

class SpaceknowAnalysis(Observable):  
    """Conducts analysis (imagery, cars) on a specified area. Encapsulates kraken api."""
    #Save cars_analysis results per scene_id. TODO: create better data type
    __cache: dict[str, dict[tuple[int,int,int], list[Feature]]] = {}

    def __init__(self,
     kraken_api: KrakenApi,
     tasking_manager: TaskingManager,
     scene_ids: list[str],
     extent: GeoJSON):
        super().__init__()
        self.__kraken_api = kraken_api
        self.__tasking_manager = tasking_manager
        self.__scene_ids = scene_ids
        self.__extent = extent

    def _observe_exception(func):
        """In special cases redirects exception to observers (i.e. AuthorizationException)."""
        def wrapper(self):
            try:
                return func(self)
            except AuthorizationException as ex:
                self.__notify_observers__(ex)
            finally:
                self.__remove_all_observers__()
        return wrapper
    

    @_observe_exception
    def get_images(self) -> list[Image]:
        """Get image per scene. The image contains highlighted cars found in a given extent."""
        output = []
        for scene_id in self.__scene_ids:
            output.append(self.__get_images_from_scene_id(scene_id))
        return output


    def __get_images_from_scene_id(self, scene_id: str) -> Image:  
        tiles, features = self.__get_cars_tiles_and_features(scene_id)
        geometries = [[f.geometry for f in tile_fs] for tile_fs in features]
        kraken_imagery_task_obj = self.__kraken_api.initiate_imagery_analysis(self.__extent, scene_id)      
        imagery_map_id = self.__tasking_manager.wait_untill_completed(kraken_imagery_task_obj)[0]
        images = [self.__get_image_from_tile(imagery_map_id, t) for t in tiles]
        images_with_highlights = [highlight_cars_on_tile(*i) for i in zip(tiles, images, geometries)]
        images_layout = self.__build_layout(tiles, images_with_highlights) 
        return merge_images(images_layout)

    def __get_cars_tiles_and_features(self,scene_id: str) -> Union[list[tuple[int,int,int]], list[list[Feature]]]:
        """In a case of cached data, returns them. Otherwise, makes a call to the kraken api and retrives and cache them."""
        if scene_id in self.__cache:
            scene_cache = self.__cache[scene_id]
            return scene_cache[0], scene_cache[1]

        kraken_cars_task_obj = self.__kraken_api.initiate_car_analysis(self.__extent, scene_id)
        cars_map_id, cars_tiles = self.__tasking_manager.wait_untill_completed(kraken_cars_task_obj)
        features = [self.__get_features_from_tile(cars_map_id, tile) for tile in cars_tiles]
        self.__cache[scene_id] =  (cars_tiles, features)
        return cars_tiles, features


    def __get_image_from_tile(self, map_id:str, tile: Tuple[int,int,int]) -> Image:
        return self.__kraken_api.get_satelite_image(map_id, tile)

    def __build_layout(self, tiles: list[tuple[int,int,int]], images: list[Image]) -> list[list[Image]]:
        """Puts together tile_images parts so they add up to a complete image.

        Args:
            tiles (list[tuple[int,int,int]]): List of tile coordinates. This acts as a sorting key.
            images (list[Image]): List of tile images. The list must be in a same order as tiles.

        Returns:
            list[list[Image]]: Layout of images.
        """
        zipped = zip(tiles, images)
        #zipped looks like [((zoom, x_tile, y_tile), image), ...], so x[0][2] is y_tile coordinate
        sorted_by_y_tile = sorted(zipped, key=lambda x: x[0][2])
        grouped_by_y_tile = itertools.groupby(sorted_by_y_tile, lambda x: x[0][2])
        sorted_by_x_tile = []
        for key, subbiter in grouped_by_y_tile:
            sorted_by_x_tile.append(sorted(list(subbiter), key=lambda x: x[0][1]))
        return [[col[1] for col in row] for row in sorted_by_x_tile]

    @_observe_exception
    def count_cars(self) -> int:
        """Counts cars in a prespecified area.

        Returns:
            int: Number of cars found within given extent (GeoJSON).
        """
        car_count = 0
        for scene_id in self.__scene_ids:
            car_count += self.__cars_in_scene(scene_id)
        return car_count

    def __cars_in_scene(self, scene_id: str) -> int:    
        features = self.__get_cars_tiles_and_features(scene_id)[1]
        return sum([self.__cars_in_features(f) for f in features])
  
    def __cars_in_features(self, features: list[Feature]) -> int:
        return sum([f.count for f in features])

    def __get_features_from_tile(self, map_id: str, tile: Tuple[int,int,int]) -> list[Feature]:
        return self.__kraken_api.get_detections(map_id, tile)


class SpaceknowActionFactory:
    def __init__(self, kraken_api:KrakenApi, tasking_manager: TaskingManager):
        self.__kraken_api = kraken_api
        self.__tasking_manager = tasking_manager

    def create(self, extent: GeoJSON, scene_ids: list[str]) -> SpaceknowAnalysis:
        return SpaceknowAnalysis(self.__kraken_api,self.__tasking_manager,scene_ids, extent)

class SpaceknowCarsAnalyser(ExceptionObserver):
    """By means of spaceknow apis, such as ragnar and kraken, analyses satelite images and returns number of cars in a given area. 
    The cars can be highlighted in a satelite image a returned. """
    
    AUTH0_CLIENT_ID = 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1'

    def __init__(self, username:str, password: str, logger: Callable[[str], None] = None):
        self.__credentials = Credentials(username, password)
        self.__tasking_manager = TaskingManager(lambda tx, nm: logger(f'{tx}! Next try in {nm}s.')  if logger else None)
        self.__auth_session = AuthorizedSession()
        self.__ragnar_api = RagnarApi(self.__auth_session)
        self.__kraken_api = KrakenApi(self.__auth_session)
        self.__auth_service = AuthorizationService(self.AUTH0_CLIENT_ID)
        self.__sk_analysis_factory = SpaceknowActionFactory(self.__kraken_api, self.__tasking_manager)
        self.__is_initialized = False


    def analyse_on(self, extent: GeoJSON, from_date: datetime, to_date: datetime) -> SpaceknowAnalysis:
        """Requests imagery data from a remote api and returns 'SpaceknowAnalysis' object on which futher actions may be caried out

        Args:
            extent (GeoJSON): The area of convern
            from_date (datetime): The earliest possible image creationg date
            to_date (datetime): The latest possible image creationg date

        Returns:
            SpaceknowAnalysis: By means of this object the analysis is conducted
        """
        self.initialize()
        scene_ids = self.__get_scene_ids(extent, from_date, to_date)
        if len(scene_ids) == 0:
            raise NoEntriesException('No scene ids.')      
        sk_analysis = self.__sk_analysis_factory.create(extent, scene_ids)
        sk_analysis.__add_observer__(self)
        return sk_analysis

    def initialize(self):
        if not self.__is_initialized:
            self.__authenticate()
            self.__is_initialized = True

    def __authenticate(self) -> None:
        auth_token = self.__auth_service.request_jwt(self.__credentials)
        self.__auth_session.update_auth_token(auth_token)

    def __get_scene_ids(self, extent: GeoJSON, from_date: datetime, to_date: datetime):       
        ragnar_task_obj = self.__ragnar_api.initiate_search(
            extent,
            from_date,
            to_date)
        return self.__tasking_manager.wait_untill_completed(ragnar_task_obj)

    def __anounce_exception__(self, ex: Exception):
        if isinstance(ex, AuthorizationException):
            #TODO: Updates authorization token.
            assert False, 'Not implemented.'
        else:
            raise ex
