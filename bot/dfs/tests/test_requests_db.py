# -*- coding: utf-8 -*-
from base import BaseServersTest
from bot.dfs.bridge.requests_db import RequestsDb


class TestRequestsDb(BaseServersTest):
    """docstring for TestRequestsDb"""

    def setUp(self):
        super(TestRequestsDb, self).setUp()
        self.requests_db = RequestsDb(self.redis)   

    def tearDown(self):
        pass

    def test_add_request(self):
        req_data = {"status": "pending", "tender_id": "111", "edr_id": "222"}
        self.requests_db.add_sfs_request("1", req_data)
        self.assertEqual(self.redis.hgetall("requests:1"), req_data)
