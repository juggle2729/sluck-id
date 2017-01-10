# -*- coding: utf-8 -*-

import json
import logging

from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from luckycommon.model.coupon import AccountCoupon
from luckycommon.db import coupon as db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required, check_params
from luckycommon.utils.tz import utc_to_local_str

_LOGGER = logging.getLogger(__name__)


class CouponTemplateView(TemplateView):

    def get(self, req):
        query_dct = req.GET.dict()
        items, total_count = db.list_coupon_template(query_dct)

        resp_items = []
        for item in items:
            item.updated_at = utc_to_local_str(item.updated_at)
            item.created_at = utc_to_local_str(item.created_at)
            resp_items.append(item.as_dict())

        return {'list': resp_items, 'page': query_dct.get('$page', 1),
                'size': len(resp_items), 'total_count': total_count}

    def post(self, req):
        query_dct = json.loads(req.body)
        db.upsert_coupon_template(query_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(CouponTemplateView, self).dispatch(*args, **kwargs)


class SingleCouponTemplateView(TemplateView):

    """ for now, only one banner...(id=1)
    """

    def get(self, req, coupon_template_id):
        banner = db.get_coupon_template(id=int(coupon_template_id))
        banner.updated_at = utc_to_local_str(banner.updated_at)
        banner.created_at = utc_to_local_str(banner.created_at)
        return banner.as_dict()

    def post(self, req, coupon_template_id):
        return self.put(req, coupon_template_id)

    def put(self, req, coupon_template_id):
        query_dct = json.loads(smart_unicode(req.body))
        query_dct['id'] = int(coupon_template_id)
        db.upsert_coupon_template(query_dct)
        return {}

    @method_decorator(response_wrapper)
    @method_decorator(token_required)
    def dispatch(self, *args, **kwargs):
        return super(SingleCouponTemplateView, self).dispatch(*args, **kwargs)


@require_POST
@response_wrapper
@token_required
def manual_create_coupon(req):
    query_dct = json.loads(req.body)
    if 'user_id' in query_dct:
        # for single user
        check_params(query_dct, ('user_id', 'template_id'), {"count": 1})
        template = db.get_coupon_template(query_dct['template_id'])
        for _ in range(query_dct['count']):
            coupon = AccountCoupon.create_from_template(
                template, query_dct['user_id'], by=req.user_id)
            coupon.save()
            AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)

        _LOGGER.info("add user coupon: %s, user: %s", query_dct, req.user_id)
    elif 'uids' in query_dct:
        check_params(query_dct, ('uids', 'coupons'))
        for template_id, count in query_dct['coupons'].iteritems():
            template = db.get_coupon_template(template_id)
            for uid in query_dct['uids']:
                for _ in range(count):
                    coupon = AccountCoupon.create_from_template(
                        template, uid, by=req.user_id)
                    coupon.save()
                    AccountCoupon.start_expire_timer(
                        coupon.id, coupon.expire_ts)
        _LOGGER.info('add users %s coupons %s', query_dct['uids'],
                     query_dct['coupons'])

    return {}
