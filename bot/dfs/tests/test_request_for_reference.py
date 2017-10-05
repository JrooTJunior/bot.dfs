# -*- coding: utf-8 -*-
from gevent import monkey, event

monkey.patch_all()

import uuid
import unittest
import datetime
from gevent.queue import Queue
from mock import patch, MagicMock
from time import sleep
from munch import munchify
from restkit.errors import Unauthorized, RequestFailed, ResourceError

from bot.dfs.bridge.request_for_reference import RequestForReference
from utils import custom_sleep
from bot.dfs.bridge.sleep_change_value import APIRateController


class TestRequestForReferenceWorker(unittest.TestCase):
    def setUp(self):
        self.sleep_change_value = APIRateController()
        self.client = MagicMock()
        self.reference_queue = Queue(10)
        self.sna = event.Event()
        self.sna.set()
        self.worker = RequestForReference.spawn(self.client, self.reference_queue, self.sna, self.sleep_change_value)

    def tearDown(self):
        self.worker.shutdown()
        del self.worker

    def test_init(self):
        self.assertGreater(datetime.datetime.now().isoformat(), self.worker.start_time.isoformat())
        self.assertEqual(self.worker.tenders_sync_client, self.client)
        self.assertEqual(self.worker.reference_queue, self.reference_queue)
        self.assertEqual(self.worker.services_not_available, self.sna)
        self.assertEqual(self.worker.sleep_change_value.time_between_requests, 0)
        self.assertEqual(self.worker.delay, 15)
        self.assertEqual(self.worker.exit, False)

    # @patch('gevent.sleep')
    # def test_worker(self, gevent_sleep):
    #     gevent_sleep.side_effect = custom_sleep
    #
    #     request_ids = {'req1': {'edr_id': '14360570'}, 'req2': {'edr_id': '14360570'}}
    #
    #     for request_id in request_ids:
    #         print(self.reference_queue.peek())
    #         self.assertEqual(self.reference_queue.get(), (request_id)
