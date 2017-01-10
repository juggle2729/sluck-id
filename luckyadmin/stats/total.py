# -*- coding: utf-8 -*-
import logging
import json
from datetime import timedelta

from django.views.decorators.http import require_GET, require_POST

from luckycommon.stats import MG as mg
from luckycommon.db.strategy import get_current_amount, get_strategy_config
from luckycommon.db import activity as activity_db
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.api import token_required
from luckycommon.utils.tz import get_utc_date
from luckycommon.utils.exceptions import ParamError
from luckycommon.timer.handler import ActivityAnnounceHandler
from luckycommon.strategy.handler import set_strategy_config
from luckycommon.utils.decorator import mongo_wrapper

_LOGGER = logging.getLogger(__name__)


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_stats(req):
    query_dct = req.GET.dict()
    start_date = get_utc_date(query_dct.get('date'))
    end_date = start_date + timedelta(days=1)

    resp = {}
    # recharge
    recharge = mg.daily_stats.aggregate([
        {"$match": {"updated_at": {"$gte": start_date, "$lt": end_date},
                    "recharge.total": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$recharge.total"},
                    "count": {"$sum": "$recharge.count"},
                    "user_count": {"$sum": 1}}}
    ])
    recharge = recharge.next() if recharge.alive else {}
    recharge.pop("_id", 0)
    resp["recharge"] = recharge or {"total": 0, "count": 0, "user_count": 0}
    resp["recharge"]["count"] = int(resp["recharge"]["count"])

    # annouce
    resp["annouce"] = {}
    annouce = get_current_amount(
        ActivityAnnounceHandler._DAILY_LIMIT, start_date).as_dict()
    for k in ('amount_limit', 'current_amount', 'current_count',
              'manual_amount', 'manual_amount_limit'):
        resp["annouce"][k] = annouce[k]
    resp["annouce"]["unused_amount"] = annouce[
        "amount_limit"] - annouce["current_amount"]
    resp["annouce"]["unused_manual_amount"] = annouce[
        "manual_amount_limit"] - annouce["manual_amount"]
    config = get_strategy_config()
    resp["annouce"]["default_limit"] = config.amount_limit
    resp["annouce"]["default_manual_limit"] = config.manual_amount_limit

    # user
    resp["user"] = {}
    active = mg.daily_stats.aggregate([
        {"$match": {"updated_at": {"$gte": start_date, "$lt": end_date}}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    resp["user"]["active"] = active.next().get(
        "count", 0) if active.alive else 0
    # activity
    resp["activity"] = {}
    resp["activity"]["hot_count"] = activity_db.get_hot_activity_count()
    resp["activity"]["process"] = activity_db.get_buy_process()

    return resp


@require_GET
@response_wrapper
@token_required
@mongo_wrapper
def get_recharge_list(req):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))
    limit = 20 if size <= 0 else size
    skip = 0 if page <= 0 else (page - 1) * limit
    query_dct = req.GET.dict()
    for k in 'start_date', 'end_date':
        query_dct[k] = get_utc_date(query_dct.get(k))

    if query_dct['start_date'] == query_dct['end_date']:
        query_dct['end_date'] += timedelta(days=1)

    cond = {"updated_at": {
        "$gte": query_dct['start_date'], "$lt": query_dct['end_date']},
        "recharge.total": {"$gt": 0}}
    results = mg.daily_stats.find(
        cond, {"user_id": 1, "recharge.total": 1}
    ).skip(skip).limit(limit).sort([("recharge.total", -1)])
    total_count = mg.daily_stats.aggregate([
        {"$match": cond},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    total_count = total_count.next().get(
        "count", 0) if total_count.alive else 0

    resp_items = []
    for result in results:
        resp_items.append({"user_id": result["user_id"],
                           "recharge": result["recharge"]["total"]})

    return {'list': resp_items, 'page': page or 1,
            'size': len(resp_items), 'total_count': total_count}


@require_POST
@response_wrapper
@token_required
def set_limit(req):
    try:
        data = json.loads(req.body)
    except (TypeError, ValueError):
        raise ParamError('not json body')
    set_strategy_config(
        data.get('current_limit'), data.get('current_manual_limit'),
        data.get('default_limit'), data.get('default_manual_limit'))

    return {}
