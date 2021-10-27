from unittest.mock import patch
import unittest
from requests import Response
from spaceknow.api import AuthorizedSession
from spaceknow.control import TaskingManager
from spaceknow.api import TaskingObject
from spaceknow.errors import TaskingError, TaskingException
from tests.shared import generate_mocked_session_request
import random as rnd


__CALLED = False
def simulate_tasking_requests(self, method, url,
    params=None, data=None, headers=None, cookies=None, files=None,
    auth=None, timeout=None, allow_redirects=True, proxies=None,
    hooks=None, stream=None, verify=None, cert=None, json=None):
    response = Response()
    global __CALLED
    SLEEP_TIME = 1
    if not __CALLED:
        __CALLED = True
        response._content = bytes('{"status": "PROCESSING" , \
            "nextTry": "'+ str(SLEEP_TIME) +'"}', 'utf-8')
    else:
        response._content = b'{"status": "RESOLVED"}'
    return response



class TestTaskingManager(unittest.TestCase):

    def test_wait_untill_completed_valid_tasking_responses_should_pass(self):
        with patch('spaceknow.api.AuthorizedSession.request',simulate_tasking_requests):
            session = AuthorizedSession('valid token')
            taskingMgr = TaskingManager()
            expected =  {'SUCCESS': 'YES'}
            taskObj = TaskingObject(session, 'valid-id', lambda: expected)
            actual = taskingMgr.wait_untill_completed(taskObj)

        self.assertDictEqual(expected,actual)

    @patch('requests.Session.request', generate_mocked_session_request('{"status": "FAILED"}'))
    def test_wait_untill_completed_fail_tasking_response_should_throw(self):
            session = AuthorizedSession('valid token')
            taskingMgr = TaskingManager()
            taskObj = TaskingObject(session, 'valid-id', None)

            with self.assertRaises(TaskingException) as ctx:
                taskingMgr.wait_untill_completed(taskObj)
            self.assertEqual(ctx.exception.error_type, TaskingManager.TASK_FAILED_ERROR)

    @patch('spaceknow.api.AuthorizedSession.request',simulate_tasking_requests)
    def test_wait_untill_completed_logging(self):
        session = AuthorizedSession('valid token')
        taskObj = TaskingObject(session, 'valid-id', lambda: {})
        expected_text = 'PROCESSINGRESOLVED'
        actual_text = ''
        def logger(text: str, num: int):
            nonlocal actual_text
            actual_text += text
        taskingMgr = TaskingManager(logger)

        taskingMgr.wait_untill_completed(taskObj)

        self.assertEqual(expected_text, actual_text)

