from PIL import Image 
from geojson import Polygon
from datetime import datetime

import geojson
from spaceknow.authorization import AuthorizationService
from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi, TaskingObject, TaskingStatus
from time import sleep
from spaceknow.interface import Spaceknow
from spaceknow.models import Credentials
import json
from geojson import Polygon
from datetime import datetime
#TESTING DATA
clientId = 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1'
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

sk = Spaceknow(Credentials(login,password), print)
query_obj = sk.analyse_on(testAirportPolygon,startDateTime, endDateTime)
query_obj.get_images()
print("Got images")

print(query_obj.count_cars())
print("Got cars")


























