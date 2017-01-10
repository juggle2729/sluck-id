# -*- coding: utf-8 -*-

from luckycommon.stats import MG as mg
from luckycommon.utils.tz import local_now, utc_to_local_str
from luckycommon.utils.decorator import mongo_wrapper


@mongo_wrapper
def get_account_aggr(account_id):
    account = {}
    account['user_stats'] = mg.user_stats.find_one(
        {"_id": account_id}) or {}
    for k in 'updated_at', 'created_at':
        if k in account['user_stats']:
            account['user_stats'][k] = utc_to_local_str(
                account['user_stats'][k])
    account['daily_stats'] = mg.daily_stats.find_one({"_id": "%s-%s" % (
        account_id, local_now().strftime('%Y-%m-%d'))}) or {}
    active_count = mg.daily_stats.aggregate([
        {"$match": {"user_id": account_id}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    account['active_days'] = active_count.next().get(
        'count', 0) if active_count.alive else 0

    return account
