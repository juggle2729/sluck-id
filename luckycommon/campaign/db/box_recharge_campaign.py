# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.model.coupon import CouponTemplate, AccountCoupon
from luckycommon.campaign.model.box_recharge_campaign import *

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@sql_wrapper
def get_diamond(user_id, campaign_id):
    item = BoxRechargeCampaign.query.filter(BoxRechargeCampaign.user_id == user_id)\
                              .filter(BoxRechargeCampaign.campaign_id == campaign_id)\
                              .first()
    return item


@sql_wrapper
def add_diamond(user_id, campaign_id, price):
    item = BoxRechargeCampaign.query.filter(BoxRechargeCampaign.user_id == user_id)\
                              .filter(BoxRechargeCampaign.campaign_id == campaign_id)\
                              .with_lockmode('update').first()
    if not item:
        item = BoxRechargeCampaign()
        item.user_id = user_id
        item.campaign_id = campaign_id
        item.balance = 0
    item.balance += price
    item.save()
        

@sql_wrapper
def award_level(user_id, campaign_id, level_price, tid_list): 
    item = BoxRechargeCampaign.query.filter(BoxRechargeCampaign.user_id == user_id)\
                              .filter(BoxRechargeCampaign.campaign_id == campaign_id)\
                              .with_lockmode('update').first()
    if not item or item.balance < level_price:
        raise err.BalanceInsufficient("account balance insufficient")
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
        log_data = coupon.as_dict()
        log_data.update({
            'type': 'coupon',
            'from': u'充值活动',
            'action': 'create'
        })
        _TRACKER.info(log_data)
    item.balance -= level_price
    item.save(auto_commit=False)
    record = BoxRecord()
    record.user_id = user_id
    record.campaign_id = campaign_id
    record.consume_price = level_price
    record.balance = item.balance
    id_list = [str(i) for i in id_list]
    record.coupons = ','.join(id_list)
    record.save(auto_commit=False)
    orm.session.commit()
    return coupon_list
