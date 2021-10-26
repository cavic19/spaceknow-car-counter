from unittest .mock import patch
import random
from requests.models import Response
from spaceknow.api import AuthorizedSession, SpaceknowApi, TaskingObject, TaskingStatus
from requests.utils import default_headers
import unittest 
import json

from spaceknow.errors import SpaceknowApiException, UnexpectedResponseException

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


    def generate_mocked_session_request(response_text: str):        
        def mocked_session_request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
            respone = Response()
            respone._content = bytes(response_text, 'utf-8')
            return respone
        return mocked_session_request

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
        actual_response = ctx.exception.actual_response.text
        self.assertEqual(expected_response, actual_response)



# class TestTaskingObject(unittest.TestCase):
#     PIPELINE_ID = '123456789'

#     def mocked_AuthorizedSession_call_sends_vali_tasking_status(self, method, api_endpoint, json_body):
#         response = Response()
#         content_str = '{"status": "'+  random.choice(list(TaskingStatus)).name  +'", "'+ str(random.randint(1,15)) +'": 15}'
#         response._content = bytes(content_str, 'utf-8')
#         return response
    
#     @patch('spaceknow.api.SpaceknowApi.call', mocked_AuthorizedSession_call_sends_vali_tasking_status)
#     def test_get_status(self):
#         session = AuthorizedSession('someToken')
#         taskObject = TaskingObject(session, self.PIPELINE_ID, None)

#         status, nexTry = taskObject.get_status()
#         self.assertEqual(status, 'dasd')
    



