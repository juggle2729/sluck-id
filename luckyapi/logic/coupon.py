# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.model.coupon import CouponLite

from luckycommon.cache import redis_cache
from luckycommon.model.coupon import COUPON_STATUS, CouponTemplate, GroupCoupon, AccountCoupon
from luckycommon.db import coupon as coupon_db
from luckycommon.account.db.account import get_account_by_phone
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.tz import now_ts, ts_to_local_date_str
from luckycommon.utils.exceptions import ParamError, ResourceInsufficient, AuthenticateError

from django.conf import settings


_LOGGER = logging.getLogger('lucky')
_DEFAULT_PAGE_SIZE = 30


def _create_coupon_lite_list(coupons, status=None):
    coupon_list = []
    now = now_ts()
    for coupon in coupons:
        coupon_lite = CouponLite()
        coupon_lite.id = coupon.id
        coupon_lite.title = coupon.title
        coupon_lite.desc = coupon.desc
        coupon_lite.price = coupon.price
        coupon_lite.status = coupon.status
        if coupon.status == COUPON_STATUS.UNUSED and now > coupon.expire_ts:
            coupon_lite.status = COUPON_STATUS.EXPIRED
        if status and not (status & coupon_lite.status):
            continue
        coupon_lite.start_date = ts_to_local_date_str(coupon.start_ts, f='%Y-%m-%d %H:%M:%S')
        coupon_lite.end_date = ts_to_local_date_str(coupon.expire_ts, f='%Y-%m-%d %H:%M:%S')
        coupon_list.append(coupon_lite)
    return coupon_list


def view_user_coupons(user_id, status, page, size):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    coupons, count = coupon_db.get_user_coupons(user_id, status, limit, offset)
    return _create_coupon_lite_list(coupons, status), count


def view_available_coupons(user_id, price, buy_list, page, size):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    now = now_ts()
    coupons = coupon_db.get_unused_coupons(user_id)
    available_coupon_list = []
    unavailable_coupon_list = []
    for coupon in coupons:
        template_id = coupon.template_id
        scopes = coupon_db.get_coupon_scope(template_id)
        scope_ids = [scope.activity_tid for scope in scopes]
        if buy_list is not None and scope_ids:
            interset = set(scope_ids).intersection(set(buy_list))
            if not interset:
                unavailable_coupon_list.append(coupon)
                continue
        if price < coupon.price or (coupon.condition_price 
            and price < coupon.condition_price) or (
                coupon.start_ts > now
            ) or (coupon.expire_ts < now):
            unavailable_coupon_list.append(coupon)
        else:
            available_coupon_list.append(coupon)

    available_coupons = _create_coupon_lite_list(available_coupon_list, status=COUPON_STATUS.UNUSED)
    available_coupons.sort(key=lambda x:x.price, reverse=True)
    unavailable_coupons = _create_coupon_lite_list(unavailable_coupon_list, status=COUPON_STATUS.UNUSED)
    return available_coupons, unavailable_coupons


COUPON_DAILY_LIMIT = 1


def snatch_coupon(phone_number, group_coupon_id):
    group_coupon = coupon_db.get_group_coupon(group_coupon_id)
    if not group_coupon:
        raise ParamError('coupon id invalid')
    internal_coupons = {} if not group_coupon.coupons else json.loads(group_coupon.coupons)
    if phone_number in internal_coupons:
        tid = internal_coupons[phone_number]
        template = CouponTemplate.query.filter(CouponTemplate.id == tid).one()
        data = {
            'title': template.title,
            'desc': template.desc,
            'price': template.price,
            'condition': template.condition_price,
            'duplicate': True
        }
        return data
    if group_coupon.left_count == 0:
        raise ResourceInsufficient("insufficient")
    snatched_count = redis_cache.get_daily_coupons(phone_number)
    if snatched_count > COUPON_DAILY_LIMIT:
        raise AuthenticateError('reached limit', status=StatusCode.REACH_LIMIT)

    account = get_account_by_phone(phone_number)
    coupon_template = coupon_db.snatch_group_coupon(group_coupon_id, phone_number, account)
    data = {
        'title': coupon_template.title,
        'desc': coupon_template.desc,
        'price': coupon_template.price,
        'condition': coupon_template.condition_price,
        'uid': None if not account else account.id
    }
    return data


def send_coupon_to_user(user_id, template_id, count, extend=None, start_ts=None):
    try:
        template = coupon_db.get_coupon_template(template_id)
        for _ in range(count):
            coupon = AccountCoupon.create_from_template(
                template, user_id, extend=extend, start_ts=start_ts)
            coupon.save()
            AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)

        _LOGGER.info("add user coupon: %s, user: %s, count: %s", template_id, user_id, count)
    except Exception as e:
        _LOGGER.exception('add user coupon exception, %s-%s, %s', user_id, template_id, e)
