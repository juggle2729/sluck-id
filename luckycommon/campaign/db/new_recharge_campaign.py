# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.model.coupon import CouponTemplate, AccountCoupon
from luckycommon.model.campaign import LEVEL_STATUS, NewRechargeCampaign

from luckycommon.utils.decorator import sql_wrapper


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@sql_wrapper
def get_levels(user_id, campaign_id, level_id):
    item = NewRechargeCampaign.query.filter(NewRechargeCampaign.user_id == user_id)\
                                 .filter(NewRechargeCampaign.campaign_id == campaign_id)\
                                 .filter(NewRechargeCampaign.level == level_id)\
                                 .filter(NewRechargeCampaign.status == LEVEL_STATUS.UNOPEN)\
                                 .all()
    return item


@sql_wrapper
def get_available_levels(user_id, campaign_id):
    return NewRechargeCampaign.query.filter(NewRechargeCampaign.user_id == user_id)\
                              .filter(NewRechargeCampaign.campaign_id == campaign_id)\
                              .filter(NewRechargeCampaign.status == LEVEL_STATUS.UNOPEN)\
                              .all()


@sql_wrapper
def get_award_levels(user_id, campaign_id):
    return NewRechargeCampaign.query.filter(NewRechargeCampaign.user_id == user_id)\
                              .filter(NewRechargeCampaign.campaign_id == campaign_id)\
                              .filter(NewRechargeCampaign.status == LEVEL_STATUS.OPENED)\
                              .all()


@sql_wrapper
def add_new_level(user_id, campaign_id, level, price):
    item = NewRechargeCampaign()
    item.campaign_id = campaign_id
    item.user_id = user_id
    item.level = level
    item.current_price = price
    item.status = LEVEL_STATUS.UNOPEN
    item.save()


@sql_wrapper
def award_level(record_id, user_id, tid_list):
    # do transaction
    item = NewRechargeCampaign.query.filter(NewRechargeCampaign.id == record_id)\
                                    .filter(NewRechargeCampaign.status == LEVEL_STATUS.UNOPEN)\
                                    .with_lockmode('update').one()
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
        _TRACKER.info({'user_id': coupon.user_id,
                       'coupon_id': coupon.id,
                       'type': 'create_coupon',
                       'from': 'recharge_campaign',
                       'price': coupon.price})
    # change level status
    item.status = LEVEL_STATUS.OPENED
    id_list = [str(i) for i in id_list]
    item.coupons = ','.join(id_list)
    item.save(auto_commit=False)
    orm.session.commit()
    return coupon_list


@sql_wrapper
def get_award_timeline(campaign_id):
    query = NewRechargeCampaign.query.filter(NewRechargeCampaign.campaign_id == campaign_id)\
                                     .filter(NewRechargeCampaign.status == LEVEL_STATUS.OPENED)
    query = query.order_by(NewRechargeCampaign.id.desc()).limit(10)
    return query.all()
