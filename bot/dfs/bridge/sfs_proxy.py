from gevent import monkey
monkey.patch_all()
from zeep import Client
from requests import post
import base64


class SignProxy(object):

    def __init__(self, url, port):
        self.url = url
        self.port = port

    def sign(self, content):
        return post(self.url, json={"Buffer": content,
                                    "Id": "sign1",
                                    "BufferInB64": "dGVzdCBidWZmZXIt8uXx8g==",
                                    "BufferEncoding": "windows-1251"})


class SfsProxy(object):
    """docstring for SfsProxy"""

    def __init__(self, url):
        super(SfsProxy, self).__init__()
        self.url = url

    def send(self, content):
        client = Client(self.url)
        return client.service.sign(content)
