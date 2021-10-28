from spaceknow.api import TaskingObject
from spaceknow.errors import TaskingException
from spaceknow.models import TaskingStatus
from time import sleep
from typing import Callable


class TaskingManager:
    """Controls execution of TaskingObjects."""
    TASK_FAILED_ERROR = 'TASKING-FAILED'
    def __init__(self, logger: Callable[[str, int], None] = None) -> None:
        """
        Args:
            logger (Callable[[str, int], None]): Logs status of a TaskingObject (status: str, time_untill_next _tep: int). Defaults to None.
        """
        self.__logger = logger or (lambda s, i: None)

    def wait_untill_completed(self, tasking_object: TaskingObject):
        """Waits untill the Tasking procedure is finished and returns the result

        Args:
            tasking_object (TaskingObject): [description]

        Raises:
            TaskingException: [description]

        Returns:
            Iterable: [description]
        """
        status, wait_in_seconds = tasking_object.get_status()
        if status in [TaskingStatus.PROCESSING, TaskingStatus.NEW]:
            self.__logger(status.name, wait_in_seconds)
            sleep(wait_in_seconds)
            return self.wait_untill_completed(tasking_object)
        elif status == TaskingStatus.FAILED:
            raise TaskingException(self.TASK_FAILED_ERROR,'Tasking failed unexpectedly.')
        self.__logger(status.name, wait_in_seconds)
        return tasking_object.retrieve_data()











