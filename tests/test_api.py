from datetime import datetime
from unittest .mock import patch
import random
from requests.models import Response
from spaceknow.api import AuthorizedSession, RagnarApi, SpaceknowApi, TaskingObject, TaskingStatus
from requests.utils import default_headers
import unittest 
import json
import geojson
from shared import generate_mocked_session_request

from spaceknow.errors import SpaceknowApiException, TaskingException, UnexpectedResponseException

class TestAuthorizedSession(unittest.TestCase):
    VALID_TOKEN = 'abcdefghijklmnopqrzstuv.123456789'
    def test_on_creation_has_proper_headers(self):
        session = AuthorizedSession(self.VALID_TOKEN)
        expectedHeader = default_headers()
        expectedHeader.update({'authorization': f'Bearer {self.VALID_TOKEN}'})
        
        actualHeader = session.headers
        
        self.assertDictEqual(dict(expectedHeader), dict(actualHeader))

    def test_update_auth_token_should_change_header(self):
        session = AuthorizedSession(self.VALID_TOKEN)
        newToken = self.VALID_TOKEN + 'NEW'
        expectedHeader = default_headers()
        expectedHeader.update({'authorization': f'Bearer {newToken}'})
        
        session.update_auth_token(newToken)
        actualHeader = session.headers

        self.assertDictEqual(dict(expectedHeader), dict(actualHeader))



class TestSpaceknowApi(unittest.TestCase):
    VALID_RESPONSE_BODY = '{"type": "json", "color": "red", "name": "John"}'
    AUTH_ERROR_RESPONSE_BODY = '{"error": "NOT-AUTHORIZED", "errorMessage": "You are not authorized."}'
    INVALID_RESPONSE_BODY = 'INVALID RESPONSE NOT JSON PARSABLE'


    @patch('requests.Session.request', generate_mocked_session_request(VALID_RESPONSE_BODY))
    def test_call_valid_response(self):
        session = AuthorizedSession('valid-token')
        spaceknowApi = SpaceknowApi(session)
        expected = json.loads(self.VALID_RESPONSE_BODY)
        
        actual = spaceknowApi.call('POST','/endpoint', {'test': '123456'})
        
        self.assertDictEqual(expected, actual)

    @patch('requests.Session.request', generate_mocked_session_request(AUTH_ERROR_RESPONSE_BODY))
    def test_call_failed_response_should_throw_SpaceknowException(self ):
        session = AuthorizedSession('valid-token')
        spaceknowApi = SpaceknowApi(session)

        with self.assertRaises(SpaceknowApiException) as ctx:
            spaceknowApi.call('POST','/endpoint', {'test': '123456'})
        expected_error_type = ctx.exception.error_type
        actual_error_type = json.loads(self.AUTH_ERROR_RESPONSE_BODY)['error']
        
        self.assertEqual(expected_error_type, actual_error_type)

    @patch('requests.Session.request', generate_mocked_session_request(INVALID_RESPONSE_BODY))
    def test_call_not_json_response(self):
        session = AuthorizedSession('valid-token')
        spaceknowApi = SpaceknowApi(session)
        
        with self.assertRaises(UnexpectedResponseException) as ctx:
            spaceknowApi.call('POST', '/endpoint', {'test': '123456'})
        
        expected_response = self.INVALID_RESPONSE_BODY
        actual_response = ctx.exception.actual_response
        self.assertEqual(expected_response, actual_response)



class TestTaskingObject(unittest.TestCase):
    PIPELINE_ID = '123456789'
    TASKIN_ERROR_TEXT = '{"error": "NON-EXISTENT-PIPELINE", "errorMessage": "Pipeline is not existent!"}'
    def mocked_call_valid_response(self, method, api_endpoint, json_body):
        return {
            'status': random.choice([s.name for s in list(TaskingStatus)]),
            'nextTry': str(random.randint(1, 15))
        }
   
    @patch('spaceknow.api.SpaceknowApi.call', mocked_call_valid_response)
    def test_get_status_valid_response(self):
        session = AuthorizedSession('someToken')
        task_object = TaskingObject(session, self.PIPELINE_ID, None)

        status, nexTry = task_object.get_status()
        self.assertIn(status, list(TaskingStatus))

    @patch('requests.Session.request', generate_mocked_session_request(TASKIN_ERROR_TEXT))
    def test_get_status_taskin_error(self):
        session = AuthorizedSession('someToken')
        task_object = TaskingObject(session, self.PIPELINE_ID, None)

        with self.assertRaises(TaskingException):
            status, nexTry = task_object.get_status()

    @patch('requests.Session.request', generate_mocked_session_request(TestSpaceknowApi.AUTH_ERROR_RESPONSE_BODY))
    def test_get_status_spaceknowException_should_throw(self):
        session = AuthorizedSession('someToken')
        task_object = TaskingObject(session, self.PIPELINE_ID, None)

        with self.assertRaises(SpaceknowApiException) as ctx:
            task_object.get_status()
        self.assertNotIsInstance(ctx.exception, TaskingException)

class TestRagnarApi(unittest.TestCase):
    INVALID_RESPONSE = '{"key": "unexpected", "anotherKey": "unexpected too"}'
    VALID_INITIATE_RESPONSE = '{"pipelineId": "123456789abc"}'
    VALID_RETRIEVE_RESPONSE = '{"results": [{"sceneId": "123456789abc", "datetime":"2021-10-26 22:34:42"}]}'
    
    def test_initiate_search_of_point_should_throw(self):
        point = geojson.Point((125,125))
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)

        with self.assertRaises(ValueError):
            ragnar.initiate_search(point,None,None)

    @patch('requests.Session.request', generate_mocked_session_request(VALID_INITIATE_RESPONSE))
    def test_initiate_search_of_polygon_should_pass(self):
        polygon = geojson.Polygon([[(1,1), (2,2), (3,3), (1,1)]])
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)
        fromDate = datetime(2021,10,26)
        toDate = datetime(2021,10,27)

        ragnar.initiate_search(polygon,fromDate,toDate)     


    def test_iitiate_search_wrong_datetime_arguments_should_throw(self):
        polygon = geojson.Polygon([[(1,1), (2,2), (3,3), (1,1)]])
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)
        fromDate = datetime(2021,10,27)
        toDate = datetime(2021,10,26)
        with self.assertRaises(ValueError):
            ragnar.initiate_search(polygon, fromDate, toDate)

    @patch('requests.Session.request', generate_mocked_session_request(VALID_RETRIEVE_RESPONSE))
    def test_retrieve_results_should_equal(self):
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)
        expectedResponse = json.loads(self.VALID_RETRIEVE_RESPONSE)['results'][0]
        
        
        expectedResult = [expectedResponse['sceneId']]
        actualResult = ragnar.retrieve_results('valid-pipeline-id')

        self.assertListEqual(expectedResult, actualResult)

    @patch('requests.Session.request', generate_mocked_session_request(INVALID_RESPONSE))
    def test_retrieve_results_invalid_response_should_throw(self):
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)

        with self.assertRaises(UnexpectedResponseException):
            ragnar.retrieve_results('valid-pipeline')

    @patch('requests.Session.request', generate_mocked_session_request(TestTaskingObject.TASKIN_ERROR_TEXT))
    def test_retrieve_results_tasking_error_should_throw(self):
        session = AuthorizedSession('valid-token')
        ragnar = RagnarApi(session)

        with self.assertRaises(TaskingException):
            ragnar.retrieve_results('pipeline-id')        

    @patch('requests.Session.request', generate_mocked_session_request(TestSpaceknowApi.AUTH_ERROR_RESPONSE_BODY))
    def test_retrieve_results_spaceknowException_should_throw(self):
        session = AuthorizedSession('someToken')
        ragnar = RagnarApi(session)

        with self.assertRaises(SpaceknowApiException) as ctx:
            ragnar.retrieve_results('pipeline-id')   
        self.assertNotIsInstance(ctx.exception, TaskingException)

class TestKrakenApi(unittest.TestCase):
    def test_get_image_when_wrong_map_id_is_presented_should_throw_error(self):
        #např pokus si ziskato brazky z analyzy aut
        pass