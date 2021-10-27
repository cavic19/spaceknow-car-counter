from datetime import date, datetime
from typing import Callable, Tuple

import geojson
from geojson import feature
from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi
from spaceknow.authorization import AuthorizationService
from spaceknow.errors import SpaceknowApiException
from spaceknow.models import Credentials, Feature, Observable, ExceptionObserver, Tiles
from spaceknow.control import TaskingManager
from geojson import GeoJSON

#TODO: pridas flag true/false podle toho jestli chces logging nebo ne 

class SpaceknowAction(Observable):
    def __init__(self,
     ragnar_api: RagnarApi,
     kraken_api:KrakenApi,
     tasking_manager: TaskingManager,
     extent: GeoJSON,
     from_date: datetime,
     to_date: datetime ):
        super().__init__()
        self.__ragnar_api = ragnar_api
        self.__kraken_api = kraken_api
        self.__tasking_manager = tasking_manager
        self.__extent = extent
        self.__from_date = from_date
        self.__to_date = to_date


    def _observe_exception(func):
        def wrapper(self):
            try:
                return func(self)
            except Exception as ex:
                self.__on_exception(ex)
            finally:
                self.__remove_all_observers__()
        return wrapper


    def __on_exception(self, ex: Exception):
        self.__notify_observers__(ex)


    @_observe_exception
    def count_cars(self) -> int:
        ragnar_task_obj = self.__ragnar_api.initiate_search(
            self.__extent,
            self.__from_date,
            self.__to_date)

        scene_ids = self.__tasking_manager.wait_untill_completed(ragnar_task_obj)
        return self.__count_cars_in_scenes(scene_ids)


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
        pass



class SpaceknowActionFactory:
    def __init__(self, ragnar_api: RagnarApi, kraken_api:KrakenApi):
        self.__ragnar_api = ragnar_api
        self.__kraken_api = kraken_api
        def __default_logger(text:str, num: int):
            print(text,'|', num)

        self.__tasking_manager = TaskingManager(__default_logger)

    def create(self, extent: GeoJSON, from_date: datetime, to_date: datetime) -> SpaceknowAction:
        return SpaceknowAction(self.__ragnar_api, self.__kraken_api,self.__tasking_manager, extent, from_date, to_date)





class Spaceknow(ExceptionObserver):
    __AUTH0_CLIENT_ID = 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1'

    __kraken_api: KrakenApi = None
    __ragnar_api: RagnarApi = None
    __auth_session: AuthorizedSession = None
    __sk_action_factory: SpaceknowActionFactory = None

    def __init__(self, credentials: Credentials):
        self.__credentials = credentials

    def __initiate(self) -> None:
        self.__auth_service = AuthorizationService(self.__AUTH0_CLIENT_ID)
        self.__auth_session = AuthorizedSession()
        self.__kraken_api = KrakenApi(self.__auth_session)
        self.__ragnar_api = RagnarApi(self.__auth_session)
        self.__sk_action_factory = SpaceknowActionFactory(self.__ragnar_api, self.__kraken_api)

    def __is_initiated(self) -> bool:
        return None not in [self.__kraken_api, self.__ragnar_api] 

    def __authenticate(self) -> None:
        if self.__is_initiated():
            auth_token = self.__auth_service.request_jwt(self.__credentials)
            self.__auth_session.update_auth_token(auth_token)


    def request_on(self, extent: GeoJSON, from_date: datetime, to_date: datetime) -> SpaceknowAction:
        if not self.__is_initiated():
            self.__initiate()
            self.__authenticate()
        sk_action = self.__sk_action_factory.create(extent, from_date, to_date)
        sk_action.__add_observer__(self)
        return sk_action

    def __notify__(self, ex: Exception):
        raise ex




