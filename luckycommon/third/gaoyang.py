# -*- coding: utf-8 -*-
import hashlib
import logging
from datetime import datetime
import json

import pyDes
import requests
import xmltodict
from django.conf import settings
from pytz import timezone
from luckycommon.utils.exceptions import DataError, ParamError
from luckycommon.db.pay import get_pay, update_pay_ext, create_pay, submit_pay_commit
from luckycommon.model.pay import PAY_TYPE, PAY_STATUS
from luckycommon.db.transaction import (add_pay_wait_transaction,
                                        add_pay_success_transaction,
                                        add_pay_fail_transaction)
from luckycommon.pay.handler import pay_after_recharge

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

_FAILED_CODE_DICT = {
    '00006': u'兑换失败',
    '10014': u'系统忙，请稍后再试',
    '10016': u'该订单支付已成功，不能重复提交',
    '10029': u'运营商系统维护，支付通道暂时关闭',
    '10030': u'运营商系统维护，该面值暂时关闭',
    '10031': u'商户没有开通此支付通道',
    '10062': u'商户不支持余额卡支付',
    '10076': u'该订单支付已失败，不能重复提交',
    '10082': u'该卡已被使用，请更换其他充值卡支付',
    '10083': u'很抱歉！该卡已连续二次支付不成功，请更换其他充值卡支付。',
    '10091': u'该卡正在处理中，请不要重复提交',
    '10110': u'系统忙，请稍后再试',
    '10118': u'商户不支持多卡支付',
    '10119': u'充值卡面额选择错误',
    '10120': u'该订单正在处理中，不能重复提交',
    '10123': u'系统忙，请稍后再试',
    '10124': u'由于运营商系统临时维护，该省充值卡暂时无法支付，请稍后再试。',
    '81000': u'该卡已失效，请更换其他充值卡支付',
    '81001': u'系统忙，请稍后再试',
    '81006': u'充值卡金额不足以支付订单',
    '81007': u'无效的卡号密码',
    '82019': u'暂不支持该卡支付',
    '82009': u'系统忙，请稍后再试',
}

_CARD_TYPES = {
    'china_mobile': {
        'name': u'全国移动充值卡',
        'pc_id': 'CMJFK00010001',
        'pm_id': 'CMJFK',
    },
    'china_telecom': {
        'name': u'中国电信充值付费卡',
        'pc_id': 'DXJFK00010001',
        'pm_id': 'DXJFK',
    },
    'china_unicom': {
        'name': u'全国联通一卡充',
        'pc_id': 'LTJFK00020000',
        'pm_id': 'LTJFK',
    }
}

_KEY = 'm35hoov8twq8t9lhqbz6lxyu7tva0903zm15fe3vs3ekf6ijdh5zf0s9nsoyuz7eqdhzvsx0z6g1a72c42oyyyno92gmbdnly8tqvi9a0fntnuvvzg59cxebjina4ytd'


def _encrypt(string):
    k = pyDes.des(_KEY[0:8], pyDes.ECB, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    return k.encrypt(string).encode('hex')


def _gen_order_verify_string(d):
    format_string = "version_id=%s&merchant_id=%s&order_date=%s&order_id=%s&amount=%s&currency=%s&cardnum1=%s&cardnum2=%s&pm_id=%s&pc_id=%s&merchant_key=%s"
    origin_string = format_string % (
        d['version_id'],
        d['merchant_id'],
        d['order_date'],
        d['order_id'],
        d['amount'],
        d['currency'],
        d['cardnum1'],
        d['cardnum2'],
        d['pm_id'],
        d['pc_id'],
        _KEY,
    )
    m = hashlib.md5()
    m.update(origin_string)
    sign = m.hexdigest().lower()
    return sign


def _gen_notify_verify_string(d):
    format_string = "version_id=%s&merchant_id=%s&order_date=%s&order_id=%s&currency=%s&pay_sq=%s&pay_date=%s&card_num=%s&card_pwd=%s&pc_id=%s&card_status=%s&card_code=%s&card_amount=%s&merchant_key=%s"
    origin_string = format_string % (
        d['version_id'],
        d['merchant_id'],
        d['order_date'],
        d['order_id'],
        d['currency'],
        d['pay_sq'],
        d['pay_date'],
        d['card_num'],
        d['card_pwd'],
        d['pc_id'],
        d['card_status'],
        d['card_code'],
        d['card_amount'],
        _KEY,
    )
    m = hashlib.md5()
    m.update(origin_string)
    sign = m.hexdigest().lower()
    return sign


def gaoyang_create_charge(pay):
    url = settings.PAY_GATEWAY_URL + str(pay.id)
    return url


def gaoyang_make_order(pay, card_type, amount, card_num, card_secret):
    url = 'http://change1.19ego.cn/pgworder/orderdirect.do'
    data = {
        'version_id': '2.00',
        'merchant_id': 275220,
        'order_date': datetime.now(timezone('Asia/Shanghai')).strftime('%Y%m%d'),
        'order_id': str(pay.id),
        'amount': amount,
        'cardnum1': _encrypt(str(card_num)),
        'cardnum2': _encrypt(str(card_secret)),
        'currency': 'RMB',
        'pm_id': _CARD_TYPES[card_type]['pm_id'],
        'pc_id': _CARD_TYPES[card_type]['pc_id'],
        'returl': '',
        'notify_url': settings.GAOYANG_NOTIFY_URL,
    }
    data['verifystring'] = _gen_order_verify_string(data)
    _LOGGER.info("gaoyang request data: %s" % data)
    response = requests.post(url, data=data)
    response_dict = xmltodict.parse(response.text)
    _LOGGER.info("gaoyang response data: %s" % response_dict)
    if response_dict['response']['result'] == 'P':
        return True
    else:
        return False


def check_notify_sign(request):
    data = request.POST
    _LOGGER.info("gaoyang notify request body: %s" % data)
    verify_string = data['verifystring']
    if verify_string != _gen_notify_verify_string(data):
        raise ParamError('Gaoyang notify data verify failed %s' % data)
    pay_id = data['order_id']
    if not pay_id:
        _LOGGER.error("fatal error, order_id not exists, data: %s" % data)
        raise ParamError('Gaoyang notify data does not contain pay ID')

    pay = get_pay(pay_id)
    if not pay:
        _LOGGER.info('pay_id invalid: %s' % pay_id)
        return

    trade_status = int(data['card_status'])
    failed_code = str(data['card_code'])
    user_id = pay.user_id
    trade_no = data['pay_sq']
    total_fee = data['card_amount']
    if pay.status == PAY_STATUS.SUBMIT:
        extend = {
            'title': u'充值-充值卡支付',
            'ext': {
                'trade_status': trade_status,
                'trade_no': trade_no,
                'total_fee': total_fee,
                'failed_reason': _FAILED_CODE_DICT.get(failed_code),
                'adjust_pay_list': [],
                'amount_sum': float(total_fee)
            }
        }
        update_pay_ext(pay_id, extend['ext'])
        if trade_status == 0:
            _LOGGER.info('Gaoyang check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
            res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
            _TRACKER.info({'user_id': user_id,
                           'type': 'recharge',
                           'price': total_fee,
                           'channel': 'gaoyang'})
            if res:
                try:
                    pay_after_recharge(pay)
                except Exception as e:
                    _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)
        else:
            add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
            _LOGGER.error('Gaoyang response data show transaction failed, data: %s', data)
    elif pay.status in [PAY_STATUS.DONE, PAY_STATUS.FAIL]:
        if pay.price and float(pay.price) == float(total_fee):
            # same repeated notify, just return Y
            return
        if (not pay.price and float(total_fee) > 0) or (pay.price and float(total_fee) > float(pay.price)):
            _LOGGER.info('Gaoyang notify amount increased, old:%s new:%s' % (pay.price, total_fee))
            new_pay = create_pay(user_id, PAY_TYPE.GAOYANG_CARD)
            _LOGGER.info('Generate new pay_id for Gaoyang pay, new pay_id:%s old pay_id: %s ' % (new_pay.id, pay.id))
            old_extend = json.loads(pay.extend)
            amount_sum = old_extend['amount_sum']
            new_amount = float(total_fee) - float(amount_sum)
            extend = {
                'title': u'补充充值-充值卡支付',
                'ext': {
                    'trade_status': trade_status,
                    'trade_no': trade_no,
                    'total_fee': new_amount,
                    'failed_reason': failed_code,
                    'pre_pay_id': str(pay.id),
                    'amount_sum': float(amount_sum)
                }
            }
            update_pay_ext(new_pay.id, extend['ext'])
            old_extend['amount_sum'] = float(total_fee)
            old_extend['adjust_pay_list'].append(new_pay.id)
            update_pay_ext(pay.id, old_extend)
            submit_pay_commit(new_pay.id, user_id)
            if trade_status == 0:
                _LOGGER.info('Gaoyang increase amount success, user_id:%s old pay_id:%s new pay_id: %s, increased amount: %s' % (
                user_id, pay_id, new_pay.id, new_amount))
                add_pay_success_transaction(user_id, new_pay.id, new_amount, extend)
                _TRACKER.info({'user_id': user_id,
                               'type': 'recharge',
                               'price': new_amount,
                               'channel': 'gaoyang'})
            else:
                add_pay_fail_transaction(user_id, pay_id, total_fee, extend)
                _LOGGER.error('Gaoyang response data show transaction failed, data: %s', data)


if __name__ == '__main__':
    print gaoyang_make_order('723594369750a73228e', 'china_unicom', 60, '919580738302507', '3480347756815443030')
