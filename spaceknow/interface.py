from datetime import datetime
from typing import Callable, Iterable, Tuple, Union

from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi
from spaceknow.authorization import AuthorizationService
from spaceknow.errors import AuthorizationException, SpaceknowApiException
from spaceknow.models import Credentials, Feature, Observable, ExceptionObserver
from spaceknow.control import TaskingManager
from geojson import GeoJSON
from PIL.Image import Image
import itertools
from spaceknow.visualization import create_image_from_tile, merge_images

#TODO: pridas flag true/false podle toho jestli chces logging nebo ne 

class SpaceknowAnalysis(Observable):  
    """Encapsulation of spaceknow API calls."""

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
        """Redirects a func's exception to observers."""
        def wrapper(self):
            try:
                return func(self)
            except AuthorizationException as ex:
                self.__notify_observers__(ex)
            finally:
                self.__remove_all_observers__()
        return wrapper
    
    # region count_cars
    @_observe_exception
    def count_cars(self) -> int:
        """Counts cars in a prespecified area.

        Returns:
            int: Number of cars found within given extent (GeoJSON).
        """
        return self.__count_cars_in_scenes(self.__scene_ids)

    def __count_cars_in_scenes(self, scene_ids: list[str]) -> int:
        car_count = 0
        for scene_id in scene_ids:
            car_count += self.__count_cars_in_scene(scene_id)
        return car_count


    def __count_cars_in_scene(self, scene_id: str) -> int:    
        features = self.__get_cars_tiles_and_features(scene_id)[1]
        return sum([self.__cars_in_features(f) for f in features])

    
    def __cars_in_features(self, features: list[Feature]) -> int:
        return sum([f.count for f in features])
    # endregion

    def __get_features_from_tile(self, map_id: str, tile: Tuple[int,int,int]) -> list[Feature]:
        return self.__kraken_api.get_detections(map_id, tile)

# region get_image
    # In a case of already carried out cars analysis the results are stored here.
    __cache: dict[str, dict[tuple[int,int,int], list[Feature]]] = {}

    @_observe_exception
    def get_images(self) -> list[Image]:
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
        images_with_highlights = [create_image_from_tile(*i) for i in zip(tiles, images, geometries)]
        images_layout = self.__build_layout(tiles, images_with_highlights) 
        return merge_images(images_layout)

    def __get_cars_tiles_and_features(self,scene_id: str) -> Union[list[tuple[int,int,int]], list[list[Feature]]]:
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

    def __build_layout(self, tiles, images: list[Image]) -> list[list[Image]]:
        zipped = zip(tiles, images)
        sorted_by_y_tile = sorted(zipped, key=lambda x: x[0][2])
        grouped_by_y_tile = itertools.groupby(sorted_by_y_tile, lambda x: x[0][2])
        sorted_by_x_tile = []
        for key, subbiter in grouped_by_y_tile:
            sorted_by_x_tile.append(sorted(list(subbiter), key=lambda x: x[0][1]))
        return [[col[1] for col in row] for row in sorted_by_x_tile]


# endregion



class SpaceknowActionFactory:
    def __init__(self, kraken_api:KrakenApi, tasking_manager: TaskingManager):
        self.__kraken_api = kraken_api
        self.__tasking_manager = tasking_manager

    def create(self, extent: GeoJSON, scene_ids: list[str]) -> SpaceknowAnalysis:
        return SpaceknowAnalysis(self.__kraken_api,self.__tasking_manager,scene_ids, extent)

class Spaceknow(ExceptionObserver):
    """Entrypoint of the package."""
    AUTH0_CLIENT_ID = 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1'
    __kraken_api: KrakenApi = None
    __ragnar_api: RagnarApi = None
    __auth_session: AuthorizedSession = None
    __sk_analysis_factory: SpaceknowActionFactory = None

    def __init__(self, credentials: Credentials, logger: Callable[[str], None] = None):
        self.__credentials = credentials
        self.__tasking_manager = TaskingManager(lambda tx, nm: logger(f'{tx}! Next try in {nm}s.'))

    def query_on(self, extent: GeoJSON, from_date: datetime, to_date: datetime) -> SpaceknowAnalysis:
        """Requests imagery data from a remote api and returns 'SpaceknowAnalysis' object on which futher actions maybe be caried out. """
        self.__check_initiation()
        scene_ids = self.__get_scene_ids(extent, from_date, to_date)
        sk_analysis = self.__sk_analysis_factory.create(extent, scene_ids)
        sk_analysis.__add_observer__(self)
        return sk_analysis


    def __check_initiation(self):
        if not self.__is_initiated():
            self.__initiate()
            self.__authenticate()

    def __is_initiated(self) -> bool:
        return None not in [self.__kraken_api, self.__ragnar_api] 


    def __initiate(self) -> None:
        self.__auth_service = AuthorizationService(self.AUTH0_CLIENT_ID)
        self.__auth_session = AuthorizedSession()
        self.__kraken_api = KrakenApi(self.__auth_session)
        self.__ragnar_api = RagnarApi(self.__auth_session)
        self.__sk_analysis_factory = SpaceknowActionFactory(self.__kraken_api, self.__tasking_manager)

    def __authenticate(self) -> None:
        if self.__is_initiated():
            auth_token = self.__auth_service.request_jwt(self.__credentials)
            self.__auth_session.update_auth_token(auth_token)

    def __get_scene_ids(self, extent: GeoJSON, from_date: datetime, to_date: datetime):       
        ragnar_task_obj = self.__ragnar_api.initiate_search(
            extent,
            from_date,
            to_date)
        return self.__tasking_manager.wait_untill_completed(ragnar_task_obj)

    def __notify__(self, ex: Exception):
        if isinstance(ex, AuthorizationException):
            #TODO: Updates authorization token.
            assert False, 'Not implemented.'
        else:
            raise ex




