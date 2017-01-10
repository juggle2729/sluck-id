# -*- coding: utf-8 -*-
# 5 second interval

import logging

from future.utils import raise_with_traceback
from suds.client import Client
from luckycommon.third.sms import SMSSender
from luckycommon.utils.exceptions import SmsPlatformError
from luckycommon.utils.template import generate_from_template


_LOGGER = logging.getLogger(__name__)

_API_USERNAME = 'luckysky'
_API_PASSWORD = 'vmg123456'
_API_ALIAS = 'LUCKYSHOP'

_ERROR_CODECS = {
    '-1': 'Sending error (Message content unicode character)',
    '100': 'Authentication failure',
    '101': 'Authentication User is deactived',
    '102': 'Authentication User is expired',
    '103': 'Authentication User is locked',
    '104': 'Template not actived',
    '105': 'Template does not existed',
    '108': 'Msisdn in blackList',
    '304': 'Send the same content in short time',
    '400': 'Not enough money',
    '900': 'System is error',
    '901': 'Length of message is 612 with noneUnicode message and 266 with Unicode message',
    '902': 'Number of msisdn must be > 0',
    '904': 'Brandname is inactive',
}


class VMGSMSSender(SMSSender):
    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        _LOGGER.info('sending sms use VMG, phone: %s' % phone_nums)
        client = Client('http://brandsms.vn:8018/VMGAPI.asmx?wsdl')
        content = generate_from_template(template_id, params, has_title=False)
        result = client.service.BulkSendSms(phone_nums, _API_ALIAS, content.decode('utf-8'), '', _API_USERNAME, _API_PASSWORD)
        if int(result.error_code) != 0:
            raise_with_traceback(SmsPlatformError('phone: %s, error code: %s, %s' %
                                                  (phone_nums, result.error_code, _ERROR_CODECS[str(result.error_code)])))


if __name__ == '__main__':
    sender = VMGSMSSender()
    sender.send_sms(['01659130499'], 'auth_code', {'code': '123456'})
