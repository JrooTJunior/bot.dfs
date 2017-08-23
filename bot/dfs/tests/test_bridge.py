# -*- coding: utf-8 -*-
import os

from gevent import killall
from mock import patch, MagicMock
from bot.dfs.client import DocServiceClient, ProxyClient
from bot.dfs.bridge.bridge import EdrDataBridge
from base import BaseServersTest, config
from utils import custom_sleep, AlmostAlwaysTrue
from openprocurement_client.client import TendersClientSync, TendersClient
from requests import RequestException
from restkit import RequestError


class TestBridgeWorker(BaseServersTest):
    def test_init(self):
        # import pdb;pdb.set_trace()
        self.worker = EdrDataBridge(config)
        self.assertEqual(self.worker.delay, config['main']['delay'])
        self.assertEqual(self.worker.sleep_change_value.time_between_requests, 0)
        self.assertTrue(isinstance(self.worker.tenders_sync_client, TendersClientSync))
        self.assertTrue(isinstance(self.worker.client, TendersClient))
        self.assertFalse(self.worker.initialization_event.is_set())
        self.assertEqual(self.worker.process_tracker.processing_items, {})
        self.assertEqual(self.worker.db._backend, "redis")
        self.assertEqual(self.worker.db._db_name, 0)
        self.assertEqual(self.worker.db._port, "16379")
        self.assertEqual(self.worker.db._host, "127.0.0.1")

    @patch('bot.dfs.bridge.bridge.TendersClientSync')
    @patch('bot.dfs.bridge.bridge.TendersClient')
    def test_tender_sync_clients(self, sync_client, client):
        self.worker = EdrDataBridge(config)
        self.assertEqual(client.call_args[0], ('',))
        self.assertEqual(client.call_args[1], {'host_url': config['main']['public_tenders_api_server'],
                                               'api_version': config['main']['tenders_api_version']})

        self.assertEqual(sync_client.call_args[0], (config['main']['api_token'],))
        self.assertEqual(sync_client.call_args[1],
                         {'host_url': config['main']['tenders_api_server'],
                          'api_version': config['main']['tenders_api_version']})

    def test_start_jobs(self):
        self.worker = EdrDataBridge(config)

        scanner, filter_tender, edr_handler, upload_file_to_doc_service, upload_file_to_tender = \
            [MagicMock(return_value=i) for i in range(5)]
        self.worker.scanner = scanner
        self.worker.filter_tender = filter_tender

        self.worker._start_jobs()
        # check that all jobs were started
        self.assertTrue(scanner.called)
        self.assertTrue(filter_tender.called)

        self.assertEqual(self.worker.jobs['scanner'], 0)
        self.assertEqual(self.worker.jobs['filter_tender'], 1)

    @patch('gevent.sleep')
    def test_bridge_run(self, sleep):
        self.worker = EdrDataBridge(config)
        scanner, filter_tender = [MagicMock() for i in range(2)]
        self.worker.scanner = scanner
        self.worker.filter_tender = filter_tender
        self.worker.check_and_revive_jobs = MagicMock()
        with patch('__builtin__.True', AlmostAlwaysTrue(10)):
            self.worker.run()
        self.assertEqual(self.worker.scanner.call_count, 1)
        self.assertEqual(self.worker.filter_tender.call_count, 1)

    def test_openprocurement_api_failure(self):
        self.worker = EdrDataBridge(config)
        self.api_server.stop()
        with self.assertRaises(RequestError):
            self.worker.check_openprocurement_api()
        self.api_server.start()
        self.assertTrue(self.worker.check_openprocurement_api())

    def test_openprocurement_api_mock(self):
        self.worker = EdrDataBridge(config)
        self.worker.client = MagicMock(head=MagicMock(side_effect=RequestError()))
        with self.assertRaises(RequestError):
            self.worker.check_openprocurement_api()
        self.worker.client = MagicMock()
        self.assertTrue(self.worker.check_openprocurement_api())

    def test_check_services(self):
        t = os.environ.get("SANDBOX_MODE", "False")
        os.environ["SANDBOX_MODE"] = "True"
        self.worker = EdrDataBridge(config)
        self.worker.services_not_available = MagicMock(set=MagicMock(), clear=MagicMock())
        self.api_server.stop()
        self.worker.check_services()
        self.assertTrue(self.worker.services_not_available.clear.called)
        self.api_server.start()
        self.worker.check_services()
        self.assertTrue(self.worker.services_not_available.set.called)
        os.environ["SANDBOX_MODE"] = t

    def test_check_services_mock(self):
        self.worker = EdrDataBridge(config)
        self.worker.check_openprocurement_api = MagicMock()
        self.worker.set_wake_up = MagicMock()
        self.worker.set_sleep = MagicMock()
        self.worker.check_services()
        self.assertTrue(self.worker.set_wake_up.called)
        self.worker.check_openprocurement_api = MagicMock(side_effect=RequestError())
        self.worker.check_services()
        self.assertTrue(self.worker.set_sleep.called)

    @patch("gevent.sleep")
    def test_check_log(self, gevent_sleep):
        gevent_sleep = custom_sleep
        self.worker = EdrDataBridge(config)
        self.worker.edrpou_codes_queue = MagicMock(qsize=MagicMock(side_effect=Exception()))
        self.worker.check_services = MagicMock(return_value=True)
        self.worker.run()
        self.assertTrue(self.worker.edrpou_codes_queue.qsize.called)

    @patch("gevent.sleep")
    def test_launch(self, gevent_sleep):
        self.worker = EdrDataBridge(config)
        with patch('__builtin__.True', AlmostAlwaysTrue(10)):
            self.worker.launch()
        gevent_sleep.assert_called_once()

    @patch("gevent.sleep")
    def test_launch_unavailable(self, gevent_sleep):
        self.worker = EdrDataBridge(config)
        self.worker.all_available = MagicMock(return_value=False)
        with patch('__builtin__.True', AlmostAlwaysTrue()):
            self.worker.launch()
        gevent_sleep.assert_called_once()

    def test_revive_job(self):
        self.worker = EdrDataBridge(config)
        self.worker._start_jobs()
        self.assertEqual(self.worker.jobs['scanner'].dead, False)
        killall(self.worker.jobs.values(), timeout=1)
        self.assertEqual(self.worker.jobs['scanner'].dead, True)
        self.worker.revive_job('scanner')
        self.assertEqual(self.worker.jobs['scanner'].dead, False)
        killall(self.worker.jobs.values())

    def test_check_and_revive_jobs_mock(self):
        self.worker = EdrDataBridge(config)
        self.worker._start_jobs()
        self.assertEqual(self.worker.jobs['scanner'].dead, False)
        killall(self.worker.jobs.values(), timeout=1)
        self.worker.revive_job = MagicMock()
        self.assertEqual(self.worker.jobs['scanner'].dead, True)
        self.worker.check_and_revive_jobs()
        self.assertEqual(self.worker.jobs['scanner'].dead, True)
        self.worker.revive_job.assert_called_once()
        killall(self.worker.jobs.values())

    def test_check_and_revive_jobs(self):
        self.worker = EdrDataBridge(config)
        self.worker._start_jobs()
        self.assertEqual(self.worker.jobs['scanner'].dead, False)
        killall(self.worker.jobs.values(), timeout=1)
        self.assertEqual(self.worker.jobs['scanner'].dead, True)
        self.worker.check_and_revive_jobs()
        self.assertEqual(self.worker.jobs['scanner'].dead, False)
        killall(self.worker.jobs.values())