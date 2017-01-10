# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.cache import redis_cache
from luckycommon.db.activity import (get_activity, get_activity_users,
                                     get_template)
from luckycommon.db.coupon import get_coupon_by_id
from luckycommon.db.goods import get_goods
from luckycommon.db.show import get_show_by_id
from luckycommon.model.coupon import COUPON_STATUS
from luckycommon.model.show import SHOW_STATUS
from luckycommon.notification.db.notification import generate_notification
from luckycommon.notification.model.notification import NOTIFY_TYPE
from luckycommon.order.db.order import get_order
from luckycommon.push import PUSH_COMMANDS
from luckycommon.third.push_notification import push_to_android
from luckycommon.utils.template import generate_from_template

_LOGGER = logging.getLogger('lucky')


def push_fresh_award(user_id, is_coupon=False):
    """
    通知系统奖励
    """
    return
    if redis_cache.is_virtual_account(user_id):
        return
    if not is_coupon:
        content = generate_from_template('freshman_bonus')
    else:
        content = generate_from_template('freshman_coupon')
    generate_notification(user_id, content, NOTIFY_TYPE.CAMPAIGN)


def push_show_award(show):
    """
    通知晒单奖励
    """
    return
    user_id = show.user_id
    activity = get_activity(None, show.template_id, show.term_number)
    data_dict = {
        'activity_name': activity.name,
        'credit_num': show.verify_award,
    }
    # for latest version
    command = '%d#%d#%d' % (PUSH_COMMANDS.TO_AWARD_ALERT, show.id, show.verify_award)
    content = generate_from_template(
        'show_bonus', data_dict=data_dict, command=command)
    generate_notification(user_id, content, NOTIFY_TYPE.AWARD)
    # send sms
    if redis_cache.is_virtual_account(user_id):
        return
    short_title = get_template(show.template_id).short_title
    params = {
        "term_number": show.term_number,
        "short_title": short_title or activity.name,
        'credit_num': show.verify_award,
    }


def push_verify_fail(show):
    """
    通知晒单审核失败
    """
    return
    user_id = show.user_id
    activity = get_activity(None, show.template_id, show.term_number)
    data_dict = {
        'activity_name': activity.name,
    }
    # internal push
    content = generate_from_template('verify_fail_notify', data_dict=data_dict)
    generate_notification(user_id, content, NOTIFY_TYPE.AWARD)
    # notification
    content = generate_from_template(
        'verify_fail_notification', data_dict=data_dict)
    push_notification(user_id, content)


def push_revealing(activity_id):
    """
    通知快开奖
    """
    return
    activity = get_activity(activity_id)
    data_dict = {
        'activity_name': activity.name,
    }
    command = '%d#%s' % (PUSH_COMMANDS.TO_ACTIVITY, activity_id)
    notification_content = generate_from_template(
        'announce_notify', data_dict=data_dict, command=command)
    user_activitys = get_activity_users(activity_id)
    for user_activity in user_activitys:
        user_id = user_activity.user_id
        if redis_cache.is_virtual_account(user_id):
            continue
        # add push notification
        push_notification(user_id, notification_content)


def push_win(user_id, activity_id, order_id):
    """
    通知已中奖
    """
    if redis_cache.is_virtual_account(user_id):
        return
    activity = get_activity(activity_id)
    data_dict = {
        'activity_name': activity.name,
    }
    command = '%d#%s#%s' % (PUSH_COMMANDS.TO_ORDER, activity_id, activity.name)
    notification_content = generate_from_template(
        'award_notify', data_dict=data_dict, command=command)
    #push_notification(user_id, notification_content)
    push_extend = {
        'alert': {
            'type': 'win',
            'cover': activity.cover,
            'title': activity.short_title,
            'target_amount': activity.target_amount,
            'equal_price': float(get_goods(activity.goods_id).price),
            'cmd': ''
        }
    }
    generate_notification(user_id, notification_content, NOTIFY_TYPE.AWARD, extend=json.dumps(push_extend, ensure_ascii=False))
    # send email
    short_title = get_template(activity.template_id).short_title
    params = {
        "term_number": activity.term_number,
        "short_title": short_title or activity.name
    }


def push_shipping(order_id, shipping_info):
    """
    通知已发货
    """
    return
    try:
        order = get_order(order_id)
        activity = get_activity(order.activity_id)
        short_title = get_template(activity.template_id).short_title
        data_dict = {
            'activity_name': activity.name,
        }
        notification_content = generate_from_template(
            'shipping_notify', data_dict=data_dict)
        generate_notification(order.buyer, notification_content, NOTIFY_TYPE.AWARD)
    except Exception as e:
        _LOGGER.exception('push shipping exception, %s', e)


def push_receipt(order_id):
    """
    通知系统代为收货
    """
    return
    order = get_order(order_id)
    activity = get_activity(order.activity_id)
    data_dict = {
        'activity_name': activity.name,
    }
    notification_content = generate_from_template(
        'receipt_notify', data_dict=data_dict)
    generate_notification(order.buyer, notification_content, NOTIFY_TYPE.AWARD)


def push_refunding(activity_id, refunded_users):
    """
    通知90天未凑够人数，返回夺宝币
    """
    return
    activity = get_activity(activity_id)
    user_activitys = get_activity_users(activity_id)
    for user_activity in user_activitys:
        user_id = user_activity.user_id
        refunded_price = refunded_users.get(user_id)
        if refunded_price:
            data_dict = {
                'activity_name': activity.name,
                'refunded_price': refunded_price
            }
            notification_content = generate_from_template(
                'refunding_notify', data_dict=data_dict)
            # add push notification
            push_notification(user_id, notification_content)
            generate_notification(user_id, notification_content, NOTIFY_TYPE.SYSTEM)


def push_out_of_stock(activity_id):
    """
    通知缺货, 返还夺宝币
    """
    pass


def push_campaign_apply(user_id, campaign_title, campaign_url):
    """
    通知活动参与成功
    """
    return
    if redis_cache.is_virtual_account(user_id):
        return
    data_dict = {
        'campaign_title': campaign_title,
    }
    command = u'%d#%s#%s' % (PUSH_COMMANDS.TO_CAMPAIGN_APPLY_ALERT, campaign_title, campaign_url)
    content = generate_from_template('campaign_apply', data_dict=data_dict, command=command)
    generate_notification(user_id, content, NOTIFY_TYPE.CAMPAIGN)


def push_campaign_award(user_id, campaign_title, award_content):
    """
    通知活动奖励到账
    """
    return
    if redis_cache.is_virtual_account(user_id):
        return
    data_dict = {
        'campaign_title': campaign_title,
        'award_content': award_content,
    }
    command = u'%d#%s' % (PUSH_COMMANDS.TO_CAMPAIGN_AWARD_ALERT, campaign_title)
    content = generate_from_template('campaign_award', data_dict=data_dict, command=command)
    generate_notification(user_id, content, NOTIFY_TYPE.CAMPAIGN)


def notify_show(show_id):
    """
    提醒用户晒单
    """
    return
    show = get_show_by_id(show_id)
    if show.status == SHOW_STATUS.WAIT_SHOW:
        # internal notify
        user_id = show.user_id
        activity = get_activity(None, show.template_id, show.term_number)
        short_title = get_template(show.template_id).short_title
        data_dict = {
            "term_number": show.term_number,
            "short_title": short_title or activity.name,
        }
        command = u'%d#%s' % (PUSH_COMMANDS.TO_EDIT_SHOW, show_id)
        content = generate_from_template('notify_show', data_dict=data_dict, command=command)
        generate_notification(user_id, content, NOTIFY_TYPE.AWARD)
        # push notification
        content = generate_from_template('notify_show_notification', command=command)
        push_notification(user_id, content)


def notify_coupon(coupon_id):
    """
    提醒用户使用红包
    """
    return
    coupon = get_coupon_by_id(coupon_id)
    # 检查今天是否已经推送过
    if redis_cache.has_notify_coupon(coupon.user_id):
        return
    if coupon.status == COUPON_STATUS.UNUSED:
        # push notification
        command = u'%d#' % PUSH_COMMANDS.TO_OPEN_COUPON
        content = generate_from_template('notify_coupon_notification', command=command)
        push_notification(coupon.user_id, content)
        redis_cache.add_notify_coupon(coupon.user_id, coupon_id)


def notify_level_up(user_id, current_level, level_name):
    return
    data_dict = {
        "level": current_level,
    }
    command = u'%d#%s#%s' % (PUSH_COMMANDS.TO_SHOW_LEVEL_UP, current_level, level_name)
    content = generate_from_template('notify_level_up', data_dict=data_dict, command=command)
    push_notification(user_id, content)


def push_feedback_ack(user_id):
    """
    通知feedback ACK
    """
    return
    content = generate_from_template('feedback_ack')
    generate_notification(user_id, content, NOTIFY_TYPE.SYSTEM)


def push_sign_award(user_id, award_amount):
    """
    push 获得每日签到幸运元宝
    """
    return
    try:
        params = {
            "award_amount": award_amount,
        }
    except Exception as e:
        _LOGGER.exception('push sign award exception, %s-%s %s', user_id, award_amount, e)


def push_recharge_campaign_award(user_id, campaign_title):
    """
    充值活动成就达成通知
    """
    return
    try:
        params = {
            "campaign_title": campaign_title,
        }
        _LOGGER.info('push recharge campaign, %s-%s', user_id, campaign_title)
    except Exception as e:
        _LOGGER.exception('push recharge campaign exception, %s-%s %s', user_id, campaign_title, e)


def push_notification(user_id, content):
    return
    try:
        data = json.loads(content)
        title = data['title'].encode('utf-8')
        body = data['content'].encode('utf-8')
        payload = {
            'title': title,
            'content': body
        }
        if data['command']:
            command = data['command'].encode('utf-8')
            payload['command'] = command
        push_to_android(user_id, title, body, payload)
    except Exception as e:
        _LOGGER.exception('push_notification exception, %s', e)
