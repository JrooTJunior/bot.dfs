import json
import requests


class SfsApiError(Exception):
    def __init__(self, response):
        self.response = response  # type: requests.Response

    def __str__(self):
        return self.response.text


class SfsJsonApiError(SfsApiError):
    def __init__(self, response, data):
        super(SfsJsonApiError, self).__init__(response)

        self.response_data = data

        self.message = data.get('message', None)
        self.status = data.get('status', None)

    def __str__(self):
        return '{}: {} # {}'.format(self.status, self.message, json.dumps(self.response_data, ensure_ascii=False))
