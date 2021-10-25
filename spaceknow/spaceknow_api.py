from requests import Session, Request, Response
from abc import ABC, abstractmethod
from json import JSONDecodeError
import asyncio
from typing import Callable, TypeVar, Generic, Tuple
from time import sleep

import requests

from spaceknow.models import Client
SPACEKNOW_API_DOMAIN = 'https://api.spaceknow.com'

class ApiException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TaskingHttpRSender:
    TASKING_ENDPOINT = '/tasking/get-status'
    def __init__(self, domainUrl: str, session: Session):
        self.__domainUrl = domainUrl
        self.__session = session 

    async def sendAsync(self, request: Request, onSucces: Callable[[str]]):  
        prepared_request = self.__session.prepare_request(request)
        response = self.__session.send(prepared_request)
        if 'application/json' in response.headers['Content-Type']:
            reponse_json = response.json() 
            pipelineId = reponse_json.get('pipelineId', None)
            self.__waitUntillResolved(pipelineId)
            return onSucces(pipelineId)


    def getStatus(self,pipelineId: str) -> Tuple[int,str]:
        body_json = {'pipelineId': pipelineId}
        response = self.__session.request('POST', self.__domainUrl + self.TASKING_ENDPOINT, json = body_json)
        response_json = response.json()
        if 'error' in response_json:
            raise ApiException(response_json['errorMessage']) 
        nextTry, status = self.__parseTaskingResponse(response_json)     

    def __waitUntillResolved(self, pipelineId: str): 
        nextTry, status = self.getStatus(pipelineId)
        if status == 'PROCESSING':
            sleep(nextTry)
            self.__waitUntillResolved(pipelineId)
        elif status == 'FAILED':
            raise ApiException(f"Task with pipelineId: {pipelineId} has failed.")      
        else:
            return

    def __parseTaskingResponse(self, response_json: dict) -> Tuple[int, str]:
        nextTry = int(response_json.get('nextTry', '0'))
        status = response_json.get('status','ERROR')
        return nextTry, status


from authorization import JWTRequester


class SpaceknowSession(Session):
    def __init__(self, authToken: str, jwtRequester: JWTRequester):
        self.__authToken = authToken
        self.headers = self.__generate_default_headers()
        self.__jwtRequester = jwtRequester
        #TODO: CHeck for authorization error and refgresh token when needed
        super().__init__()

    def __generate_default_headers(self) -> dict:
        return {'authorization': f'Bearer {self.__authToken}'}

    def refreshAuthToken(self,client: Client):
        authToken = self.__jwtRequester.RequestAuthToken(client)

    def request(self, method, url,
        params=None, data=None, headers=None, cookies=None, files=None,
        auth=None, timeout=None, allow_redirects=True, proxies=None,
        hooks=None, stream=None, verify=None, cert=None, json=None) -> Response:
        response = super().request(method,url,params,data,headers,cookies,files,auth,timeout,allow_redirects,proxies,hooks,stream,verify,cert,json)
        




from geojson import GeoJSON
from datetime import datetime

class RagnarAPI():
    IMAGERY_SEARCH_INITIATE_ENDPOINT = '/imagery/search/initiate'
    IMAGERY_SEARCH_RETRIEVE_ENDPOINT = '/imagery/search/retrieve'
    def __init__(self, session: SpaceknowSession):
       self.__session = session
       self.__taskingHttpSender = TaskingHttpRSender(SPACEKNOW_API_DOMAIN, session)
    
    async def initiateSearch(self, extent: GeoJSON, startDateTime: datetime, endDateTime: datetime, provider: str = 'gbdx', dataset: str = 'idaho-pansharpened'):
        request_body = {
            'provider': provider, 
            'dataset': dataset, 
            'startDatetime': startDateTime.strftime('%Y-%m-%d %H:%M:%S'), 
            'endDatetime': endDateTime.strftime('%Y-%m-%d %H:%M:%S'), 
            'extent': extent
            }  
        request = Request('POST', SPACEKNOW_API_DOMAIN + self.IMAGERY_SEARCH_INITIATE_ENDPOINT,json=request_body)
        return self.__taskingHttpSender.sendAsync(request, self.retrieveSearchResults)

    def retrieveSearchResults(self, pipeLineId):
        request_json = {'pipelineId': pipeLineId}
        response = self.__session.request('POST', SPACEKNOW_API_DOMAIN + self.IMAGERY_SEARCH_RETRIEVE_ENDPOINT,json=request_json)
        if 'application/json' in response.headers['Content-Type']:
            return self.__parseImagiryResultJson(response.json())
        else:
            #Raise exception something liek Invalid response .. .
            raise Exception()
    
    def __parseImagiryResultJson(self, jsonDict) -> dict:
        results = jsonDict.get('results', [])
        dtList = [datetime.strptime(r['datetime'],'%Y-%m-%d %H:%M:%S')for r in results]
        sceneIdList = [r['sceneId'] for r in results ]
        return dict(zip(sceneIdList,dtList))

