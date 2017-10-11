# -*- coding: utf-8 -*-
import requests


class ProxyClient(object):
    """Base class for making requests to Proxy server"""

    def __init__(self, host, user, password, timeout=None, port=6547, version=1.0):
        self.session = requests.Session()
        self.user = user
        self.password = password
        self.verify_url = '{host}:{port}/api/{version}/verify'.format(host=host, port=port, version=version)
        self.health_url = '{host}:{port}/api/{version}/health'.format(host=host, port=port, version=version)
        self.timeout = timeout

    def verify(self, param, code, headers):
        """Send request to Proxy server to verify EDRPOU code"""
        url = '{url}?{param}={code}'.format(url=self.verify_url, param=param, code=code)
        response = self.session.get(url=url, auth=(self.user, self.password), timeout=self.timeout, headers=headers)
        return response

    def health(self, sandbox_mode):
        """Send request to the Proxy server to get whether its active"""
        response = self.session.get(url=self.health_url, auth=(self.user, self.password),
                                    headers={"sandbox-mode": sandbox_mode}, timeout=self.timeout)
        if response.status_code == 200:
            return response
        raise requests.RequestException("{} {} {}".format(response.url, response.status_code, response.reason),
                                        response=response)
