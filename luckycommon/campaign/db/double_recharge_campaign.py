# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.model.coupon import CouponTemplate, AccountCoupon
from luckycommon.campaign.model.double_recharge_campaign import *

from luckycommon.utils.orm import get_count
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import DataError


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@sql_wrapper
def get_levels(user_id, campaign_id, level_id):
    item = DoubleRechargeCampaign.query.filter(
        DoubleRechargeCampaign.user_id == user_id)\
        .filter(DoubleRechargeCampaign.campaign_id == campaign_id)\
        .filter(DoubleRechargeCampaign.level == level_id)\
        .all()
    return item


@sql_wrapper
def get_level_count(user_id, campaign_id, level_id):
    query = DoubleRechargeCampaign.query.filter(
        DoubleRechargeCampaign.user_id == user_id)\
        .filter(DoubleRechargeCampaign.campaign_id == campaign_id)\
        .filter(DoubleRechargeCampaign.level == level_id)
    return get_count(query)


@sql_wrapper
def add_new_level(user_id, campaign_id, level, price):
    item = DoubleRechargeCampaign()
    item.campaign_id = campaign_id
    item.user_id = user_id
    item.level = level
    item.current_price = price
    item.save()
    return item


@sql_wrapper
def award_level(record_id, user_id, tid_list, is_double=False):
    # do transaction
    item = DoubleRechargeCampaign.query.filter(
        DoubleRechargeCampaign.id == record_id)\
        .with_lockmode('update').one()
    if item.coupons:
        raise DataError('item coupons is not none')
    # create coupon
    coupon_list = []
    id_list = []
    for tid in tid_list:
        template = CouponTemplate.query.filter(CouponTemplate.id == tid).one()
        coupon = AccountCoupon.create_from_template(template, user_id)
        coupon.save(auto_commit=False)
        orm.session.flush()
        coupon_list.append(coupon)
        id_list.append(coupon.id)
        AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
    id_list = [str(i) for i in id_list]
    item.coupons = ','.join(id_list)
    if is_double:
        item.is_double = 1
    item.save(auto_commit=False)
    orm.session.commit()
    for coupon in coupon_list:
        log_data = coupon.as_dict()
        log_data.update({
            'type': 'coupon',
            'from': u'充值奖励',
            'action': 'create'
        })
        _TRACKER.info(log_data)
    return coupon_list
