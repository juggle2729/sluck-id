# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.campaign.db import first_double as double_db
from luckycommon.campaign.model.first_double import *
from luckycommon.db import coupon as coupon_db

_LOGGER = logging.getLogger('lucky')


def apply(user_id):
    """
    报名活动
    """
    return double_db.apply(user_id)


def get_status(user_id):
    """
    获取活动参与状态
    """
    item = double_db.get_status(user_id)
    status = 0 if not item else item.status
    if 2 == status:
        coupons = json.loads(item.coupons)
        coupon_tid = coupons.get('tid') or None
        coupon_count = coupons.get('count') or 1
        coupon = coupon_db.get_coupon_template(coupon_tid)
        return {
            'status': status,
            'coupon_title': coupon.title,
            'coupon_desc': coupon.desc,
            'coupon_price': coupon.price,
            'coupon_count': coupon_count,
        }
    else:
        return {
            'status': status
        }


def recharge_callback(user_id, recharge_amount):
    """
    充值回调
    """
    try:
        if recharge_amount < LEAST_AMOUNT:
            return
        item = double_db.check_recharge(user_id, recharge_amount)
        if item:
            _LOGGER.info('first double, %s recharge success %s', user_id, recharge_amount)
    except Exception as e:
        _LOGGER.exception('first double, recharge_callback exception:%s', e)


def check_complete(user_id):
    item = double_db.get_status(user_id)
    status = 0 if not item else item.status
    return True if 2 == status else False
