from typing import Tuple
from PIL import Image, UnidentifiedImageError
from requests import Session
from spaceknow.errors import UnexpectedResponseException, SpaceknowApiException,TaskingError, TaskingException
from geojson import GeoJSON
from datetime import datetime
from spaceknow.models import Feature, TaskingStatus, GeoJSONExtentValidator
from typing import Callable, Union
from io import BytesIO


POST_METHOD = 'POST'
GET_METHOD = 'GET'

class AuthorizedSession(Session):
    """Session that contains authorization token."""
    def __init__(self, authToken: str = None):
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

    def _call(self, method, api_endpoint, json_body: dict) -> dict:
        """Calls an API."""
        response = self._session.request(method, url= self.DOMAIN + api_endpoint, json=json_body)
        try:       
            response_json =  response.json()
            self.__check_for_errors(response_json)
            return response_json
        except ValueError as ex:
            raise UnexpectedResponseException(response.text) from ex

    def _get_image(self, endpoint) -> Image:
        """Gets image from a given endpoint.

        Raises:
            UnexpectedResponseException: When no image parsable data are presented.
        """
        response = self._session.request(GET_METHOD, url = self.DOMAIN + endpoint)
        try:
            return Image.open(BytesIO(response.content))
        except UnidentifiedImageError:
            raise UnexpectedResponseException(response)

        

    def __check_for_errors(self, response: dict) -> None:
        """Check whether any errors where thrown. If so, raises SpaceknoApiException."""
        if self.__is_call_failure(response):
            error_type = response['error']
            error_message = response.get('errorMessage', '')
            raise SpaceknowApiException(error_type, error_message)

    def __is_call_failure(self, response: dict) -> bool:
        return 'error' in response
    
    def _try_get(self, key: str, response: dict):
        """Tries to get a value out of a given response. If failure, raises UnexpectedResponseException."""
        try:
            return response[key]
        except KeyError as ex:
            raise UnexpectedResponseException(response) from ex



class TaskingObject(SpaceknowApi):
    """Encapsulates asynchronous operations on serverside."""
    ENDPOINT = '/tasking/get-status'

    def __init__(self, session: AuthorizedSession, pipeline_id: str, on_success: Callable[[],dict]):
        """
        Args:
            session (AuthorizedSession): HttpClient with valid authorization token
            pipeline_id (str): Pipeline ID, that coresponds to a encapsulated procedure
            on_success (Callable[[],dict]): Function called when procedure is successfully finished
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

    
    def retrieve_data(self):
        """Retrives data from encapsulated procedere via constructor injected 'on_success' function"""
        return self.__on_success()
    
    def call(self, method, api_endpoint, json_body) -> dict:
        try:
            return super()._call(method,api_endpoint,json_body)
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message) from ex
            raise


class RagnarApi(SpaceknowApi):
    """Ragnar API is a system that can be used for searching and ordering satellite imagery"""
    INITIATE_ENDPOINT = '/imagery/search/initiate'    
    RETRIEVE_ENDPOINT = '/imagery/search/retrieve'

    def initiate_search(
        self, 
        extent: GeoJSON, 
        from_date_time: datetime, 
        to_date_time: datetime, 
        images_provider: str = 'gbdx', 
        dataset: str = 'idaho-pansharpened') -> TaskingObject:
        """Initiates search for scenes intersecting with a given extent. Returned scenes are within a given time period and are provided by a given provider and dataset.

        Args:
            extent (GeoJSON): Desired area to obtain satelite images for.
        """
        self._extent_validator.validate(extent)
        self.__check_dates_validity(from_date_time, to_date_time)  
        json_body = {
            'provider': images_provider,
            'dataset': dataset,
            'startDatetime': from_date_time.strftime(self.TIME_FORMAT),
            'endDatetime': to_date_time.strftime(self.TIME_FORMAT),
            'extent': extent
        } 
        response = self._call(POST_METHOD, self.INITIATE_ENDPOINT, json_body)
        pipeline_id = self._try_get('pipelineId', response)
        return TaskingObject(self._session, pipeline_id, lambda: self.retrieve_results(pipeline_id))


    def __check_dates_validity(self, from_date_time: datetime, to_date_time: datetime):
        if from_date_time > to_date_time:
            raise ValueError('toDateTime argument cant precede fromToDateTime')
    
        
    def retrieve_results(self, pipeline_id) -> list[str]:
        """Retrieves list of 'scene ids' for a given procedure specified in 'initiate_search' method.

        Args:
            pipeline_id ([type]): Pipeline id of the procedure that is desired to be retrieved.

        Raises:
            TaskingException: In a case that pipeline wasn't processed or the pipeline id is wrong.
            UnexpectedResponseException

        Returns:
            list[str]: List of scene ids coresponding to original query in 'initiate_search' method.
        """
        response = None
        try:
            response = self._call(POST_METHOD, self.RETRIEVE_ENDPOINT,{'pipelineId': pipeline_id})
            results = response['results']
            datetimes = [datetime.strptime(r['datetime'], self.TIME_FORMAT) for r in results]
            scenes = [r['sceneId'] for r in results ]
            return list(zip(datetimes,scenes))
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message) from ex
            raise
        except KeyError as ex:
            raise UnexpectedResponseException(response) from ex



class KrakenApi(SpaceknowApi):
    """The API interfaces imagery and analyses through tiled web map interface."""

    RELEASE_ENDPOINT = "/kraken/release/%s/geojson/%s"
    """/kraken/release/<map_type/geojson/<initiate|retrieve>*"""

    GRID_IMAGERY_ENDPOINT = "/kraken/grid/%s/-/%s/%s/%s/truecolor.png"
    """/kraken/grid/<map_id>/-/<z>/<x>/<y>/truecolor.png"""

    GRID_CARS_ENDPOINT = "/kraken/grid/%s/-/%s/%s/%s/detections.geojson"
    """/kraken/grid/<map_id>/-/<z>/<x>/<y>/detections.geojson"""
    
    def initiate_car_analysis(self, extent: GeoJSON, scene_id: str) -> TaskingObject:
        """[summary]

        Args:
            extent (GeoJSON): Are of concern
            scene_id (str): Id of a chosen scene (satelite image)
        """
        return self.__initiate_analysis(extent,scene_id, 'cars')

    def initiate_imagery_analysis(self, extent: GeoJSON, scene_id: str) -> TaskingObject:
        """Initiates imagery analysis and returns TaskingObject. After retrieval, tiles (coordinates) of a given extent are obtained and map_id to identify the result.
        Map_id is essential for conducting further analysis.


        Args:
            extent (GeoJSON): Are of concern.
            scene_id (str): Unambiguously identifies satelite image on which the imagery analysis is conducted.

        Returns:
            TaskingObject
        """
        return self.__initiate_analysis(extent, scene_id, 'imagery')

    def __initiate_analysis(self, extent: GeoJSON, scene_id: str, middle_path: str) -> TaskingObject:
        self._extent_validator.validate(extent)
        body_json = {
            'sceneId': scene_id,
            'extent': extent
        }
        endpoint = self.RELEASE_ENDPOINT %(middle_path, 'initiate')
        response = self._call(POST_METHOD, endpoint, body_json)
        pipeline_id = self._try_get('pipelineId', response)
        return TaskingObject(self._session, pipeline_id, lambda: self.__retrieve_analysis(pipeline_id, middle_path))


    def __retrieve_analysis(self, pipeline_id: str, middle_path: str) -> Union[str, list]:
        """Retrieves data from a server. In a case the data aren't ready to be retrieved, the TaskingException is raised. 
        In a case of succesfull fetch, the tuple of map_id and list of tile coordinates (zoom, x, y) are 

        Args:
            pipeline_id (str): Identified of a tasking object.
            middle_path (str)

        Raises:
            TaskingException: Tasking failed. No data can be retrieved.

        Returns:
            Union[str, list]: Tuple of map_id (unique identifie of the result) and list of tile coordinates (zoom, x_tile, y_tile).
        """
        try:
            endpoint = self.RELEASE_ENDPOINT %(middle_path, 'retrieve')
            body_json = {'pipelineId': pipeline_id}
            response = self._call(POST_METHOD, endpoint, body_json)
            map_id = self._try_get('mapId', response)
            tiles = self._try_get('tiles', response)
            return map_id, tiles
        except SpaceknowApiException as ex:
            if ex.error_type in [TaskingError.NON_EXISTENT_PIPELINE, TaskingError.PIPELINE_NOT_PROCESSED]:
                raise TaskingException(ex.error_type, ex.error_message) from ex
            raise
    

    def get_satelite_image(self, map_id: str, tile: Tuple[int, int, int]) -> Image.Image:
        """Retrieves satelite image, by map_id, tile, that were analysed earlier.

        Args:
            map_id (str): Unique identifier of analysis result.
            tile (Tuple[int, int, int]): Tile coordinates (zoom, x_tile, y_tile).

        Returns:
            Image.Image: Satelite image coresponding to give map_id, tile.
        """
        endpoint = self.GRID_IMAGERY_ENDPOINT %(map_id, tile[0], tile[1], tile[2])
        return self._get_image(endpoint)

    def get_detections(self, map_id: str, tile: Tuple[int,int,int]) -> list[Feature]:
        """Retrieves data results of cars analysis. 

        Args:
            map_id (str): [description]
            tile (Tuple[int,int,int]): [description]

        Returns:
            list[Feature]: List of features. Each feature contains geoemtrieas of specified count. Geometry represents found object (car).
        """
        endpoint = self.GRID_CARS_ENDPOINT %(map_id, tile[0], tile[1], tile[2])
        response = self._call(GET_METHOD, endpoint, json_body=None)
        return self.__parse_detections_to_list_of_features(response)


    def __parse_detections_to_list_of_features(self, detections: dict) -> list[Feature]:
        features = self._try_get('features', detections)
    
        geometry_strings = [self._try_get('geometry', f) for f in features]
        properties = [self._try_get('properties', f) for f in features]
        
        classes = [self._try_get('class',p) for p in properties]
        counts = [int(self._try_get('count',p)) for p in properties]
        geometries = [GeoJSON(g) for g in geometry_strings]

        return [Feature(item[0], item[1], item[2]) for item in zip(classes, counts, geometries)]
            





     







