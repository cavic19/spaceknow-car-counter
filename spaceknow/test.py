from geojson import GeoJSON,Polygon
from datetime import datetime

from requests.sessions import Session
from models import Client
import authorization as au

# TESTING DATA
spaceKnowClientId = 'CP2hrNFIStlVEJUFAksfw3htqy9qwsP9'
login = "tomecek-backend-candidate@spaceknow.com"
password = "0d6bojq4wy2o"
testAirportPolygon = Polygon(
    [
        [
            (153.10478095093333,-27.390398450838056),
            (153.10668832863644,-27.391102659318708),
            (153.10534310906212,-27.393405862986185),
            (153.10364951776478,-27.392496065380755),
            (153.10478095093333,-27.390398450838056)            
        ]
    ])

startDateTime = datetime(2018,1,5,0,0,0)
endDateTime = datetime(2018,1,8,0,0,0)


client = Client(login, password)
session = Session()
authReq = au.Auth0JWTRequester(spaceKnowClientId,'https://spaceknow.auth0.com',session)

print(authReq.RequestAuthToken(client))