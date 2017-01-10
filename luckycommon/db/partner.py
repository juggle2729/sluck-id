# -*- coding: utf-8 -*-
import json
import copy
from datetime import timedelta

from sqlalchemy import func, distinct

from luckycommon.model import orm
from luckycommon.model.partner import *
from luckycommon.model.pay import Pay

from luckycommon.db import coupon as coupon_db

from luckycommon.utils.orm import get_count
from luckycommon.utils import exceptions as err
from luckycommon.utils.decorator import sql_wrapper


@sql_wrapper
def get_direct_partners(user_id):
    """
    获取一层好友列表
    """
    partner_list = []
    items = Partner.query.filter(Partner.inviter_id == user_id).all()
    for item in items:
        partner_list.append(item.user_id)
    return partner_list


@sql_wrapper
def get_coupon_status(user_id):
    return PartnerCoupon.query.filter(PartnerCoupon.user_id == user_id).first()


@sql_wrapper
def init_coupon_status(user_id):
    partner_coupon = PartnerCoupon.query.filter(PartnerCoupon.user_id == user_id).with_lockmode('update').first()
    if not partner_coupon:
        count = get_count(Partner.query.filter(Partner.inviter_id == user_id))
        partner_coupon = PartnerCoupon()
        partner_coupon.user_id = user_id
        partner_coupon.partner_count = count
        coupon_status = copy.deepcopy(DEFAULT_COUPON_STATUS)
        for c in coupon_status:
            if c['status'] == 0 and c['count'] <= count:
                c['status'] = 1
        partner_coupon.coupon_status = json.dumps(coupon_status)
        partner_coupon.save()
    return partner_coupon


@sql_wrapper
def update_coupon_status(user_id): 
    partner_coupon = PartnerCoupon.query.filter(PartnerCoupon.user_id == user_id).with_lockmode('update').first()
    count = get_count(Partner.query.filter(Partner.inviter_id == user_id))
    partner_coupon.partner_count = count
    coupon_status = json.loads(partner_coupon.coupon_status)
    for c in coupon_status:
        if c['status'] == 0 and c['count'] <= count:
            c['status'] = 1
    partner_coupon.coupon_status = json.dumps(coupon_status)
    partner_coupon.save()
    return partner_coupon


@sql_wrapper
def activate_coupon(user_id, level_id):
    partner_coupon = PartnerCoupon.query.filter(PartnerCoupon.user_id == user_id).with_lockmode('update').first()
    coupon_status = json.loads(partner_coupon.coupon_status)
    c = coupon_status[level_id]
    if c['status'] != 1:
        raise err.ParamError('level status invalid')
    coupon_status[level_id]['status'] = 2
    coupon_tid = COUPON_LIST[level_id]
    coupon = coupon_db.award_coupon_in_transaction(user_id, coupon_tid)
    partner_coupon.coupon_status = json.dumps(coupon_status)
    partner_coupon.save()
    return coupon


@sql_wrapper
def get_partner_rewards(user_id, limit=0, offset=0):
    query = PartnerReward.query.filter(PartnerReward.user_id == user_id)\
                               .filter(PartnerReward.relation_level < 3)
    query = query.order_by(PartnerReward.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
        query = query.offset(offset)
    return query.all()


@sql_wrapper
def add_reward_record(user_id, partner_id, relation_level, reward_amount):
    partner_reward = PartnerReward()
    partner_reward.user_id = user_id
    partner_reward.partner_id = partner_id
    partner_reward.relation_level = relation_level
    partner_reward.amount = reward_amount
    partner_reward.balance = 0
    partner_reward.save()


@sql_wrapper
def get_reward_by_level(user_id, level):
    """
    获取某级别好友的返利额度
    """
    query = orm.session.query(orm.func.sum(PartnerReward.amount))\
                       .filter(PartnerReward.user_id == user_id)\
                       .filter(PartnerReward.relation_level == level)
    res = query.first()
    return res[0] or 0


def _update_children_invites(user_id, invite_list):
    """
    we can do it in async later
    """
    items = Partner.query.filter(Partner.inviter_id == user_id).all()
    if not items:
        return
    for item in items:
        l = [item.inviter_id]
        l.extend(invite_list)
        item.invite_list = ','.join([str(i) for i in l])
        item.save()
        _update_children_invites(item.user_id, l)


@sql_wrapper
def get_user_inviter(user_id):
    return Partner.query.filter(Partner.user_id == user_id).first()


@sql_wrapper
def create_relation(user_id, invite_list):
    # bind
    account_inviter = Partner()
    account_inviter.user_id = user_id
    account_inviter.inviter_id = invite_list[0]
    account_inviter.invite_list = ','.join([str(item) for item in invite_list])
    account_inviter.save()
    # update children invite list
    _update_children_invites(user_id, invite_list)


@sql_wrapper
def get_report(start_day):
    end_day = start_day + timedelta(days=1)
    resp = {}
    invited_count = orm.session.query(func.count(Partner.user_id)).filter(
        Partner.created_at >= start_day).filter(
        Partner.created_at < end_day).scalar()
    resp['invited'] = invited_count or 0
    inviter_count = orm.session.query(
        func.count(distinct(Partner.inviter_id))).filter(
        Partner.created_at >= start_day).filter(
        Partner.created_at < end_day).scalar()
    resp['inviter'] = inviter_count or 0

    invited_recharged_count, invited_recharged_total = orm.session.query(
        func.count(distinct(Pay.user_id)), func.sum(Pay.price)).join(
        Partner, Partner.user_id == Pay.user_id).filter(
        Partner.created_at >= start_day).filter(
        Partner.created_at < end_day).filter(
        Pay.status == 2).filter(
        Pay.created_at >= start_day).filter(
        Pay.created_at < end_day).first()

    resp['invited_recharged_count'], resp['invited_recharged_total'] = \
        invited_recharged_count or 0, int(float(invited_recharged_total or 0))
    return resp


@sql_wrapper
def get_releation_dist():
    # NOTE: here, assume user_id length is 8, this may be wrong...
    id_length = 8
    resp = {
        'level_1': {},
        'level_2': {},
        'level_3': {}
    }
    for k in range(3):
        l = (k + 1) * id_length + k
        count = orm.session.query(func.count(Partner.user_id)).filter(
            func.length(Partner.invite_list) >= l).scalar()
        resp['level_' + str(k + 1)]['count'] = count or 0

    items = orm.session.query(
        PartnerReward.relation_level,
        func.count(PartnerReward.user_id),
        func.sum(PartnerReward.amount)).group_by(
        PartnerReward.relation_level).all()

    for level, count, amount in items:
        resp['level_' + str(level)]['bonus_count'] = count or 0
        resp['level_' + str(level)]['bonus_amount'] = int(float(amount or 0))

    return resp
