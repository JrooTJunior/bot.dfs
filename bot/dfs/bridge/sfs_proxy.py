from gevent import monkey

monkey.patch_all()
from zeep import Client
from requests import post


class SignProxy(object):
    def __init__(self, url, port):
        self.url = url
        self.port = port

    def sign(self, content):
        return post(self.url, json={"Buffer": content,
                                    "Id": "sign1",
                                    "BufferInB64": "dGVzdCBidWZmZXIt8uXx8g==",
                                    "BufferEncoding": "windows-1251"})
