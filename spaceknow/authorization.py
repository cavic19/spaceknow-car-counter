from requests import Session
from abc import ABC, abstractmethod
from models import Client



class Auth0Exception(Exception):
    def __init__(self, message):
        super().__init__(message)


class JWTRequester(ABC):
    @abstractmethod
    def RequestAuthToken(self,client: Client) -> str:
        pass

class Auth0JWTRequester(JWTRequester):
    AUTH0_API_ENDPOINT = '/oauth/token'
    
    def __init__(self,clientId: str, auth0Domain: str, session: Session = None):
        self.__clientId = clientId
        self.__auth0Domain = auth0Domain
        self.__session = session if session is not None else Session()
    
    def RequestAuthToken(self, client: Client) -> str:
        response = self.__session.request(
            'POST',
            url=self.__buildRequestUrl(), 
            json=self.__buildRequestBody(client))
        if 'application/json' in response.headers['Content-Type']:
            response_json = response.json()
            if 'error' in response_json:
                self.__handleErrors(response_json['error'], response_json['error_description'])
            return response_json['id_token']
            
    def __buildRequestUrl(self) -> str:
        return f"{self.__auth0Domain}{self.AUTH0_API_ENDPOINT}"

    def __buildRequestBody(self, user: Client) -> dict:
        return {
            'client_id': self.__clientId,
            'username': user.username,
            'password': user.password,
            'connection': 'Username-Password-Authentication',
            'grant_type': 'password',
            'scope': 'openid'
        }
    def __handleErrors(self, errorType:str,errorMessage:str):
        raise Auth0Exception(f'{errorType}: {errorMessage}.')

