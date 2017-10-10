# -*- coding: utf-8 -*-
from datetime import datetime
from logging import getLogger
from string import digits, uppercase
from uuid import uuid4

from constants import FORM_NAME, qualification_procurementMethodType, tender_status, version
from restkit import ResourceError


LOGGER = getLogger(__name__)


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
