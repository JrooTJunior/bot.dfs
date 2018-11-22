# -*- coding: utf-8 -*-
from gevent import monkey

from bot.dfs.bridge.sfs.exceptions import SfsApiError

monkey.patch_all()

import logging.config
from datetime import datetime
from gevent import spawn, sleep

from bot.dfs.bridge.workers.base_worker import BaseWorker
from bot.dfs.bridge.utils import business_date_checker

logger = logging.getLogger(__name__)


class RequestForReference(BaseWorker):
    """ Edr API XmlData Bridge """

    def __init__(self, reference_queue, sfs_client, request_db, services_not_available, sleep_change_value,
                 delay=15):
        super(RequestForReference, self).__init__(services_not_available)
        self.start_time = datetime.now()
        self.delay = delay
        self.sfs_client = sfs_client
        self.request_db = request_db

        # init queues for workers
        self.reference_queue = reference_queue

        # blockers
        self.sleep_change_value = sleep_change_value

    def sfs_checker(self):
        """Get request ids from redis, check date, check quantity of documents"""
        while not self.exit:
            self.services_not_available.wait()
            if business_date_checker():
                try:
                    request_ids = self.request_db.get_pending_requests()
                    logger.info(u"got pending requests: {}".format(request_ids))
                except Exception as e:
                    logger.warning(u'Fail to get pending requests. Message {}'.format(e.message))
                else:
                    self.check_incoming_correspondence(request_ids)
            sleep(self.delay)

    def check_incoming_correspondence(self, request_ids):
        for request_id, request_data in request_ids.items():
            code = request_data['code']
            self.sfs_receiver(request_id, code)

            # try:
            #     cert = self.request_to_sfs.sfs_get_certificate_request(ca_name)
            # except Exception as e:
            #     logger.warning(u'Fail to get certificate. Message {}'.format(e.message))
            #     sleep()
            # else:
            #     try:
            #         quantity_of_docs = self.request_to_sfs.sfs_check_request(code)
            #     except Exception as e:
            #         logger.warning(
            #             u'Fail to check for incoming correspondence. Message {}'.format(e.message))
            #         sleep()
            #     else:
            #         if int(quantity_of_docs) != 0:
            #             self.sfs_receiver(request_id, code, ca_name, cert)

    def sfs_receiver(self, request_id, code):
        """Get documents from SFS, put request id with received documents to queue"""
        try:
            response = self.send_request(code, request_id)
        except Exception as e:
            logger.warning('Fail to check incoming correspondence: {}'.format(e))
        else:
            self.request_db.complete_request(request_id)
            # TODO: send data to next workers

        # try:
        #     received_docs = self.request_to_sfs.sfs_receive_request(code, ca_name, cert)
        # except Exception as e:
        #     logger.warning(u'Fail to check for incoming correspondence. Message {}'.format(e.message))
        #     sleep()
        # else:
        #     self.request_db.complete_request(request_id)
        #     try:
        #         logger.info('Put request_id {} to process...'.format(request_id))
        #         all_the_data = self.request_db.get_tenders_of_request(request_id)
        #         yamled_data = {"meta": {"id": "123"}}  # TODO: placeholder; presume it will contain stuff needed
        #         for data in all_the_data:
        #             data.file_content['meta'].update(yamled_data['meta'])
        #         self.reference_queue.put((yamled_data, all_the_data))
        #     except Exception as e:
        #         logger.exception(u"Message: {}".format(e.message))
        #     else:
        #         logger.info(
        #             u'Received docs with request_id {} is already in process or was processed.'.format(request_id))

    def send_request(self, code, request_id):
        try:
            response = self.sfs_client.check_by_id(request_id)
        except SfsApiError as e:
            logger.error('Request {request_id} failed: {e}'.format(request_id=request_id, e=e))
            return False

        if response.status != 'OK':
            logger.error('Failed to check request {} for code {}'.format(request_id, code))
            return False
        elif not response.kvtList or len(response.kvtList) != 2:
            logger.error('Receipt 2 is not available for request {} code: {}'.format(request_id, code))
        else:
            logger.info('Request for {code} accepted.'.format(code=request_id))
            response = self.sfs_client.extract_data(response.kvtList[1].kvtBase64)  # Encrypted Base64 -> XML
            return response

        logger.error(
            'Request for {code} not accepted: status={status}, kvt count: {count}'.format(
                code=-1,
                status=response.status,
                count=len(response.kvtList) if response.kvtList else 0
            ))
        return False

    def _start_jobs(self):
        return {'sfs_checker': spawn(self.sfs_checker)}
