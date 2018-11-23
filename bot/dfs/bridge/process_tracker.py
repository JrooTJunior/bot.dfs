# coding=utf-8
import pickle
from datetime import datetime

from caching import db_key
from utils import item_key


class ProcessTracker(object):
    def __init__(self, db=None, ttl=300):
        self.processing_items = {}
        self.processed_items = {}
        self._db = db
        self.ttl = ttl

    def set_item(self, tender_id, award_id, docs_amount=1):
        self.processing_items[item_key(tender_id, award_id)] = docs_amount

    def check_processing_item(self, tender_id, award_id):
        """Check if current tender_id, award_id is processing"""
        return item_key(tender_id, award_id) in self.processing_items.keys()

    def check_processed_item(self, tender_id, award_id):
        """Check if current tender_id, award_id was already processed"""
        return item_key(tender_id, award_id) in self.processed_items.keys()

    def check_processed_tenders(self, tender_id):
        return self._db.has(db_key(tender_id)) or False

    def get_unprocessed_items(self):
        return self._db.get_items("unprocessed_*") or []

    def add_unprocessed_item(self, data):
        self._db.put(data.doc_id(), pickle.dumps(data), self.ttl)

    def _remove_unprocessed_item(self, document_id):
        self._db.remove(document_id)

    def _update_processing_items(self, tender_id, award_id, document_id):
        key = item_key(tender_id, award_id)
        if self.processing_items.get(key) > 1:
            self.processing_items[key] -= 1
        else:
            self.processed_items[key] = datetime.now()
            self._remove_unprocessed_item(document_id)
            if key in self.processing_items:
                del self.processing_items[key]

    def update_items_and_tender(self, tender_id, award_id, document_id):
        self._update_processing_items(tender_id, award_id, document_id)
