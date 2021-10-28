from datetime import date, datetime
from typing import Callable, Tuple

import geojson
from geojson import feature
from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi
from spaceknow.authorization import AuthorizationService
from spaceknow.errors import AuthorizationException, SpaceknowApiException
from spaceknow.models import Credentials, Feature, Observable, ExceptionObserver, Tiles
from spaceknow.control import TaskingManager
from geojson import GeoJSON

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
            except Exception as ex:
                self.__notify_observers__(ex)
            finally:
                self.__remove_all_observers__()
        return wrapper
    


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
        kraken_task_obj = self.__kraken_api.initiate_car_analysis(self.__extent, scene_id)
        tiles = self.__tasking_manager.wait_untill_completed(kraken_task_obj)           
        return self.__count_cars_in_tiles(tiles)

    def __count_cars_in_tiles(self, tiles: Tiles) -> int:
        car_count = 0
        for tile in tiles:
            car_count += self.__count_cars_in_tile(tiles.map_id, tile)
        return car_count

    def __count_cars_in_tile(self, map_id: str, tile: Tuple[int,int,int]) -> int:
        features = self.__kraken_api.get_detections(map_id, tile)
        return sum([f.count for f in features])


    @_observe_exception
    def get_image(self) -> object:
        assert False, 'Method not implemented!'



class SpaceknowActionFactory:
    def __init__(self, kraken_api:KrakenApi, tasking_manager: TaskingManager):
        self.__kraken_api = kraken_api
        self.__tasking_manager = tasking_manager

    def create(self, extent: GeoJSON, scene_ids: list[str]) -> SpaceknowAnalysis:
        return SpaceknowAnalysis(self.__kraken_api,self.__tasking_manager,scene_ids, extent)

class Spaceknow(ExceptionObserver):
    """Entrypoint of the package."""
    __AUTH0_CLIENT_ID = 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1'
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
        sk_analysis = self.__sk_analysis_factory.create(extent, scene_ids, from_date, to_date)
        sk_analysis.__add_observer__(self)
        return sk_analysis


    def __check_initiation(self):
        if not self.__is_initiated():
            self.__initiate()
            self.__authenticate()

    def __is_initiated(self) -> bool:
        return None not in [self.__kraken_api, self.__ragnar_api] 


    def __initiate(self) -> None:
        self.__auth_service = AuthorizationService(self.__AUTH0_CLIENT_ID)
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
            #TODO: Update authorization token.
            assert False, 'Not implemented.'
        else:
            raise ex




