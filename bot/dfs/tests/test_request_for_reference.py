# -*- coding: utf-8 -*-
from gevent import monkey, event

monkey.patch_all()

import datetime
from gevent.queue import Queue
from base import BaseServersTest
from mock import patch, MagicMock
from time import sleep

from bot.dfs.bridge.request_for_reference import RequestForReference
from bot.dfs.bridge.sleep_change_value import APIRateController
from bot.dfs.bridge.requests_db import RequestsDb
from bot.dfs.bridge.requests_to_sfs import RequestsToSfs
from utils import custom_sleep


class TestRequestForReferenceWorker(BaseServersTest):
    def setUp(self):
        super(TestRequestForReferenceWorker, self).setUp()
        self.sleep_change_value = APIRateController()
        self.request_db = RequestsDb(self.redis)
        self.request_to_sfs = RequestsToSfs()
        self.request_ids = {'req1': {'edr_id': '14360570'}, 'req2': {'edr_id': '0013823'}}
        for key, value in self.request_ids.items():
            self.request_db.add_sfs_request(key, value)
        self.reference_queue = Queue(10)
        self.sna = event.Event()
        self.sna.set()
        self.worker = RequestForReference.spawn(self.reference_queue, self.request_to_sfs, self.request_db, self.sna,
                                                self.sleep_change_value)

    def tearDown(self):
        self.redis.flushall()
        super(TestRequestForReferenceWorker, self).tearDown()

    def test_init(self):
        self.assertGreater(datetime.datetime.now().isoformat(), self.worker.start_time.isoformat())
        self.assertEqual(self.worker.reference_queue, self.reference_queue)
        self.assertEqual(self.worker.request_to_sfs, self.request_to_sfs)
        self.assertEqual(self.worker.request_db, self.request_db)
        self.assertEqual(self.worker.services_not_available, self.sna)
        self.assertEqual(self.worker.sleep_change_value.time_between_requests, 0)
        self.assertEqual(self.worker.delay, 15)
        self.assertEqual(self.worker.exit, False)

    @patch('gevent.sleep')
    def test_worker(self, gevent_sleep):
        gevent_sleep.side_effect = custom_sleep
        self.assertEqual(self.reference_queue.qsize(), 0)
