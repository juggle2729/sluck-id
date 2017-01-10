# -*- coding: utf-8 -*-

import requests
from future.utils import raise_with_traceback

from luckycommon.third.sms import SMSSender
from luckycommon.utils.exceptions import SmsPlatformError
from luckycommon.utils.template import generate_from_template

API_KEY = 'c85fcacbe6f2fbf9ccc9b678048e3811'
URL = 'http://sms-api.luosimao.com/v1/send.json'


class LSMSender(SMSSender):

    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        content = generate_from_template(template_id, params, has_title=False)

        for phone_num in phone_nums:
            if phone_num.startswith('86'):
                phone_num = phone_num[2:]
            resp = requests.post(URL,
                                 auth=("api", "key-%s" % API_KEY),
                                 data={
                                     "mobile": phone_num,
                                     "message": content
                                 }, timeout=3, verify=False).json()

            if resp['error'] != 0:
                raise_with_traceback(SmsPlatformError(resp['msg']))

if __name__ == '__main__':
    sender = LSMSender()
    sender.send_sms(['8618502710984'], 'auth_code', {'code': 123456})
