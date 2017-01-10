# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import sys
import fcntl
import json
import os
from datetime import timedelta

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache import redis_cache
from luckycommon.order.model.order import CombineAwardedOrder, ORDER_STATUS, SHIP_STATUS
from luckycommon.order.db import order as order_db
from luckycommon.db import activity as activity_db
from luckycommon.db import account as account_db
from luckycommon.strategy.handler import is_valid_user
from luckycommon.third.sms.helper import send_sms
from luckycommon.model import orm
from luckyplatform.settings import RED_ENVELOPE_TIDS, TRANSFER_TIDS

_LOGGER = logging.getLogger('ofpay')


def generate():
    items = CombineAwardedOrder.query.filter(
        CombineAwardedOrder.status == ORDER_STATUS.WAIT_SHIP).filter(
        CombineAwardedOrder.ship_status == SHIP_STATUS.NORMAL).filter(
        CombineAwardedOrder.is_virtual == False).all()
    for item in items:
        user_id = item.buyer
        try:
            ac = activity_db.get_activity(item.activity_id)
            if not ac:
                continue

            tmp_id = ac.template_id
            price = None
            is_transfer = False
            if tmp_id in TRANSFER_TIDS:
                is_transfer = True
                price = TRANSFER_TIDS[tmp_id]
            elif tmp_id in RED_ENVELOPE_TIDS:
                price = RED_ENVELOPE_TIDS[tmp_id]
            else:
                continue

            if not is_valid_user(user_id, ac):
                print 'found invalid user %s' % user_id
                _LOGGER.info('found invalid user %s %s',
                             user_id, item.id)
                # update order
                order_db.update_order_by_id(
                    item.id,
                    {
                        'status': ORDER_STATUS.DEAL,
                        'ship_status': SHIP_STATUS.ILLEGAL,
                        'extend': json.dumps({'illegal': 1})
                    })
                # black it
                account_db.black_account(user_id)
                continue

            receipt_address = json.loads(item.receipt_address or '{}')
            phone = receipt_address.get('phone')
            code = order_db.generate_red_envelope(item.id,
                                                  tmp_id,
                                                  is_transfer)
            send_sms([phone], 'sms_redenvelope_code', {
                'code': code,
                'term_number': ac.term_number,
                'name': u'购物卡%s元' % price
            })
        except Exception as e:
            _LOGGER.error(e)

if __name__ == '__main__':
    try:
        f = open('/tmp/flock_%s' % sys.argv[0].split('/')[-1], 'w')
        fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
        generate()
        fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        raise e
