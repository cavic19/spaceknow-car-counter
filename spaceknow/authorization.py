from requests import Session
from spaceknow.errors import  AuthenticationException, UnexpectedResponseException
from spaceknow.models import Credentials

AUTH0_DOMAIN = 'https://spaceknow.auth0.com'

class AuthorizationService:
    """Service providing authorization via JWT"""
    DEFAULT_CONNECTION = 'Username-Password-Authentication'
    DEFAULT_GRANT_TYPE = 'password'
    DEFAULT_SCOPE = 'openid'

    ENDPOINT = '/oauth/ro'

    def __init__(self, client_id, session: Session = None):
        self.__client_id =  client_id
        self.__session = session or Session()

    def request_jwt(self, credentials: Credentials) -> str:
        """ Authenticates user with giver username and password and if successed returns jwt else throws AuthenticationException

        Args:
            username (str): User's name against which the authentication is done
            password (str): User's password against which the authentication is done]

        Returns:
            str: json web token
        """
        pass
        body_json = {
            'client_id': self.__client_id,
            'username': credentials.username,
            'password': credentials.password,
            'connection': self.DEFAULT_CONNECTION,
            'grant_type': self.DEFAULT_GRANT_TYPE,
            'scope': self.DEFAULT_SCOPE
        }
        url = AUTH0_DOMAIN + self.ENDPOINT
        response = self.__session.post(url=url, json=body_json)      
        try:
            return response.json()['id_token']
        except ValueError:
            raise UnexpectedResponseException(response)
        except KeyError:
            if 'error' in response.json():
                error_type = response.json()['error']
                error_message = response.json()['error_description']
                raise AuthenticationException(f'{error_type}: {error_message}.')
            else:
                raise UnexpectedResponseException(response)
    

