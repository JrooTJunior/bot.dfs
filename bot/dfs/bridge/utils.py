# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime, time
from copy import deepcopy, copy
from logging import getLogger
from string import digits, uppercase
from uuid import uuid4

from constants import FORM_NAME, version, qualification_procurementMethodType, tender_status, DOC_TYPE, AWARD_STATUS, TZ, HOLIDAYS
from restkit import ResourceError


LOGGER = getLogger(__name__)

Data = namedtuple("Data", ["tender_id", "award_id", "edr_code", "name"])


def item_key(tender_id, item_id):
    return '{}_{}'.format(tender_id, item_id)


def journal_context(record={}, params={}):
    for k, v in params.items():
        record["JOURNAL_" + k] = v
    return record


def generate_req_id():
    return b'edr-api-data-bridge-req-' + str(uuid4()).encode('ascii')


def generate_doc_id():
    return uuid4().hex


class RetryException(Exception):
    pass


def check_412(func):
    def func_wrapper(obj, *args, **kwargs):
        try:
            response = func(obj, *args, **kwargs)
        except ResourceError as re:
            if re.status_int == 412:
                obj.headers['Cookie'] = re.response.headers['Set-Cookie']
                response = func(obj, *args, **kwargs)
            else:
                raise ResourceError(re)
        return response

    return func_wrapper


def is_no_document_in_edr(response, res_json):
    return (response.status_code == 404 and isinstance(res_json, dict)
            and res_json.get('errors')[0].get('description')[0].get('error').get('code') == u"notFound")


def should_process_item(item):
    return (item['status'] == AWARD_STATUS and not [document for document in item.get('documents', [])
                                                    if document.get('documentType') == DOC_TYPE])


def is_code_invalid(code):
    return (not (type(code) == int or (type(code) == str and code.isdigit()) or
                 (type(code) == unicode and code.isdigit())))


def more_tenders(params, response):
    return not (params.get('descending')
                and not len(response.data) and params.get('offset') == response.next_page.offset)


def valid_qualification_tender(tender):
    return (tender['status'] == tender_status and
            tender['procurementMethodType'] in qualification_procurementMethodType)


def sfs_file_name(edr_code, request_number):
    date = datetime.now()
    m = to_base36(date.month)
    d = to_base36(date.day)
    return "ieK{}{}{}{}{}{}.xml".format(edr_code, FORM_NAME, m, d, date.year, request_number)


def to_base36(number):
    """Converts an integer to a base36 string."""
    alphabet = digits + uppercase
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36


def business_date_checker():
    current_date = datetime.now(TZ)
    if current_date.weekday() in [5, 6] and HOLIDAYS.get(current_date.date().isoformat(), True) or HOLIDAYS.get(
            current_date.date().isoformat(), False):
        return False
    else:
        if time(9, 0) <= current_date.time() <= time(18, 0):
            return True
        else:
            return False
