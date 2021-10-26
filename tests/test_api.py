from unittest .mock import patch
from spaceknow.api import AuthorizedSession
from requests.utils import default_headers
import unittest 


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

