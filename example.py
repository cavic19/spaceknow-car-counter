from geojson import Polygon
from datetime import datetime
from spaceknow.authorization import AuthorizationService
from spaceknow.api import AuthorizedSession, KrakenApi, RagnarApi, TaskingObject, TaskingStatus
from time import sleep


# TESTING DATA
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

authService = AuthorizationService(clientId)



print('Retrieving token')
token = authService.request_jwt(login,password)
print('Token: ', token)

session = AuthorizedSession(token)
ragnarApi = RagnarApi(session)

print('Initiating search')
ragnar_tast_obj = ragnarApi.initiate_search(testAirportPolygon,startDateTime,endDateTime)
status, nextTry = ragnar_tast_obj.get_status()
while status == TaskingStatus.PROCESSING:
    print(status)
    sleep(nextTry)
    status, nextTry = ragnar_tast_obj.get_status()

print('Ragnar finished with status: ', status.name)
data = ragnar_tast_obj.retrieve_data()
print(data)


scene_ids = list(data.keys())
krakenApi = KrakenApi(session)
print('Initiating kraken analysis')
kraken_task_obj = krakenApi.initiate_car_analysis(testAirportPolygon,scene_ids[0])
status, nextTry = kraken_task_obj.get_status()
while status == TaskingStatus.PROCESSING:
    print(status)
    sleep(nextTry)
    status, nextTry = ragnar_tast_obj.get_status()
print('Kraken finished with status: ', status.name)
kraken_data = kraken_task_obj.retrieve_data()
print(kraken_data)
print('Finished')
