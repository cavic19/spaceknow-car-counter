from unittest.mock import patch
import unittest 
from spaceknow.authorization import AuthorizationService, UnexpectedResponseException
import spaceknow.errors as errors
from requests import Response
from spaceknow.models import Credentials

VALID_USERNAME = 'valid-username'
VALID_PASSWORD = 'valid-password'
VALID_CLIENTID = '123456789client'
VALID_TOKEN = '123456789'

ERROR_TYPE = 'some-error'
ERROR_DESCRIPTION = 'Some error description.'


def mocked_request_post_with_valid_response(self, url, data=None, json=None, **kwargs):
    username = json['username']
    password = json['password']
    response = Response()
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        response._content = bytes('{"id_token": "' + VALID_TOKEN + '"}', 'utf-8')
    else:
        response._content = bytes('{"error": "'   + ERROR_TYPE +'", "error_description": "'+ ERROR_DESCRIPTION + '"}','utf-8')
    return response

def mocked_request_post_with_invalid_response(self, url, data=None, json=None, **kwargs):
    response = Response()
    response._content = b'Normal text, not json parsable.'
    return response


class TestAuthorization(unittest.TestCase):
    @patch('requests.Session.post', mocked_request_post_with_valid_response)
    def test_valid_credentials_should_equal(self):
        authService = AuthorizationService(VALID_CLIENTID)
        token = authService.request_jwt(Credentials(VALID_USERNAME, VALID_PASSWORD))
        
        self.assertEquals(token, VALID_TOKEN)

    @patch('requests.Session.post', mocked_request_post_with_valid_response)
    def test_invalid_credentials_should_throw_authenticationException(self):
        authService = AuthorizationService(VALID_CLIENTID)
        with  self.assertRaises(errors.AuthenticationException) as ctx:
            authService.request_jwt(Credentials('invalid-username','invalid-password'))
        self.assertTrue(ERROR_TYPE in str(ctx.exception) and ERROR_DESCRIPTION in str(ctx.exception))

    @patch('requests.Session.post', mocked_request_post_with_invalid_response)
    def test_not_json_response_should_throw_unexpectetException(self):
        authService = AuthorizationService(VALID_CLIENTID)
        with self.assertRaises(UnexpectedResponseException):
            authService.request_jwt(Credentials(VALID_USERNAME, VALID_PASSWORD))