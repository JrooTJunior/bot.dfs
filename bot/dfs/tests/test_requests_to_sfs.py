# -*- coding: utf-8 -*-
from unittest import TestCase
from bot.dfs.bridge.requests_db import RequestsDb
from bot.dfs.bridge.requests_to_sfs import RequestsToSfs


class TestRequestsToSfs(TestCase):
    """docstring for TestRequestsToSfs"""

    def setUp(self):
        self.edr_id = '14360570'
        self.ca_name = ''
        self.cert = ''
        self.r = RequestsToSfs()

    def test_sfs_check_request(self):
        qtDocs = self.r.sfs_check_request(self.edr_id)
        self.assertEqual(qtDocs, 0)

    def test_sfs_receive_request(self):
        docs = self.r.sfs_receive_request(self.edr_id, self.ca_name, self.cert)
        self.assertEqual(docs, None)

    def test_sfs_get_certificate_request(self):
        cert = self.r.sfs_get_certificate_request(self.ca_name)
        self.assertIsNotNone(cert)
