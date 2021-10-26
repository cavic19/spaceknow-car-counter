from geojson import Polygon
from datetime import datetime
from spaceknow.authorization import AuthorizationService
from spaceknow.api import AuthorizedSession, RagnarApi, TaskingObject, TaskingStatus
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
taskObject = ragnarApi.initiate_search(testAirportPolygon,startDateTime,endDateTime)
status, nextTry = taskObject.get_status()
while status == TaskingStatus.PROCESSING:
    print(status)
    sleep(nextTry)
    status, nextTry = taskObject.get_status()

print('Procedure finisged with status: ', status.name)
data = taskObject.retrieve_data()

print(data)
print('Finished')



