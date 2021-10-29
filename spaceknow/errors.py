from enum import Enum, auto
from requests import Response

class ApiError():   
    NOT_AUTHORIZED = 'NOT_AUTHORIZED'
    """The request is either not properly authorized or you do not have sufficient permissions"""
    
    INVALID_JWT = 'INVALID-JWT'
    """Provided authorization token is not valid"""

    NON_EXISTENT_ENDPOINT = 'NON-EXISTENT-ENDPOINT'
    """Requested path does not correspond to any API endpoint"""
    
    ACCESS_DENIED = 'ACCESS-DENIED'
    """Requesting client is not permitted to do perform an operation or access the resource"""

class TaskingError():
    NON_EXISTENT_PIPELINE = 'NON-EXISTENT-PIPELINE'
    """Pipeline with given ID was not found when processing your request"""

    PIPELINE_NOT_PROCESSED = 'PIPELINE-NOT-PROCESSED'
    """Pipeline has not been resolved yet"""

class AuthenticationException(Exception):
    def __init__(self, message: str):
        super().__init__(message)  

class AuthorizationException(Exception):
    def __init__(self, message: str):
        super().__init__(message)   

class UnexpectedResponseException(Exception):
    def __init__(self, actual_response_message):
        self.actual_response = actual_response_message
        super().__init__(actual_response_message)

class SpaceknowApiException(Exception):
    def __init__(self, error_type: str, error_message: str):
        super().__init__(f'{error_type}: {error_message}')
        self.error_type = error_type
        self.error_message = error_message

class NoEntriesException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(f'No entries were found. {msg}.')

class TaskingException(SpaceknowApiException):
    pass


