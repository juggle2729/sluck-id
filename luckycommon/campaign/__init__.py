# -*- coding: utf-8 -*-
from datetime import datetime

from luckycommon.model.campaign import CAMPAIGN_DICT

from luckycommon.utils.tz import utc_to_local_str, to_local_ts, now_ts


def valid_time(start_time, end_time):
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    now_time = datetime.strptime(utc_to_local_str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S')
    if now_time >= start_time and now_time <= end_time:
        return True
    return False


def remain_ts(campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    start_time = campaign_info.get('start_time')
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    start_ts = to_local_ts(start_time)
    remain_ts = start_ts - now_ts()
    if remain_ts < 0:
        remain_ts = 0
    return remain_ts


def campaign_ts(campaign_id):
    campaign_info = CAMPAIGN_DICT.get(campaign_id)
    start_time = campaign_info.get('start_time')
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    start_ts = to_local_ts(start_time)
    end_time = campaign_info.get('end_time')
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    end_ts = to_local_ts(end_time)
    return now_ts(), start_ts, end_ts
