# -*- coding: utf-8 -*-
from gevent import monkey, event

monkey.patch_all()

import datetime
from gevent.queue import Queue
from base import BaseServersTest
from mock import patch, MagicMock

from bot.dfs.bridge.request_for_reference import RequestForReference, soap_to_dict
from bot.dfs.bridge.sleep_change_value import APIRateController
from bot.dfs.bridge.requests_db import RequestsDb
from utils import custom_sleep
from zeep import Client, helpers


class TestRequestForReferenceWorker(BaseServersTest):
    def setUp(self):
        super(TestRequestForReferenceWorker, self).setUp()
        self.sleep_change_value = APIRateController()
        self.dfs_client = Client('http://obmen.sfs.gov.ua/SwinEd.asmx?WSDL')
        self.request_db = RequestsDb(self.redis)
        self.request_ids = {'req1': {'edr_id': '14360570'}, 'req2': {'edr_id': '14360570'}}
        for key, value in self.request_ids.items():
            self.request_db.add_dfs_request(key, value)
        self.reference_queue = Queue(10)
        self.sna = event.Event()
        self.sna.set()
        self.worker = RequestForReference.spawn(self.dfs_client, self.reference_queue, self.request_db, self.sna,
                                                self.sleep_change_value)

    def tearDown(self):
        super(TestRequestForReferenceWorker, self).tearDown()

    def test_init(self):
        self.assertGreater(datetime.datetime.now().isoformat(), self.worker.start_time.isoformat())
        self.assertEqual(self.worker.dfs_client, self.dfs_client)
        self.assertEqual(self.worker.reference_queue, self.reference_queue)
        self.assertEqual(self.worker.request_db, self.request_db)
        self.assertEqual(self.worker.services_not_available, self.sna)
        self.assertEqual(self.worker.sleep_change_value.time_between_requests, 0)
        self.assertEqual(self.worker.delay, 15)
        self.assertEqual(self.worker.exit, False)

    @patch('gevent.sleep')
    def test_dfs_checker(self, gevent_sleep):
        gevent_sleep.side_effect = custom_sleep
        self.worker.request_ids = self.request_ids
        for request_id, request_data in self.worker.request_ids.items():
            edr_id = request_data['edr_id']
            dept_id = 1
            depts_proc = 1
            ca_name = ""
            cert = ""
            dfs_receive = self.dfs_client.service.Receive(recipientEDRPOU=edr_id,
                                                          recipientDept=dept_id,
                                                          procAllDepts=depts_proc,
                                                          caName=ca_name,
                                                          cert=cert)
            dfs_receive_to_dict = soap_to_dict(dfs_receive)
            dfs_received_docs = dfs_receive_to_dict['docs']
            self.assertEqual(self.reference_queue.get(), (request_id, dfs_received_docs))
