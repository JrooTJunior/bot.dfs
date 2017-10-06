from gevent import monkey, sleep
monkey.patch_all()

from base_worker import BaseWorker
from datetime import datetime


class SfsWorker(BaseWorker):

    def __init__(self, sfs_client, sfs_reqs_queue, process_tracker, redis_db,
                 services_not_available, sleep_change_value, delay=15):
        super(SfsWorker, self).__init__(services_not_available)
        self.start_time = datetime.now()

        self.delay = delay
        self.process_tracker = process_tracker

        # init queues for workers
        self.sfs_reqs_queue = sfs_reqs_queue
        self.redis_db = redis_db
        self.sfs_client = sfs_client
        self.sleep_change_value = sleep_change_value

    def send_dfs_request(self):
        while not self.exit:
            data = self.sfs_reqs_queue.get()
            if self.redis_db.has_recent_requests(data.code):
                response = self.sfs_client.send_request()
            self.process_tracker.save_to_db(data.tender_id, data.award_id, data.personal_data)
            sleep(self.delay)

    def _start_jobs(self):
        return {"send_dfs_request": self.send_dfs_request()}
