# -*- coding: utf-8 -*-
from gevent import monkey

monkey.patch_all()

import json
import logging.config
from datetime import datetime
from gevent import spawn, sleep
from base_worker import BaseWorker
from zeep import helpers

logger = logging.getLogger(__name__)


def soap_to_dict(soap_object):
    return json.loads(json.dumps(helpers.serialize_object(soap_object)))


class RequestForReference(BaseWorker):
    """ Edr API Data Bridge """
    def __init__(self, dfs_client, reference_queue, request_db, services_not_available, sleep_change_value, delay=15):
        super(RequestForReference, self).__init__(services_not_available)
        self.start_time = datetime.now()
        self.delay = delay
        self.request_db = request_db
        self.request_ids = self.request_db.get_pending_requests()

        # init clients
        self.dfs_client = dfs_client

        # init queues for workers
        self.reference_queue = reference_queue

        # blockers
        self.sleep_change_value = sleep_change_value

    def dfs_checker(self):
        """Get request ids from redis, check date, check quantity of documents"""
        while not self.exit:
            self.services_not_available.wait()
            for request_id, request_data in self.request_ids.items():
                edr_id = request_data['edr_id']
                dept_id = 1
                depts_proc = 1
                ca_name = ""
                cert = ""
                if self.date_checker:
                    try:
                        dfs_check = self.dfs_client.service.Check(recipientEDRPOU=edr_id,
                                                                  recipientDept=dept_id,
                                                                  procAllDepts=depts_proc)
                    except Exception as e:
                        logger.warning('Fail to check for incoming correspondence. Message {}'.format(e.message))
                        sleep()
                    else:
                        dfs_check_to_dict = soap_to_dict(dfs_check)
                        quantity_of_docs = dfs_check_to_dict['qtDocs']
                        if quantity_of_docs != 0:
                            self.dfs_receive(request_id, edr_id, dept_id, depts_proc, ca_name, cert)

    def dfs_receive(self, request_id, edr_id, dept_id, depts_proc, ca_name, cert):
        """Get documents from SFS, put request id with received documents to queue"""
        try:
            dfs_receive = self.dfs_client.service.Receive(recipientEDRPOU=edr_id,
                                                          recipientDept=dept_id,
                                                          procAllDepts=depts_proc,
                                                          caName=ca_name,
                                                          cert=cert)
        except Exception as e:
            logger.warning('Fail to check for incoming correspondence. Message {}'.format(e.message))
            sleep()
        else:
            dfs_receive_to_dict = soap_to_dict(dfs_receive)
            dfs_received_docs = dfs_receive_to_dict['docs']
            try:
                logger.info('Put request_id {} to process...'.format(request_id))
                self.reference_queue.put((request_id, dfs_received_docs))
            except Exception as e:
                logger.exception("Message: {}".format(e.message))
            else:
                logger.info(
                    'Received docs with request_id {} is already in process or was processed.'.format(request_id))

    def date_checker(self):
        """Check if the working time is now or not"""
        return True

    def _start_jobs(self):
        return {'dfs_checker': spawn(self.dfs_checker)}
