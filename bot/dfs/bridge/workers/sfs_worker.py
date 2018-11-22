# coding=utf-8
import random
from gevent import monkey, sleep

from bot.dfs.bridge.sfs.exceptions import SfsApiError, SfsJsonApiError
from bot.dfs.bridge.xml_utils import generate_request

monkey.patch_all()
import logging.config

from datetime import datetime

from bot.dfs.bridge.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class SfsWorker(BaseWorker):
    def __init__(self, sfs_client, sfs_reqs_queue, upload_to_api_queue, process_tracker, redis_db,
                 services_not_available, sleep_change_value, delay=15):
        super(SfsWorker, self).__init__(services_not_available)
        self.start_time = datetime.now()

        self.delay = delay
        self.process_tracker = process_tracker

        # init queues for workers
        self.sfs_reqs_queue = sfs_reqs_queue
        self.upload_to_api_queue = upload_to_api_queue
        self.requests_db = redis_db
        self.sfs_client = sfs_client
        self.sleep_change_value = sleep_change_value

    def send_sfs_request(self):
        while not self.exit:
            data = self.sfs_reqs_queue.get()
            logger.info(u"Got data from edrpou_codes_queue: {}".format(data))
            recent_reqs = self.requests_db.recent_requests_with(data.code)
            logger.info("Recent requests: {}".format(recent_reqs))
            if not recent_reqs:
                self.process_new_request(data)
            else:
                self.process_existing_request(data, recent_reqs[0])
            sleep(self.delay)

    def process_new_request(self, data):
        """Make a new request, bind award in question to it"""
        logger.info(u"Processing new request: {}".format(data))
        request_id = self.send_request(data)
        self.requests_db.add_sfs_request(request_id, {"code": data.code, "tender_id": data.tender_id,
                                                      "name": data.name, "kvt2": "", "doc_url": ""})
        self.requests_db.add_award(data.tender_id, data.award_id, request_id, data)

    def process_existing_request(self, data, existing_request_id):
        logger.info(u"Processing existing request: {};\t{}".format(data, existing_request_id))
        """bind award to existing request, load the answer which is already there into Central Database"""
        completed_reqs = self.requests_db.recent_complete_requests_with(data.code)
        logger.info("Put {} into upload queue".format(data))
        if completed_reqs:  # this way we upload the completed request, not pending one
            self.requests_db.add_award(data.tender_id, data.award_id, completed_reqs[0], data)
            self.upload_to_api_queue.put((data, self.requests_db.get_request(completed_reqs[0])))
        else:  # this way we upload receipt from existing request into the award
            self.requests_db.add_award(data.tender_id, data.award_id, existing_request_id, data)
            self.upload_to_api_queue.put((data, self.requests_db.get_request(existing_request_id)))

    def _start_jobs(self):
        return {"send_sfs_request": self.send_sfs_request()}

    def send_request(self, data):
        request_id = random.randint(0, 1000)
        try:
            data.code = '1234567890'  # TODO: change
            content, fname = generate_request(data, request_id)  # data -> Encrypted XML + filename

        except ValueError as e:
            logger.exception('Generating request for {code} failed: {e}'.format(code=data.code, e=e))
            raise

        try:
            response = self.sfs_client.send_report(content, fname)
        except SfsJsonApiError as e:
            print(e.response_data)
            logger.error('Request for code {code} failed: {e}'.format(code=data.code, e=e))
            return False

        if response.status == 'OK':
            logger.info('Request for {code} accepted.'.format(code=data.code))
            # response = self.sfs_client.extract_data(response.kvtList[0].kvtBase64)  # Encrypted Base64 -> XML
            return response.id

        logger.error(
            'Request for {code} not accepted: status={status}, kvt count: {count}, kvt_status: {kvt_status}'.format(
                code=data.code,
                status=response.status,
                count=len(response.kvtList) if response.kvtList else 0,
                kvt_status=response.kvtList[0].status if response.kvtList else 'None'
            ))
        return False
