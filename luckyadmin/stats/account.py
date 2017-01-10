# -*- coding: utf-8 -*-
from django.views.decorators.http import require_GET

from luckycommon.account.db.account import get_account, get_logon_info
from luckycommon.cache.redis_cache import is_virtual_account
from luckyapi.logic.crowdfunding import view_my_activitys_v2
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckyapi.logic.transaction import get_user_transactions
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.exceptions import DataError
from luckycommon.utils.tz import utc_to_local_str, ts_to_local_date_str
from luckycommon.db.coupon import list_coupon
from luckycommon.db.transaction import list_transaction
from luckycommon.stats.account import get_account_aggr


@require_GET
@response_wrapper
@token_required
def get_account_info(req, account_id):
    account_id = long(account_id)
    account = get_account(account_id)
    if not account:
        raise DataError(status=StatusCode.INVALID_USER)
    account = account.as_dict()
    account.pop("password")
    account['is_virtual'] = is_virtual_account(account_id)
    account.update(get_logon_info(account_id))
    account.update(get_account_aggr(account_id))
    account['created_at'] = utc_to_local_str(account['created_at'])
    account['updated_at'] = utc_to_local_str(account['updated_at'])
    # for mobile console
    account["total_recharge"] = account[
        'user_stats'].get("recharge", {}).get("total", 0)
    account["total_win"] = account['user_stats'].get("win", {}).get("total", 0)

    return account


@require_GET
@response_wrapper
@token_required
def get_coupon_list(req, account_id):
    query_dct = req.GET.dict()
    items, total_count = list_coupon(query_dct)
    resp_items = []
    for item in items:
        item.created_at = utc_to_local_str(item.created_at)
        item.updated_at = utc_to_local_str(item.updated_at)
        item.start_ts = ts_to_local_date_str(item.start_ts)
        item.expire_ts = ts_to_local_date_str(item.expire_ts)
        resp_items.append(item.as_dict())
    return {'list': resp_items, 'page': query_dct.get('page', 1),
            'size': len(resp_items), 'total_count': total_count}


@require_GET
@response_wrapper
@token_required
def get_recharge_list(req, account_id):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))

    # only_need: price, created_at
    items, total_count = get_user_transactions(long(account_id), page, size, 1)
    return {'list': items, 'page': page or 1,
            'size': len(items), 'total_count': total_count}


@require_GET
@response_wrapper
@token_required
def get_win_list(req, account_id):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))

    items, total_count = view_my_activitys_v2(
        long(account_id), page, size, 1, None)
    return {'list': items, 'page': page or 1,
            'size': len(items), 'total_count': total_count}


@require_GET
@response_wrapper
@token_required
def get_transaction_list(req, account_id):
    query_dct = req.GET.dict()
    query_dct['user_id'] = account_id
    items, total_count = list_transaction(query_dct)
    resp_items = []
    for item in items:
        item.order_id = str(item.order_id or '')
        item.created_at = utc_to_local_str(item.created_at)
        item.updated_at = utc_to_local_str(item.updated_at)
        resp_items.append(item.as_dict())
    return {'list': resp_items, 'page': query_dct.get('page', 1),
            'size': len(resp_items), 'total_count': total_count}
