#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import time

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "luckyplatform.settings")

from luckycommon.db.pay import get_pay, update_pay_ext
from luckycommon.db.transaction import add_pay_success_transaction
from luckycommon.model.pay import PayStatus
from luckycommon.pay.handler import pay_after_recharge
from luckycommon.account.model.account import Account

_LOGGER = logging.getLogger('pay')
_TRACKER = logging.getLogger('tracker')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(u"请输入 Pay ID 和 金额(元)")
        exit()

    pay_id = sys.argv[1]
    pay = get_pay(pay_id)

    if not pay:
        print(u"Pay Object 不存在")
        exit()

    pay_amount_from_cmd = sys.argv[2]
    pay_amount_from_database = pay.price

    if pay.status != PayStatus.SUBMIT.value:
        print(u"Pay object 状态异常. pay.status: %s" % pay.status)
        exit()

    user_id = pay.user_id
    user = Account.query.with_for_update().filter(Account.id == user_id).first()

    print(u"用户: %s, 充值前余额: %s" % (str(user.phone), str(user.balance)))

    total_fee = pay_amount_from_cmd

    channel = u"支付宝"
    extend = {
        'title': u"充值-%s" % channel,
        'ext': {
            'total_fee': total_fee,
            'note': "charge manually"
        }
    }
    update_pay_ext(pay_id, extend['ext'])
    _LOGGER.info('pingpp check order success, user_id:%s pay_id:%s' % (user_id, pay_id))
    res = add_pay_success_transaction(user_id, pay_id, total_fee, extend)
    _TRACKER.info({'user_id': user_id, 'type': 'recharge',
                   'price': total_fee,
                   'channel': 'ping++'})
    if res:
        try:
            pay_after_recharge(pay)
        except Exception as e:
            _LOGGER.exception('pay_after_recharge of pay[%s] exception.(%s)', pay.id, e)

    user = Account.query.with_for_update().filter(Account.id == user_id).first()
    print(u"用户: %s, 充值后余额: %s" % (str(user.phone), str(user.balance)))
