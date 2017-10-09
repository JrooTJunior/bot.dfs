# -*- coding: utf-8 -*-
import os
from json import loads
from pytz import timezone


def read_json(name):
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


major = 0
minor = 0
bugfix = 1
version = '{}.{}.{}'.format(major, minor, bugfix)
author = "SfsBot"
retry_mult = 1
id_passport_len = 9
scheme = u'UA-EDR'
tender_status = "active.qualification"
DOC_TYPE = "sfsConfirmation"
AWARD_STATUS = 'active'
qualification_procurementMethodType = ('aboveThresholdUA', 'aboveThresholdUA.defense', 'aboveThresholdEU',
                                       'competitiveDialogueUA.stage2', 'competitiveDialogueEU.stage2')
HOLIDAYS = read_json('working_days.json')
TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
