# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.model.coupon import (CouponTemplate, AccountCoupon)
from luckycommon.model.campaign import RecommendCampaign

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils import exceptions as err


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@sql_wrapper
def get_award_timeline(campaign_name):
    query = RecommendCampaign.query.filter(RecommendCampaign.campaign_name == campaign_name)
    query = query.order_by(RecommendCampaign.id.desc()).limit(10)
    return query.all()


@sql_wrapper
def get_status(user_id, campaign_name, date_str):
    item = RecommendCampaign.query.filter(RecommendCampaign.user_id == user_id)\
                            .filter(RecommendCampaign.campaign_name == campaign_name)\
                            .filter(RecommendCampaign.date == date_str).first()
    return item

@sql_wrapper
def activate(user_id, campaign_name, date_str, tid_list):
    item = RecommendCampaign.query.filter(RecommendCampaign.user_id == user_id)\
                            .filter(RecommendCampaign.campaign_name == campaign_name)\
                            .filter(RecommendCampaign.date == date_str)\
                            .with_lockmode('update').first()
    if item:
        raise err.DataError('activated')
    item = RecommendCampaign()
    item.user_id = user_id
    item.campaign_name = campaign_name
    item.date = date_str
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
    item.save(auto_commit=False)
    orm.session.commit()
    return coupon_list
