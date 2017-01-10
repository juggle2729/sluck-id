# -*- coding: utf-8 -*-
import logging
import requests
import dicttoxml
import xmltodict
from future.utils import raise_with_traceback

from luckycommon.third.sms import SMSSender
from luckycommon.utils.exceptions import SmsPlatformError
from luckycommon.utils.template import generate_from_template

_LOGGER = logging.getLogger(__name__)


API_KEY = 'B7D360013A0D4F09BEFC0461902F0C'
SECRET_KEY = '9E949CC4E0510B5CD7625CBD2ABDB3'
URL = 'http://api.esms.vn/MainService.svc/xml/SendMultipleMessage_V4'


class ESMSSender(SMSSender):
    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        _LOGGER.info('sending sms use esms, phone: %s' % phone_nums)
        content = generate_from_template(template_id, params, has_title=False)
        post_data = {
            "RQST":
                {
                    "APIKEY": API_KEY,
                    "SECRETKEY": SECRET_KEY,
                    "ISFLASH": 0,
                    "SMSTYPE": 7,
                    "CONTENT": str(content.decode('utf-8')),
                    "CONTACTS": []
                }
        }
        if use_unicode:
            post_data['RQST']['UNICODE'] = 0
        for phone_num in phone_nums:
            post_data['RQST']['CONTACTS'].append({
                "CUSTOMER": {"PHONE": phone_num}
            })
        xml_data = dicttoxml.dicttoxml(post_data, attr_type=False, root=False)
        resp = requests.post(URL, xml_data)
        resp = xmltodict.parse(resp.text)['SmsResultModel']
        if resp['CodeResult'] != '100':
            raise_with_traceback(SmsPlatformError('phone: %s, error: %s' % (phone_nums, resp['ErrorMessage'])))


if __name__ == '__main__':
    sender = ESMSSender()
    sender.send_sms(['01659130499'], 'auth_code', {'code': '123456'})
