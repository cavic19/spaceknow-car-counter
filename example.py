from geojson import Polygon
from datetime import datetime
from spaceknow.interface import SpaceknowCarsAnalyser

username = "tomecek-backend-candidate@spaceknow.com"
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

sk = SpaceknowCarsAnalyser(username, password, print)
query_obj = sk.analyse_on(testAirportPolygon,startDateTime, endDateTime)

print(query_obj.count_cars())
query_obj.get_images()[0].show()


























