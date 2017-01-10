# -*- coding: utf-8 -*-
import logging

from future.utils import raise_with_traceback

from luckycommon.third.jd.token import send_request, get_token
from luckycommon.third.sms.helper import send_sms
from luckycommon.utils.exceptions import ServerError

_LOGGER = logging.getLogger(__name__)


def submit_order(params_dict):
    resp = send_request('biz.order.unite.submit', params_dict)
    resp = resp['biz_order_unite_submit_response']
    if resp['success'] is not True:
        tips = {'success': False, 'code': resp['resultCode'],
                'msg': resp['resultMessage']}
        _LOGGER.error('submit order failture, code:%s, msg: %s',
                      tips['code'], tips['msg'])
        if tips['code'] == '3017':            # 余额不足
            _LOGGER.error('not enough balance at jd!!!!')
            send_sms(['18627907155'], 'sms_jd_balance_warning')
        elif tips['code'] == '1004':
            get_token(True)
        return tips
    else:
        result = resp['result']
        result.pop('sku')
        result['success'] = True
        # 重要字段：
        # orderPrice: 总价, orderNakedPrice: 裸价, jdOrderId: 京东订单号
        # freight: 快递费, orderTaxPrice: 税
        return result


def check_balance(need_notify=False):
    params = {"payType": 4}
    r = send_request('biz.price.balance.get', params)
    r = r['biz_price_balance_get_response']
    if r['success'] is not True:
        _LOGGER.error('fail to get jd balance, code: %s, msg:%s',
                      r['resultCode'], r['resultMessage'])
        raise_with_traceback(ServerError("can't get balance from huicai!!!"))
        # send_sms(['18502710984'], 'CfyUG', {'msg': u'无法取得慧采余额'})
    else:
        if need_notify and r['result'] < 50000:
            send_sms(['18627907155'], 'sms_jd_balance_warning')
        return r['result']
