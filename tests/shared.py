from requests import Response

def generate_mocked_session_request(response_text: str):        
    def mocked_session_request(self, method, url,
        params=None, data=None, headers=None, cookies=None, files=None,
        auth=None, timeout=None, allow_redirects=True, proxies=None,
        hooks=None, stream=None, verify=None, cert=None, json=None):
        respone = Response()
        respone._content = bytes(response_text, 'utf-8')
        return respone
    return mocked_session_request