# -*- coding: utf-8 -*-
import time
import json
import logging
from hashlib import md5

from luckycommon.cache import ProxyAgent, prefix_key
from luckycommon.utils.tz import now_ts, left_seconds_today
from luckycommon.utils.decorator import cache_wrapper

_LOGGER = logging.getLogger('lucky')
_LOCK_TIMEOUT = 10


@cache_wrapper
def get_lucky_numbers(activity_id):
    """
    deprecated, used for db
    """
    key = prefix_key('luckynumbers:%s' % activity_id)
    return ProxyAgent().smembers(key)


@cache_wrapper
def add_lucky_numbers(activity_id, *num_list):
    """
    deprecated, used for db
    """
    key = prefix_key('luckynumbers:%s' % activity_id)
    return ProxyAgent().sadd(key, *num_list)


@cache_wrapper
def get_lucky_numbers_count(activity_id):
    """
    deprecated, used for db
    """
    key = prefix_key('luckynumbers:%s' % activity_id)
    return ProxyAgent().scard(key)


@cache_wrapper
def revert_lucky_numbers(activity_id, *num_list):
    """
    deprecated, used for db
    """
    key = prefix_key('luckynumbers:%s' % activity_id)
    return ProxyAgent().srem(key, *num_list)


@cache_wrapper
def generate_numbers(activity_id, *num_list):
    """
    used for db
    """
    key = prefix_key('numberspool:%s' % activity_id)
    # key_flag = prefix_key('poolflag:%s' % activity_id)
    # ProxyAgent().set(key_flag, 1)
    return ProxyAgent().sadd(key, *num_list)


@cache_wrapper
def get_numbers(activity_id, count):
    """
    used for db
    """
    key = prefix_key('numberspool:%s' % activity_id)
    return ProxyAgent().srandmember(key, count)


@cache_wrapper
def lock_numbers(activity_id, *num_list):
    """
    used for db
    """
    key = prefix_key('numberspool:%s' % activity_id)
    return ProxyAgent().srem(key, *num_list)


@cache_wrapper
def unlock_numbers(activity_id, *num_list):
    """
    used for db
    """
    key = prefix_key('numberspool:%s' % activity_id)
    return ProxyAgent().sadd(key, *num_list)

@cache_wrapper
def exists_15phone(phone):
    """
    used for autoship
    """
    key = prefix_key('phonenumber:%s' % phone)
    return ProxyAgent().exists(key)

@cache_wrapper
def set_15phone(phone):
    """
    used for autoship
    """
    key = prefix_key('phonenumber:%s' % phone)
    ProxyAgent().setnx(key, 'lala')
    ProxyAgent().expire(key, 15*62)


@cache_wrapper
def set_gp_order(orderid):
    '''
    used for gwallet refund
    :param orderid:
    :return:
    '''
    key = prefix_key('gporder:%s' % orderid)
    ProxyAgent().setnx(key, 'limit')
    ProxyAgent().expire(key, 3600 * 24 * 7)


@cache_wrapper
def exists_gp_order(orderid):
    key = prefix_key('gporder:%s' % orderid)
    return ProxyAgent().exists(key)


@cache_wrapper
def set_delay_timestamp(orderid, timestamp):
    '''
    used for set phone charge  delay deliver
    :param orderid:
    :param timestamp:
    :return None:
    '''
    key = prefix_key('phoneorder:%s' % orderid)
    ProxyAgent().setnx(key, timestamp)
    ProxyAgent().expire(key, 3600 * 4)

@cache_wrapper
def get_delay_timestamp(orderid):
    '''
    used for get phone charge  delay deliver
    :param orderid:
    :return timestamp:
    '''
    key = prefix_key('phoneorder:%s' % orderid)
    return ProxyAgent().get(key)

@cache_wrapper
def exists_phone_limit(phone):
    """
    used for autoship
    """
    key = prefix_key('phonelimit:%s' % phone)
    return ProxyAgent().exists(key)

@cache_wrapper
def set_phone_limit(phone, carrier):
    """
    used for autoship
    """
    key = prefix_key('phonelimit:%s' % phone)
    ProxyAgent().setnx(key, 'lala')
    if carrier in ('IR', 'TRI'):
        ProxyAgent().expire(key, 3*61)
    else:
        ProxyAgent().expire(key, 15*61)

@cache_wrapper
def get_left_numbers_count(activity_id):
    """
    used for db
    """
    key = prefix_key('numberspool:%s' % activity_id)
    return ProxyAgent().scard(key)


@cache_wrapper
def check_numbers_pool(activity_id):
    """
    used for cache flag
    """
    return True
    key = prefix_key('poolflag:%s' % activity_id)
    return ProxyAgent().get(key)


@cache_wrapper
def mapping_num_with_order(activity_id, num, order_id):
    """
    used for db
    """
    key = prefix_key('luckyorders:%s' % activity_id)
    field = str(num)
    value = str(order_id)
    return ProxyAgent().hset(key, field, value)


@cache_wrapper
def mapping_nums_with_order(activity_id, mapping_dict):
    """
    used for db
    """
    key = prefix_key('luckyorders:%s' % activity_id)
    return ProxyAgent().hmset(key, mapping_dict)


@cache_wrapper
def get_lucky_order(activity_id, lucky_number):
    """
    used for db
    """
    key = prefix_key('luckyorders:%s' % activity_id)
    field = str(lucky_number)
    return ProxyAgent().hget(key, field)


@cache_wrapper
def remove_lucky_order(activity_id):
    """
    used for db
    """
    key = prefix_key('luckyorders:%s' % activity_id)
    return ProxyAgent().delete(key)


@cache_wrapper
def submit_timer_event(event_type, cache_value, timestamp):
    """
    used for db
    """
    key = prefix_key('timerzset:%s' % event_type)
    return ProxyAgent().zadd(key, timestamp, cache_value)


@cache_wrapper
def range_expired_events(event_type, max_time):
    """
    used for db
    """
    key = prefix_key('timerzset:%s' % event_type)
    return ProxyAgent().zrangebyscore(key, 0, max_time)


@cache_wrapper
def remove_expired_event(event_type, event_value):
    """
    used for db
    """
    key = prefix_key('timerzset:%s' % event_type)
    return ProxyAgent().zrem(key, event_value)


@cache_wrapper
def timer_event_processed(event_id):
    """
    used for db
    """
    key = prefix_key('timerlock:%s' % event_id)
    return not ProxyAgent().setnx(key, int(time.time()))


@cache_wrapper
def try_template_lock(template_id):
    """
    used for db
    """
    key = prefix_key('templatelock:%s' % template_id)
    return ProxyAgent().setnx(key, int(time.time()))


@cache_wrapper
def release_template_lock(template_id):
    """
    used for db
    """
    key = prefix_key('templatelock:%s' % template_id)
    return ProxyAgent().delete(key)


@cache_wrapper
def get_sync_id(user_id):
    """
    used for db
    """
    key = prefix_key('notify:%s' % user_id)
    return ProxyAgent().incr(key)


@cache_wrapper
def get_sys_sync_id():
    """
    used for db
    """
    key = prefix_key('sysnotify')
    return ProxyAgent().incr(key)


@cache_wrapper
def add_virtual_account(user_id):
    """
    used for db
    """
    key = prefix_key('virtual:account')
    return ProxyAgent().sadd(key, user_id)


@cache_wrapper
def get_virtual_account():
    """
    used for db
    """
    key = prefix_key('virtual:account')
    return ProxyAgent().smembers(key)


@cache_wrapper
def get_random_virtual_account():
    """
    used for db
    """
    key = prefix_key('virtual:account')
    return ProxyAgent().srandmember(key)


@cache_wrapper
def is_virtual_account(user_id):
    """
    used for db
    """
    key = prefix_key('virtual:account')
    return ProxyAgent().sismember(key, user_id)


@cache_wrapper
def get_last_order():
    """
    used for db
    """
    key = prefix_key('lastorder')
    return ProxyAgent().get(key)


@cache_wrapper
def set_last_order(pay_at):
    """
    used for db
    """
    key = prefix_key('lastorder')
    return ProxyAgent().set(key, pay_at)


_ACTIVITY_WINNER_EXPIRE = 3600


@cache_wrapper
def set_activity_winner(activity_id, winner_info):
    """
    used for cache
    """
    key = prefix_key('winner:%s' % activity_id)
    return ProxyAgent().setex(key, _ACTIVITY_WINNER_EXPIRE, winner_info)


@cache_wrapper
def get_activity_winner(activity_id):
    """
    used for cache
    """
    key = prefix_key('winner:%s' % activity_id)
    return ProxyAgent().get(key)


@cache_wrapper
def get_revealed(activity_id):
    """
    used for cache
    """
    key = prefix_key('revealed:%s' % activity_id)
    return ProxyAgent().get(key)


_REVEALED_EXPIRE = 24 * 3600


@cache_wrapper
def set_revealed(activity_id, revealed_info):
    """
    used for cache
    """
    key = prefix_key('revealed:%s' % activity_id)
    return ProxyAgent().setex(key, _REVEALED_EXPIRE, revealed_info)


@cache_wrapper
def get_activity_detail(activity_id):
    """
    deprecated
    """
    key = prefix_key('detail:%s' % activity_id)
    return ProxyAgent().get(key)


_DETAIL_EXPIRE = 3 * 30 * 24 * 3600


@cache_wrapper
def set_activity_detail(activity_id, detail_info):
    """
    deprecated
    """
    key = prefix_key('detail:%s' % activity_id)
    return ProxyAgent().setex(key, _DETAIL_EXPIRE, detail_info)


@cache_wrapper
def get_winn_list(user_id):
    """
    used for db
    """
    key = prefix_key('winned:%s' % user_id)
    return ProxyAgent().smembers(key)


@cache_wrapper
def add_user_winn(user_id, activity_id):
    """
    used for db
    """
    key = prefix_key('winned:%s' % user_id)
    return ProxyAgent().sadd(key, activity_id)


@cache_wrapper
def add_user_pending(user_id, field, amount=1):
    """
    增加待处理消息
    used for cache
    """
    key = prefix_key('pending:%s' % user_id)
    return ProxyAgent().hincrby(key, field, amount)


@cache_wrapper
def remove_user_pending(user_id, field, delta=-1):
    """
    used for cache
    """
    key = prefix_key('pending:%s' % user_id)
    return ProxyAgent().hincrby(key, field, delta)


@cache_wrapper
def clear_user_pending(user_id, field):
    """
    used for cache
    """
    key = prefix_key('pending:%s' % user_id)
    return ProxyAgent().hdel(key, field)


@cache_wrapper
def set_user_pending(user_id, field, num):
    """
    used for cache
    """
    key = prefix_key('pending:%s' % user_id)
    return ProxyAgent().hset(key, field, num)


@cache_wrapper
def get_user_pending(user_id, field=None):
    """
    used for cache
    """
    key = prefix_key('pending:%s' % user_id)
    if field:
        return ProxyAgent().hget(key, field)
    else:
        return ProxyAgent().hgetall(key)


_MAX_SCROLLING = 20


@cache_wrapper
def submit_scrolling(cache_value, timestamp):
    """
    used for db
    """
    key = prefix_key('scrolling')
    return ProxyAgent().zadd(key, timestamp, cache_value)


@cache_wrapper
def range_scrolling(min_index=0, max_index=_MAX_SCROLLING - 1):
    """
    used for db
    """
    key = prefix_key('scrolling')
    return ProxyAgent().zrevrange(key, min_index, max_index, withscores=True)


@cache_wrapper
def get_scrolling_count():
    key = prefix_key('scrolling')
    return ProxyAgent().zcard(key)


@cache_wrapper
def trim_scrolling():
    key = prefix_key('scrolling')
    return ProxyAgent().zremrangebyrank(key, 0, -_MAX_SCROLLING - 1)


@cache_wrapper
def submit_missreturn_scrolling(cache_value, timestamp):
    """
    used for db
    """
    key = prefix_key('scrolling:missreturn')
    ret = ProxyAgent().zadd(key, timestamp, cache_value)
    if ProxyAgent().zcard(key) > _MAX_SCROLLING * 2:
        ProxyAgent().zremrangebyrank(key, 0, -_MAX_SCROLLING - 1)
    return ret


@cache_wrapper
def range_missreturn_scrolling(min_index=0, max_index=_MAX_SCROLLING - 1):
    """
    used for db
    """
    key = prefix_key('scrolling:missreturn')
    return ProxyAgent().zrevrange(key, min_index, max_index, withscores=True)


@cache_wrapper
def edit_cart_item(user_id, activity_id, number):
    key = prefix_key('cart:%s' % user_id)
    value = {
        'number': number,
        'ts': now_ts()
    }
    return ProxyAgent().hset(key, activity_id, json.dumps(value, ensure_ascii=False))


@cache_wrapper
def clear_cart_list(user_id):
    key = prefix_key('cart:%s' % user_id)
    return ProxyAgent().delete(key)


@cache_wrapper
def edit_cart_list(user_id, cart_dict):
    key = prefix_key('cart:%s' % user_id)
    return ProxyAgent().hmset(key, cart_dict)


@cache_wrapper
def remove_cart(user_id, activity_id):
    key = prefix_key('cart:%s' % user_id)
    return ProxyAgent().hdel(key, activity_id)


@cache_wrapper
def list_cart(user_id):
    """
    used for db
    """
    key = prefix_key('cart:%s' % user_id)
    return ProxyAgent().hgetall(key)


@cache_wrapper
def exists_cart(user_id, activity_id):
    key = prefix_key('cart:%s' % user_id)
    return ProxyAgent().hexists(key, activity_id)


_ACCOUNT_EXPIRE = 3600


@cache_wrapper
def save_account(user_id, account_value):
    key = prefix_key('account:%s' % user_id)
    return ProxyAgent().setex(key, _ACCOUNT_EXPIRE, account_value)


@cache_wrapper
def get_account(user_id):
    """
    used for cache
    """
    key = prefix_key('account:%s' % user_id)
    return ProxyAgent().get(key)


_UXIN_CREDENTIAL_EXPIRE = 30 * 24 * 3600


@cache_wrapper
def invalid_uxin_login_credential(phone_number, credential):
    key = prefix_key('uxin:%s:%s' % (phone_number, credential))
    return ProxyAgent().setex(key, _UXIN_CREDENTIAL_EXPIRE, 1)


@cache_wrapper
def is_uxin_login_credential_valid(phone_number, credential):
    key = prefix_key('uxin:%s:%s' % (phone_number, credential))
    return not ProxyAgent().get(key)


@cache_wrapper
def get_user_recharge(user_id):
    key = 'stats:recharge:%s' % user_id
    return ProxyAgent().get(key)


@cache_wrapper
def get_user_win_amount(user_id):
    key = 'stats:win:%s' % user_id
    return ProxyAgent().get(key)


@cache_wrapper
def get_user_stats(user_id):
    key = 'stats:user:%s' % user_id
    return ProxyAgent().hgetall(key)


@cache_wrapper
def get_daily_stats(date, user_id):
    key = 'stats:%s:%s' % (date, user_id)
    return ProxyAgent().hgetall(key)


_WEIXIN_TICKET_EXPIRE = 3600


@cache_wrapper
def get_weixin_ticket():
    key = prefix_key('weixin:ticket')
    return ProxyAgent().get(key)


@cache_wrapper
def set_weixin_ticket(ticket):
    key = prefix_key('weixin:ticket')
    return ProxyAgent().setex(key, _WEIXIN_TICKET_EXPIRE, ticket)


@cache_wrapper
def get_daily_coupons(phone_number):
    key = prefix_key('coupon:daily:%s' % phone_number)
    count = ProxyAgent().incr(key)
    ttl = left_seconds_today()
    ProxyAgent().expire(key, ttl)
    return count


_INVITER_TRACK_EXPIRE = 30 * 60


@cache_wrapper
def set_inviter_track(track_str, inviter_id):
    key = prefix_key('inviter:track:%s' % track_str)
    return ProxyAgent().setex(key, _INVITER_TRACK_EXPIRE, inviter_id)


@cache_wrapper
def get_inviter_track(track_str):
    key = prefix_key('inviter:track:%s' % track_str)
    return ProxyAgent().get(key)


@cache_wrapper
def check_discovery_item_notified(user_id, cmd_str):
    key = prefix_key('discovery:notified:%s' % user_id)
    return ProxyAgent().hget(key, cmd_str)


@cache_wrapper
def notify_discovery_item(user_id, cmd_str):
    key = prefix_key('discovery:notified:%s' % user_id)
    return ProxyAgent().hset(key, cmd_str, now_ts())


@cache_wrapper
def get_next_virtual_phone():
    key = prefix_key('virtual:phoneno')
    return ProxyAgent().incr(key)


@cache_wrapper
def update_zero_time(cache_dict):
    key = prefix_key('zerotime')
    return ProxyAgent().hmset(key, cache_dict)


@cache_wrapper
def get_zero_time():
    key = prefix_key('zerotime')
    return ProxyAgent().hgetall(key)


_TIPS_EXPIRE = 60


@cache_wrapper
def set_user_tips(user_id, tips):
    key = prefix_key('tips:%s' % user_id)
    return ProxyAgent().setex(key, _TIPS_EXPIRE, json.dumps(tips, ensure_ascii=False))


@cache_wrapper
def get_user_tips(user_id):
    key = prefix_key('tips:%s' % user_id)
    tips = ProxyAgent().get(key)
    return {} if not tips else json.loads(tips)


_COUPON_NOTIFY_EXPIRE = 24 * 3600


@cache_wrapper
def add_notify_coupon(user_id, coupon_id):
    key = prefix_key('couponnotify:%s' % user_id)
    return ProxyAgent().setex(key, _COUPON_NOTIFY_EXPIRE, coupon_id)


@cache_wrapper
def has_notify_coupon(user_id):
    key = prefix_key('couponnotify:%s' % user_id)
    return ProxyAgent().get(key)


@cache_wrapper
def get_ios_qq_group_uin():
    key = prefix_key('qqgroup:ios_uin')
    return ProxyAgent().get(key)


@cache_wrapper
def get_ios_qq_group_key():
    key = prefix_key('qqgroup:ios_key')
    return ProxyAgent().get(key)


@cache_wrapper
def get_android_qq_group_key():
    key = prefix_key('qqgroup:android_key')
    return ProxyAgent().get(key)


def get_cache_rank(year, week):
    key = prefix_key('weekrank:%s-%s' % (year, week))
    return ProxyAgent().get(key)


_RANK_EXPIRE = 600


@cache_wrapper
def set_cache_rank(year, week, rank_list):
    key = prefix_key('weekrank:%s-%s' % (year, week))
    return ProxyAgent().setex(key, _RANK_EXPIRE, rank_list)


@cache_wrapper
def get_current_partner_accu():
    key = prefix_key('partner_accu')
    return ProxyAgent().hgetall(key)


@cache_wrapper
def set_current_partner_accu(current_dict):
    key = prefix_key('partner_accu')
    return ProxyAgent().hmset(key, current_dict)


@cache_wrapper
def add_credit_pool(user_id, added_credit):
    key = prefix_key('creditpool')
    return ProxyAgent().incrby(key, added_credit)


@cache_wrapper
def clear_credit_pool():
    key = prefix_key('creditpool')
    return ProxyAgent().delete(key)


@cache_wrapper
def get_credit_pool():
    key = prefix_key('creditpool')
    return ProxyAgent().get(key)


@cache_wrapper
def get_current_sunday_term():
    key = prefix_key('sundayterm')
    return ProxyAgent().get(key)


@cache_wrapper
def set_next_sunday_term(term_id):
    key = prefix_key('sundayterm')
    return ProxyAgent().set(key, term_id)


@cache_wrapper
def set_jd_token(token, expired):
    k = prefix_key('jdtoken')
    ProxyAgent().setex(k, expired, token)


@cache_wrapper
def get_jd_token():
    return ProxyAgent().get(prefix_key('jdtoken'))


@cache_wrapper
def set_wechat_token(token, expired):
    k = prefix_key('wechattoken')
    ProxyAgent().setex(k, expired, token)


@cache_wrapper
def check_wechat_ttl():
    k = prefix_key('wechattoken')
    return ProxyAgent().ttl(k)


@cache_wrapper
def get_wechat_token():
    k = prefix_key('wechattoken')
    return ProxyAgent().get(k)

_HOT_KEYS_SIZE = 10


@cache_wrapper
def get_hot_keys():
    key = prefix_key('hotkeys')
    return ProxyAgent().zrevrangebyscore(key, '+inf', '-inf',
                                         start=0, num=_HOT_KEYS_SIZE)


@cache_wrapper
def add_hot_key(key_name):
    key = prefix_key('hotkeys')
    return ProxyAgent().zincrby(key, key_name)


@cache_wrapper
def get_top_buyer(activity_id):
    key = prefix_key('topbuy:%s' % activity_id)
    top_set = ProxyAgent().zrevrangebyscore(key, '+inf', '-inf',
                                            start=0, num=1, withscores=True)
    # trim, reserve top 10
    ProxyAgent().zremrangebyrank(key, 0, -11)
    return top_set


@cache_wrapper
def add_top_buyer(activity_id, user_id, buy_amount):
    key = prefix_key('topbuy:%s' % activity_id)
    return ProxyAgent().zadd(key, buy_amount, user_id)


@cache_wrapper
def set_first_buyer(activity_id, user_id):
    key = prefix_key('statsbuy:%s' % activity_id)
    return ProxyAgent().hsetnx(key, 'first', user_id)


@cache_wrapper
def set_last_buyer(activity_id, user_id):
    key = prefix_key('statsbuy:%s' % activity_id)
    return ProxyAgent().hsetnx(key, 'last', user_id)


@cache_wrapper
def get_stats_buy(activity_id):
    key = prefix_key('statsbuy:%s' % activity_id)
    return ProxyAgent().hgetall(key)


_ANNOUNCE_QUEUE_SIZE = 100


@cache_wrapper
def add_to_announce(activity_id):
    """
    开奖缓存队列
    """
    key = prefix_key('announcequeue')
    ProxyAgent().zadd(key, int(time.time()), activity_id)
    ProxyAgent().zremrangebyrank(key, 0, -_ANNOUNCE_QUEUE_SIZE - 1)


@cache_wrapper
def get_latest_announce(start=0, num=10):
    key = prefix_key('announcequeue')
    return ProxyAgent().zrevrangebyscore(key, '+inf', '-inf',
                                         start=start, num=num)


@cache_wrapper
def get_daily_privilege():
    """
    获取每日A+特权的发放数量
    """
    key = prefix_key('daily:privilege:a+')
    exists = ProxyAgent().exists(key)
    count = ProxyAgent().incr(key)
    if not exists:
        ttl = left_seconds_today()
        ProxyAgent().expire(key, ttl)
    return count


@cache_wrapper
def get_today_free_interval():
    """
    获取每日价格区间免费发放
    """
    key = prefix_key('daily:freeinterval')
    return ProxyAgent().hgetall(key)


@cache_wrapper
def incr_today_free_interval(index_str):
    key = prefix_key('daily:freeinterval')
    exists = ProxyAgent().exists(key)
    count = ProxyAgent().hincrby(key, index_str, 1)
    if not exists:
        ttl = left_seconds_today()
        ProxyAgent().expire(key, ttl)
    return count


@cache_wrapper
def lock_red_envelope(open_id):
    key = prefix_key('wechat:redenv:%s' % open_id)
    locked = ProxyAgent().setnx(key, 1)
    if locked:
        ProxyAgent().expire(key, 65)
    return locked


@cache_wrapper
def unlock_red_envelope(open_id):
    key = prefix_key('wechat:redenv:%s' % open_id)
    ProxyAgent().delete(key)


_BUY_RECORDS_EXPIRE = 3600 * 6


@cache_wrapper
def set_buy_records(user_id, activity_id, offset, limit, record_list):
    cache_key = md5('%s-%s-%s-%s' % (user_id, activity_id, offset, limit)).hexdigest()
    key = prefix_key('buyrecords:%s' % cache_key)
    return ProxyAgent().setex(key, _BUY_RECORDS_EXPIRE, json.dumps(record_list, ensure_ascii=False))


@cache_wrapper
def get_buy_records(user_id, activity_id, offset, limit):
    cache_key = md5('%s-%s-%s-%s' % (user_id, activity_id, offset, limit)).hexdigest()
    key = prefix_key('buyrecords:%s' % cache_key)
    record_list = ProxyAgent().get(key)
    return None if not record_list else json.loads(record_list)



@cache_wrapper
def set_gwallet_purchase_token(ptoken, orderid, userid, payid):
    key = prefix_key('purchasetoken:%s' % ptoken)
    dic = {'order_id': orderid, 'user_id': userid, 'pay_id': payid}
    ProxyAgent().hmset(key, dic)
    ProxyAgent().expire(key, 3600 * 72)

@cache_wrapper
def get_gwallet_purchase_token(ptoken):
    key = prefix_key('purchasetoken:%s' % ptoken)
    return ProxyAgent().hgetall(key)

@cache_wrapper
def set_gwallet_refund_endtime(end_time):
    key = prefix_key('gwrefundendtime')
    value = str(end_time)
    ProxyAgent().set(key, value)

@cache_wrapper
def get_gwallet_refund_endtime():
    key = prefix_key('gwrefundendtime')
    return ProxyAgent().get(key)