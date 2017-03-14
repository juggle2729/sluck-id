# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
from decimal import Decimal

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'






from luckycommon.model.pay import Pay
from luckycommon.account.model.account import Account


COINS = [ (0.91, 1.00), (4.55, 5.00), (9.09, 10.00), (45.45, 50.00),(90.91, 100.00), (181.82, 200.00), (454.55, 500.00)]



for wrong_price, origin_price in COINS:
    add_value = origin_price - wrong_price
    pays = Pay.query.filter(Pay.pay_type == 19).filter(Pay.status == 2).filter(Pay.price == wrong_price).all()
    print "原始金额： %s，实际金额： %s，差额： %s，处理数量： %s" % (origin_price, wrong_price, add_value, len(pays))
    for pay in pays:
        print pay.updated_at, pay.id, pay.user_id, pay.price, pay.extend
        if pay.user_id is not None:
            # account = Account.query.filter(Account.id == pay.user_id).first()
            account = Account.query.filter(
                Account.id == pay.user_id).with_lockmode('update').first()
            if account is not None:
                old_balance = account.balance
                account.balance = account.balance + \
                              (0 if not add_value else Decimal(add_value).quantize(Decimal('0.01')))
                print 'UID: %s, Phone: %s, 现余额：%s, 更新后余额： %s, 增加值：%s' % (
                    account.id, account.phone, old_balance, account.balance, Decimal(add_value).quantize(Decimal('0.01')))
                account.save()
                pay.status = 3
                pay.save()



