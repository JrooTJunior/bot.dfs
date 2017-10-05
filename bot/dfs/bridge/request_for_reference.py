# -*- coding: utf-8 -*-
from gevent import monkey

monkey.patch_all()

import json
import logging.config
from datetime import datetime
from gevent import spawn
from base_worker import BaseWorker
from zeep import Client, helpers
from RequestsDb import get_pending_requests

logger = logging.getLogger(__name__)


def soap_to_dict(soap_object):
    return json.loads(json.dumps(helpers.serialize_object(soap_object)))


class RequestForReference(BaseWorker):
    """ Edr API Data Bridge """
    def __init__(self, tenders_sync_client, reference_queue, services_not_available, sleep_change_value, delay=15):
        super(RequestForReference, self).__init__(services_not_available)
        self.start_time = datetime.now()
        self.delay = delay
        self.request_ids = get_pending_requests()

        # init clients
        self.tenders_sync_client = tenders_sync_client
        self.dfs_client = Client('http://obmen.sfs.gov.ua/SwinEd.asmx?WSDL')

        # init queues for workers
        self.reference_queue = reference_queue

        # blockers
        self.sleep_change_value = sleep_change_value

    def request_checker(self):
        for request_id, request_data in self.request_ids.items():
            edr_id = request_data['edr_id']
            if self.date_checker:
                dfs_check = self.dfs_client.service.Check(recipientEDRPOU=edr_id, recipientDept=1, procAllDepts=1)
                dfs_check_to_dict = soap_to_dict(dfs_check)
                quantity_of_docs = dfs_check_to_dict['qtDocs']
                if quantity_of_docs == 0:
                    dfs_receive = self.dfs_client.service.Receive(recipientEDRPOU=edr_id, recipientDept=1,
                                                                  procAllDepts=1)
                    dfs_receive_to_dict = soap_to_dict(dfs_receive)
                    dfs_received_docs = dfs_receive_to_dict['docs']
                    try:
                        logger.info('Put request_id {} to process...'.format(request_id))
                        self.reference_queue.put((request_id, dfs_received_docs))
                    except Exception as e:
                        logger.exception("Message: {}".format(e.message))
                        return False
                    else:
                        return True

    def date_checker(self):
        return True

    def _start_jobs(self):
        return {'request_checker': spawn(self.request_checker)}
