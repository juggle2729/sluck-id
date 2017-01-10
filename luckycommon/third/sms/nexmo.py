# -*- coding: utf-8 -*-
# 5 second interval

import logging

from future.utils import raise_with_traceback
from urllib import urlencode
import requests
from luckycommon.third.sms import SMSSender
from luckycommon.utils.exceptions import SmsPlatformError
from luckycommon.utils.template import generate_from_template


_LOGGER = logging.getLogger(__name__)

_API_KEY = 'c2001b58'
_API_PASSWORD = '97288f072024f929'
_API_ALIAS = 'ALONG'

#_ERROR_CODECS = {
#    '-1': 'Sending error (Message content unicode character)',
#    '100': 'Authentication failure',
#    '101': 'Authentication User is deactived',
#    '102': 'Authentication User is expired',
#    '103': 'Authentication User is locked',
#    '104': 'Template not actived',
#    '105': 'Template does not existed',
#    '108': 'Msisdn in blackList',
#    '304': 'Send the same content in short time',
#    '400': 'Not enough money',
#    '900': 'System is error',
#    '901': 'Length of message is 612 with noneUnicode message and 266 with Unicode message',
#    '902': 'Number of msisdn must be > 0',
#    '904': 'Brandname is inactive',
#}


class NexmoSender(SMSSender):
    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        _LOGGER.info('sending sms use Nexmo, phone: %s' % phone_nums)
        content = generate_from_template(template_id, params, has_title=False)
        for phone in phone_nums:
            params = {
                    'api_key': _API_KEY,
                    'api_secret': _API_PASSWORD,
                    'from': _API_ALIAS,
                    'type': 'unicode',
                    'to': phone,
                    'text': content
            }
            url = "https://rest.nexmo.com/sms/json?" + urlencode(params)
            try:
                res = requests.get(url)
                print res.content
                _LOGGER.info(res.content)
            except Exception as e:
                print e
                _LOGGER.error(e)

def test():
    sender = NexmoSender()
    sender.send_sms(['8613277976923'], 'auth_code', {'code': 'sorry, this is a debug msg'})

if __name__ == '__main__':
    sender = NexmoSender()
    sender.send_sms(['6281212827738'], 'auth_code', {'code': 'sorry, this is a debug msg'})
