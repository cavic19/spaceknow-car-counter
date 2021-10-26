from typing import Tuple
from requests import Session, Response
from spaceknow.errors import UnexpectedResponseException,ApiError, AuthorizationException, SpaceknowApiException,TaskingError, TaskingException
from geojson import GeoJSON
from datetime import datetime
from spaceknow.models import TaskingStatus, GeoJSONExtentValidator
from typing import Callable, TypeVar
import area

POST_METHOD = 'POST'
GET_METHOD = 'GET'

class AuthorizedSession(Session):
    """Session that contains authorization token."""
    def __init__(self, authToken: str):
        super().__init__()
        self.update_auth_token(authToken)

    def update_auth_token(self, authToken: str) -> None:
        """Updates current authorization token.""" 
        self.headers.update({'authorization': f'Bearer {authToken}'})



class SpaceknowApi:
    """Base class for all spaceknow APIs. Handling spaceknow api ERRORS. Expects only json formatted response."""
    DOMAIN = 'https://api.spaceknow.com'
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    def __init__(self, session: AuthorizedSession):
        self._session = session
        self._extent_validator = GeoJSONExtentValidator(0)

    def call(self, method, api_endpoint, json_body: dict) -> dict:
        """Calls an API."""
        response = self._session.request(method, url= self.DOMAIN + api_endpoint, json=json_body)
        try:           
            response_json =  response.json()
            self.__check_for_errors(response_json)
            return response_json
        except ValueError as ex:
            raise UnexpectedResponseException(response.text) from ex

    def __check_for_errors(self, response: dict) -> None:
        if self.__is_call_failure(response):
            error_type = response['error']
            error_message = response.get('errorMessage', '')
            raise SpaceknowApiException(error_type, error_message)

    def __is_call_failure(self, response: dict) -> bool:
        return 'error' in response
    
    def _try_get(self, key: str, response: dict):
        try:
            return response[key]
        except KeyError as ex:
            raise UnexpectedResponseException(response) from ex



class TaskingObject(SpaceknowApi):
    """Encapsulates asynchronous operations on the serverside."""
    ENDPOINT = '/tasking/get-status'

    def __init__(self, session: AuthorizedSession, pipeline_id: str, on_success: Callable[[],dict]):
        """
        Args:
            session (AuthorizedSession): HttpClient with valid authorization token
            pipeline_id (str): Pipeline ID coresponding to a encapsulated procedure
            on_success (Callable[[],dict]): Function called when procedure finishes via 'retrieve_data' method
        """
        super().__init__(session)
        self.__pipeline_id = pipeline_id
        self.__on_success = on_success

    @property
    def pipeline_id(self):
        return self.__pipeline_id

    def get_status(self) -> Tuple[TaskingStatus, int]:
        """Checks on a status of procedure enclosed in a tasking object.

        Raises:
            UnexpectedResponseException

        Returns:
            Tuple[TaskingStatus, int]: Tuple of a current status and int represnting recommended time before next check.
        """
        response = self.call(POST_METHOD, self.ENDPOINT, {'pipelineId': self.pipeline_id})
        status = self._try_get('status', response)
        nextTry = int(response.get('nextTry', 0))
        return TaskingStatus[status], nextTry

    
    def retrieve_data(self) -> dict:
        """Retrives data from encapsulated procedere via constructor injected 'on_success' function"""
        return self.__on_success()
    
    def call(self, method, api_endpoint, json_body) -> dict:
        try:
            return super().call(method,api_endpoint,json_body)
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message)
            raise


class RagnarApi(SpaceknowApi):
    """Ragnar API is a system that can be used for searching and ordering satellite imagery"""
    INITIATE_ENDPOINT = '/imagery/search/initiate'    
    RETRIEVE_ENDPOINT = '/imagery/search/retrieve'

    def initiate_search(
        self, 
        extent: GeoJSON, 
        fromDateTime: datetime, 
        toDateTime: datetime, 
        imagesProvider: str = 'gbdx', 
        dataset: str = 'idaho-pansharpened') -> TaskingObject:
        """Initiates search for scenes intersecting with a given extent. Returned scenes are withing a given time period and are provided by a given provider and dataset.

        Args:
            extent (GeoJSON): Desired area to obtain satelite images for.
        """
        self._extent_validator.validate(extent)
        self.__check_dates_validity(fromDateTime, toDateTime)  
        json_body = {
            'provider': imagesProvider,
            'dataset': dataset,
            'startDatetime': fromDateTime.strftime(self.TIME_FORMAT),
            'endDatetime': toDateTime.strftime(self.TIME_FORMAT),
            'extent': extent
        } 
        response = self.call(POST_METHOD, self.INITIATE_ENDPOINT, json_body)
        pipeline_id = self._try_get('pipelineId', response)
        return TaskingObject(self._session, pipeline_id, lambda: self.retrieve_results(pipeline_id))


    def __check_dates_validity(self, fromDateTime: datetime, toDateTime: datetime):
        if fromDateTime > toDateTime:
            raise ValueError('toDateTime argument cant precede fromToDateTime')
    
        

    
    def retrieve_results(self, pipeline_id) -> dict:
        """If the search procedure has been finished, the results are returned. Otherwise it throws TaskingException."""
        response = None
        try:
            response = self.call(POST_METHOD, self.RETRIEVE_ENDPOINT,{'pipelineId': pipeline_id})
            results = response['results']
            dates = [datetime.strptime(r['datetime'], self.TIME_FORMAT)for r in results]
            scenes = [r['sceneId'] for r in results ]
            return dict(zip(scenes,dates))
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message)
            raise
        except KeyError as ex:
            raise UnexpectedResponseException(response) from ex



class KrakenApi(SpaceknowApi):
    RELEASE_PATH = '/kraken/release'
    CARS_PATH = '/cars'
    IMAGERY_PATH = '/imagery'
    INITITATE_ENDPOINT = '/geojson/inititate'
    RETRIEVE_ENDPOINT = '/geojson/retrieve'

    def initiate_car_analysis(self, extent: GeoJSON, scene_id: str) -> TaskingObject:
        return self.__initiate_analysis(extent,scene_id, self.CARS_PATH)

    def initiate_imagery_analysis(self, extent: GeoJSON, scene_id: str) -> TaskingObject:
        return self.__initiate_analysis(extent, scene_id, self.IMAGERY_PATH)

    def __initiate_analysis(self, extent: GeoJSON, scene_id: str, middle_path: str) -> TaskingObject:
        self._extent_validator.validate(extent)
        body_json = {
            'sceneId': scene_id,
            'extent': extent
        }
        endpoint = self.RELEASE_PATH + middle_path + self.INITITATE_ENDPOINT
        response = self.call(POST_METHOD, endpoint, body_json)
        pipeline_id = self._try_get('pipelineId', response)
        return TaskingObject(self._session, pipeline_id, lambda: self.__retrieve_analysis(pipeline_id, middle_path))


    def __retrieve_analysis(self, pipeline_id: str, middle_path: str) -> dict:
        try:
            endpoint = self.RELEASE_PATH + middle_path + self.RETRIEVE_ENDPOINT
            body_json = {'pipelineId': pipeline_id}
            response = self.call(POST_METHOD, endpoint, body_json)
            map_id = self._try_get('mapId', response)
            tiles = self._try_get('tiles', response)
            return {'mapId': map_id, 'tiles': tiles}
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message)
            raise 







