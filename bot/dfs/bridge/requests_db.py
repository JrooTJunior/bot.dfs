# -*- coding: utf-8 -*-


class RequestsDb(object):

    def __init__(self, db):
        super(RequestsDb, self).__init__()
        self._db = db

    def add_sfs_request(self, request_id, request_data):
        self._db.hmset(req_key(request_id), request_data)
        self._db.sadd("requests:pending", request_id)

    def get_pending_requests(self):
        return {key: self.get_request(key) for key in self._db.smembers("requests:pending")}

    def get_request(self, request_id):
        return self._db.hgetall(req_key(request_id))

    def complete_request(self, request_id):
        self._db.sremove("requests:pending", request_id)
        self._db.hset(request_id, "status", "complete")

    def add_award(self, tender_id, award_id, request_id):
        self._db.add(award_key(tender_id, award_id), request_id)


def award_key(tender_id, award_id):
    return "{}:{}".format(tender_id, award_id)


def req_key(request_id):
    return "requests:{}".format(request_id)
