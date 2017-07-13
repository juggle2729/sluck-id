# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.model.coupon import GroupCoupon
from luckycommon.social.model.share import *
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.tz import now_ts

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def submit(user_id, date_str, share_type):
    item = SocialShare.query.filter(SocialShare.user_id == user_id)\
                            .filter(SocialShare.date == date_str)\
                            .filter(SocialShare.share_type == share_type)\
                            .with_lockmode('update').first()
    if not item:
        item = SocialShare()
        item.user_id = user_id
        item.date = date_str
        item.share_type = share_type
        item.share_times = 0
        if share_type == SHARE_TYPE.DETAIL:
            # create coupon
            coupon = GroupCoupon()
            coupon.user_id = user_id
            coupon.title = ''
            coupon.total_count = SHARE_COUPON_INTERNAL_COUNT
            coupon.left_count = SHARE_COUPON_INTERNAL_COUNT
            coupon.expire_ts = now_ts() + SHARE_COUPON_EXPIRE_TS
            coupon.campaign_id = 'social_share'
            coupon.save(auto_commit=False)
            orm.session.flush()
            item.extend = json.dumps({'coupon': coupon.id})
    item.share_times += 1
    item.save(auto_commit=False)
    orm.session.commit()
    return item
