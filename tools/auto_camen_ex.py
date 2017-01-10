# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import fcntl
import json
import pyDes
import logging
import urllib
import hashlib
import requests

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.third.kamen import *
from luckycommon.zero.start_card import start_activity

from luckycommon.cache import redis_cache
from luckycommon.model import orm
from luckycommon.order.model.order import *
from luckycommon.order.db import order as order_db
from luckycommon.db import activity as activity_db
from luckycommon.db import account as account_db
from luckycommon.strategy.handler import is_valid_user
from luckycommon.third.sms.helper import send_sms
from luckycommon.utils import tz
from luckycommon.utils import exceptions as err

from django.conf import settings

_LOGGER = logging.getLogger('ofpay')


NOTIFY_PHONES = ['15927067926', '18674066001', '15623099215', '15549483798', '18186055862']

REFER_TIDS = {
    #'1138217': [522],
    #'1138223': [523],
    '1138224': [524, 525, 526],
    #'1138228': [527],
    #'1138229': [528],
    #'1138230': [529, 530, 531],
    #'1138266': [519, 520, 521],
}


def sms_notify(product_id, product_title, err_code, err_info):
    try:
        params = {
            "product_id": product_title,
            "err_code": err_code,
            "err_info": err_info,
        }
        send_sms(NOTIFY_PHONES, 'sms_kamen_err', params)
        _LOGGER.info('sms notify kamen err, %s-%s-%s', product_id, err_code, err_info)
    except Exception as e:
        _LOGGER.exception('sms notify kamen err exception, %s', e)


def _url_encrypt(encrypt_params):
    h = hashlib.md5()
    h.update(APP_KEY)
    app_key_hash = h.hexdigest()
    sorted_params = sorted(encrypt_params, key=lambda item: item[0])
    param_array = [item[0] + '=' + str(item[1]) for item in sorted_params]
    param_str = "&".join(param_array) + APP_KEY
    m = hashlib.md5()
    m.update(param_str)
    signature = m.hexdigest()
    url = REQUEST_URL
    for r in encrypt_params:
        url += '%s=%s&' % (r[0], urllib.quote(str(r[1])))
    url += 'sign=%s' % signature
    return url


def _fill_charge_card(order, card_info):
    card_award = ChargeCardAward()
    card_award.user_id = order.user_id
    card_award.order_id = order.order_id
    card_award.card_info = json.dumps(card_info, ensure_ascii=False)
    card_award.save(auto_commit=False)
    order_db.update_order(order, {
        'status': ORDER_STATUS.WAIT_RECEIPT,
        'ship_status': SHIP_STATUS.SHIPPING_SUCCESS
    }, auto_commit=False)


def _request_card_ex(product_id, product_info, count, user_id, order):
    _LOGGER.info('ready to request kamen card, info:%s', product_info)
    timestamp = tz.local_now().strftime('%Y-%m-%d %H:%M:%S')
    order_no = 'zh%s%s' % (order.order_id, user_id)
    encrypt_params = [
        ('method', 'kamenwang.order.cardorder.add'),
        ('timestamp', timestamp),
        ('format', 'json'),
        ('customerid', APP_ID),
        ('customerorderno', order_no),
        ('v', '1.0'),
        ('productid', product_id),
        ('buynum', count),
    ]
    url = _url_encrypt(encrypt_params)
    print url
    refer_tids = REFER_TIDS.get(product_id) or []
    resp = requests.post(url)
    resp_obj = json.loads(resp.text)
    if 'MessageCode' in resp_obj:
        _LOGGER.error('request kamen card fail, msg:%s', resp_obj['MessageInfo'])
        # alarm
        current_status = redis_cache.get_card_status(product_id)
        if not current_status or 0 == int(current_status):
            sms_notify(product_id, product_info['title'], resp_obj['MessageCode'], resp_obj['MessageInfo'])
            redis_cache.set_card_status(product_id, 1)
        for refer_tid in refer_tids:
            activity_db.update_template(refer_tid, {'status': 2})
            _LOGGER.warn('paused tid %s for %s', refer_tid, product_id)
        raise err.ThirdPartyError('%s' % resp_obj['MessageCode'])
    else:
        third_id = resp_obj['OrderId']
        _LOGGER.info('request kamen card succ, third_id:%s, info:%s, count:%s, resp_obj:%s',
            third_id, product_info, count, resp_obj)
        card_info = []
        cards = resp_obj['Cards']
        for card in cards:
            card_number = card['CardNumber']
            card_pwd = card['CardPwd']
            pool_item = ChargeCardPool()
            pool_item.product_id = product_id
            pool_item.order_no = order_no
            pool_item.third_id = third_id
            pool_item.op_type = product_info['op']
            pool_item.title = product_info['title']
            pool_item.price = product_info['price']
            pool_item.card_number = card_number
            pool_item.card_pwd = card_pwd
            pool_item.used = 1
            pool_item.user_id = user_id
            pool_item.order_id = order.order_id
            pool_item.save(auto_commit=False)
            orm.session.flush()
            card_info.append({
                'id': pool_item.id,
                'third_id': pool_item.third_id,
                'product_id': pool_item.product_id,
                'card_number': pool_item.card_number,
                'card_pwd': pool_item.card_pwd
            })
        _fill_charge_card(order, card_info)
        orm.session.commit()
        current_status = redis_cache.get_card_status(product_id)
        if current_status:
            for refer_tid in refer_tids:
                try:
                    start_activity(refer_tid)
                except:
                    pass
            redis_cache.set_card_status(product_id, 0)
            redis_cache.add_card_price(product_info['price']*count)


def fetch_card_ex(user_id, template_id, order):
    """
    升级接口：用户领奖时再取请求卡密
    """
    product_conf = settings.CAMEN_TIDS[template_id]
    product_id = str(product_conf['product_id'])
    card_count = product_conf['count']
    _request_card_ex(product_id, CHARGE_CARD_CONF[product_id], card_count, user_id, order)


def shipping():
    items = AwardedOrder.query.filter(
        AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).filter(
        AwardedOrder.ship_status == SHIP_STATUS.NORMAL).all()
    for item in items:
        user_id = item.user_id
        if redis_cache.is_virtual_account(user_id):
            continue
        try:
            activity = activity_db.get_activity(item.activity_id)
            if not activity or \
                    activity.template_id not in settings.CAMEN_TIDS:
                continue
            if not is_valid_user(user_id, activity):
                print 'found invalid user %s' % user_id
                _LOGGER.info('found invalid user %s %s', user_id, item.order_id)
                # update order
                order_db.update_order_by_id(
                    item.order_id,
                    {
                        'status': ORDER_STATUS.DEAL,
                        'ship_status': SHIP_STATUS.ILLEGAL,
                        'extend': json.dumps({'illegal': 1})
                    })
                # black it
                account_db.black_account(user_id)
                continue
            # 获取卡密
            # lock order
            AwardedOrder.query.filter(AwardedOrder.order_id==item.order_id).filter(
                AwardedOrder.status==ORDER_STATUS.WAIT_SHIP).filter(
                AwardedOrder.ship_status==SHIP_STATUS.NORMAL).with_lockmode('update').one()
            order_db.update_order_by_id(
                item.order_id,
                {
                    'ship_status': SHIP_STATUS.CHARGING,
                })
            try:
                fetch_card_ex(user_id, activity.template_id, item)
                receipt_address = json.loads(item.receipt_address or '{}')
                phone = receipt_address.get('phone')
                try:
                    send_sms([phone], 'sms_camen_code', {
                        'term_number': activity.term_number,
                        "short_title": activity.short_title or activity.name,
                    })
                except:
                    pass
            except err.ThirdPartyError as e:
                order_db.update_order_by_id(
                    item.order_id,
                    {
                        'ship_status': SHIP_STATUS.NORMAL,
                    })
            except Exception as e:
                order_db.update_order_by_id(
                    item.order_id,
                    {
                        'ship_status': SHIP_STATUS.CHARGE_FAILED,
                    })
                # pause template
                activity_db.update_template(activity.template_id, {'status': 2})
                _LOGGER.warn('paused tid %s for unexpected error, order id %s',
                    activity.template_id, item.order_id)
                raise e
        except Exception as e:
            orm.session.rollback()
            _LOGGER.error('shipping charge card error %s %s-%s', e, user_id, item.order_id)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if 'shipping' == cmd:
        try:
            f = open('/tmp/flock_%s' % sys.argv[0].split('/')[-1], 'w')
            fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
            shipping()
            fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            raise e
