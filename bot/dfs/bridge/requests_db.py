# coding=utf-8
from time import time


class RequestsDb(object):
    def __init__(self, db, time_range=1000):
        super(RequestsDb, self).__init__()
        self.time_range = time_range
        self._db = db

    def add_sfs_request(self, request_id, request_data):
        self._db.hmset(req_key(request_id), request_data)
        self._db.sadd("requests:pending", request_id)
        self._db.sadd("requests:edrpou:{}".format(request_data['edr_code']), request_id)
        self._db.zadd("requests:dates", time(), request_id)

    def get_pending_requests(self):
        return {key: self._get_request(key) for key in self._db.smembers("requests:pending")}

    def _get_request(self, request_id):
        return self._db.hgetall(req_key(request_id))

    def complete_request(self, request_id):
        self._db.srem("requests:pending", request_id)
        self._db.hset(req_key(request_id), "status", "complete")

    def add_award(self, tender_id, award_id, request_id):
        self._db.put(award_key(tender_id, award_id), request_id)
        self._db.sadd("tenders_of:{}".format(request_id), award_key(tender_id, award_id))

    def recent_requests_with(self, edr_code):
        self._db.zinterstore("recent:requests:edrpou:{}".format(edr_code), ("requests:edrpou:{}".format(edr_code),
                                                                            "requests:dates"))
        return self._db.zrangebyscore("recent:requests:edrpou:{}".format(edr_code), time() - self.time_range, time())

    def add_daily_request(self):
        self._db.incr("requests:number")


def award_key(tender_id, award_id):
    return "tender:{}:{}".format(tender_id, award_id)


def req_key(request_id):
    return "requests:{}".format(request_id)
