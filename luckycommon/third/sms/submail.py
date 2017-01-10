# -*- coding: utf-8 -*-
import json

import requests
from future.utils import raise_with_traceback

from luckycommon.third.sms import SMSSender
from luckycommon.utils.exceptions import SmsPlatformError
from luckycommon.utils.api import EnhencedEncoder

URL = 'https://api.submail.cn/message/xsend.json'
APPID = '10685'
APP_KEY = '8419e355ac064269f34e5c34d652f082'

TEMPLATE_DICT = {
    'auth_code': 'wMgdP3',
    'sms_award_notify': 'ZYl6a1',
    'sms_lack_goods': 'd2s9A',
    'sms_shipping_notify': 'ys2v52',
    'sms_shipping_virtual_notify': 'fbYG91',
    'sms_shipping_coupon_notify': 'J6TXY1',
    'sms_shipping_coin_notify': 'PpOOY4',
    'sms_shipping_qq_notify': 'W8oCd3',
    'sms_show_bonus': 'ljfHL3',
    'sms_sign_award': 'SB40g',
    'sms_recharge_campaign_award': 'MQfKH',
    'sms_strategy_amount': 'BDpb53',
    'sms_jd_balance_warning': 'xhOYL',
    'sms_redenvelope_code': 'S1ojD3',
    'sms_notify_a': 'VdJ2N4',
    'sms_notify_b': '4Vm893',
    'sms_notify_c': 'AF3ab1',
    'sms_notify_d': 'scuaE',
}


class SubMailSender(SMSSender):

    def send_sms(self, phone_nums, template_id, params, use_unicode=True):
        post_data = {
            'appid': APPID,
            'project': TEMPLATE_DICT[template_id],
            'vars': json.dumps(params, cls=EnhencedEncoder,
                               ensure_ascii=False),
            'signature': APP_KEY
        }
        for phone_num in phone_nums:
            # TODO: check phone number validation
            post_data['to'] = phone_num

            resp = requests.post(URL, post_data).json()
            if resp['status'] != 'success':
                raise_with_traceback(SmsPlatformError(
                    resp.get('msg', 'unknown error')))


if __name__ == '__main__':
    sender = SubMailSender()
    sender.send_sms(['8618502710984'], 'jN9zt3', {'name': 'terran'})
