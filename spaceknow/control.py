from spaceknow.api import TaskingObject
from spaceknow.errors import TaskingException
from spaceknow.models import TaskingStatus
from time import sleep
from typing import Callable


class TaskingManager:
    TASK_FAILED_ERROR = 'TASKING-FAILED'
    def __init__(self, logger: Callable[[str, int], None] = None) -> None:
        self.__logger = logger or (lambda s, i: None)

    def wait_untill_completed(self, taskingObject: TaskingObject):
        status, wait_in_seconds = taskingObject.get_status()
        if status in [TaskingStatus.PROCESSING, TaskingStatus.NEW]:
            self.__logger(status.name, wait_in_seconds)
            sleep(wait_in_seconds)
            return self.wait_untill_completed(taskingObject)
        elif status == TaskingStatus.FAILED:
            raise TaskingException(self.TASK_FAILED_ERROR,'Tasking failed unexpectedly.')
        self.__logger(status.name, wait_in_seconds)
        return taskingObject.retrieve_data()











