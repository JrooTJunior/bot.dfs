# -*- coding: utf-8 -*-
import os
import requests
from munch import munchify, unmunchify
from requests import HTTPError

from .exceptions import SfsJsonApiError, SfsApiError

BASE_URL = 'cabinet.sfs.gov.ua'
BASE_PATH = '/cabinet/public/api/exchange'


class SfsApiClient(object):
    def __init__(self, euscp, base_url=BASE_URL, base_path=BASE_PATH, ssl=True):
        self.euscp = euscp

        self.base_url = base_url
        self.base_path = base_path

        self.api_url = 'http{}://{}{}'.format(['', 's'][ssl], base_url, base_path)

        self.session = requests.Session()

    @staticmethod
    def _parse_response(response):
        try:
            response.raise_for_status()
        except HTTPError:
            try:
                data = response.json()
            except ValueError:
                raise SfsApiError(response)
            else:
                raise SfsJsonApiError(response, data)

        result = munchify(response.json())
        if result.status == u'OK':
            return result
        raise SfsJsonApiError(response, response.json())

    def report(self, data):
        response = self.session.post(
            self.api_url + '/report',
            json=unmunchify(data)
        )
        return self._parse_response(response)

    def kvt_by_id(self, encryptedId):
        response = self.session.post(
            self.api_url + '/kvt_by_id',
            data=encryptedId
        )

        return self._parse_response(response)

    def send_report(self, data, filename):
        data = self.euscp.encrypt(data)

        result = self.report([
            {'contentBase64': data, 'fname': filename}
        ])
        return result.id

    def send_report_from_file(self, file_path):
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            return self.send_report(f.read(), filename)

    def check_by_id(self, identifier):
        data = self.euscp.encrypt(bytes(identifier))
        return self.kvt_by_id(data)

    def extract_data(self, data):
        return self.euscp.decrypt(data)
