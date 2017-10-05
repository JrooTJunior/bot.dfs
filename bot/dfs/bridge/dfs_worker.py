from gevent import monkey, sleep
monkey.patch_all()

from base_worker import BaseWorker
from datetime import datetime


class SfsWorker(BaseWorker):

    def __init__(self, sfs_client, dfs_reqs_queue, process_tracker,
                 services_not_available, sleep_change_value, delay=15):
        super(SfsWorker, self).__init__(services_not_available)
        self.start_time = datetime.now()

        self.delay = delay
        self.process_tracker = process_tracker

        # init queues for workers
        self.dfs_reqs_queue = dfs_reqs_queue
        self.sfs_client = sfs_client
        self.sleep_change_value = sleep_change_value

    def send_dfs_request(self):
        while not self.exit:
            data = self.dfs_reqs_queue.get()
            self.sfs_client.send_dfs_request()
            self.process_tracker.save_to_db(data.tender_id, data.award_id, data.personal_data)
            sleep(self.delay)

    def _start_jobs(self):
        return {"send_dfs_request": self.send_dfs_request()}


class CheckSfsWorker(BaseWorker):
    """Worker who periodically checks up on pending requests to SFS"""

    def __init__(self, sfs_client, checks_queue):
        super(CheckSfsWorker, self).__init__()
        self.sfs_client = sfs_client
