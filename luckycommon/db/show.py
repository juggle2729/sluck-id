# -*- coding: utf-8 -*-
import logging

from sqlalchemy import func

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.activity import ActivityTemplate, ActivityWin, Activity
from luckycommon.order.model.order import AwardedOrder, ORDER_STATUS
from luckycommon.model.show import SHOW_STATUS, AnnounceShow, HIGHLIGHT_TAG
from luckycommon.utils.tz import now_ts
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import (AuthenticateError, ParamError,
                                          ResourceNotFound)
from luckycommon.utils.orm import get_count
from luckycommon.db.helper import (get_orderby, parse_query_dct,
                                   paginate, generate_filter)


_LOGGER = logging.getLogger('lucky')

_TIMELINE_SIZE = 10

ROAD_MAP = {
    SHOW_STATUS.WAIT_SHOW: {
        SHOW_STATUS.WAIT_VERIFY: {}
    },
    SHOW_STATUS.WAIT_VERIFY: {
        SHOW_STATUS.VERIFY_PRE: {"flag": {"need_award": False}},
        SHOW_STATUS.VERIFY_SUCCESS: {"flag": {"need_award": True}},
        SHOW_STATUS.VERIFY_FAIL: {"flag": {"push_fail": True}}
    },
    SHOW_STATUS.VERIFY_PRE: {
        SHOW_STATUS.VERIFY_SUCCESS: {"flag": {"need_award": True}},
        SHOW_STATUS.VERIFY_FAIL: {"flag": {"push_fail": True}}
    },
    SHOW_STATUS.VERIFY_FAIL: {
        SHOW_STATUS.WAIT_SHOW: {},
        SHOW_STATUS.VERIFY_SUCCESS: {"flag": {"need_award": True}}
    }
}


@sql_wrapper
def count_show_by_template(template_id):
    return orm.session.query(func.count(AnnounceShow)).filter(
        AnnounceShow.template_id == template_id).filter(
        AnnounceShow.status > 1).scalar()


@sql_wrapper
def get_user_shows(user_id, limit=0, offset=0):
    query = AnnounceShow.query.filter(AnnounceShow.user_id == user_id)
    query = query.order_by(AnnounceShow.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all()


@sql_wrapper
def get_user_verified_shows(user_id, limit=0, offset=0):
    query = AnnounceShow.query.filter(AnnounceShow.user_id == user_id).filter(
        AnnounceShow.status == SHOW_STATUS.VERIFY_SUCCESS)
    query = query.order_by(AnnounceShow.verified_at.desc())
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    return query.all()


@sql_wrapper
def create_virtual_show(info):
    win_info = ActivityWin.query.filter(
        ActivityWin.activity_id == info['activity_id']).one()
    ac_info = Activity.query.filter(
        Activity.id == info['activity_id']).one()
    show = AnnounceShow()
    show.order_id = win_info.order_id
    show.user_id = win_info.winner
    show.template_id = ac_info.template_id
    show.term_number = ac_info.term_number
    show.status = SHOW_STATUS.WAIT_VERIFY
    show.title = info['title']
    show.content = info['content']
    show.images = info['images']
    show.verify_award = 0
    show.save()

    return show.as_dict()


@sql_wrapper
def list_shows(query_dct):
    is_virtual = query_dct.pop('is_virtual', None)
    activity_name = query_dct.pop('activity_name', None)
    query_dct = parse_query_dct(query_dct, AnnounceShow)
    query = AnnounceShow.query
    if is_virtual is not None:
        is_virtual = True if is_virtual == '1' else False
        query = query.join(Account, Account.id == AnnounceShow.user_id).filter(
            Account.is_virtual == is_virtual)
    if activity_name is not None:
        query = query.join(
            ActivityTemplate, ActivityTemplate.id == AnnounceShow.template_id).filter(
            ActivityTemplate.name.like('%%%s%%' % activity_name))
    query = query.filter(generate_filter(query_dct, AnnounceShow))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), AnnounceShow)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    return query.all(), total_count


@sql_wrapper
def get_latest_highlight_shows():
    query = AnnounceShow.query.filter(AnnounceShow.status == SHOW_STATUS.VERIFY_SUCCESS)\
                        .filter(AnnounceShow.highlight > 0)\
                        .order_by(AnnounceShow.verified_at.desc())
    query = query.order_by(AnnounceShow.verify_award.desc())
    query = query.limit(2)
    return query.all()


@sql_wrapper
def get_shows_by_time(start_ts, max_ts=-1, template_id=None,
                      limit=_TIMELINE_SIZE):
    if template_id:
        query = AnnounceShow.query.filter(
            AnnounceShow.template_id == template_id)
    else:
        query = AnnounceShow.query

    query = query.filter(AnnounceShow.status == SHOW_STATUS.VERIFY_SUCCESS)\
                 .filter(AnnounceShow.verified_at > start_ts)

    #if not template_id:
    #    query = query.filter(AnnounceShow.verify_award > 200)
    if max_ts != -1:
        query = query.filter(AnnounceShow.verified_at < max_ts)
    query = query.order_by(AnnounceShow.verified_at.desc())
    if limit > 0:
        query = query.limit(limit)
    return query.all()


@sql_wrapper
def get_show_by_id(show_id):
    show = AnnounceShow.query.filter(AnnounceShow.id == show_id).first()
    if not show:
        raise ResourceNotFound('show id not invalid')
    return show


@sql_wrapper
def get_show_by_order(order_id):
    show = AnnounceShow.query.filter(AnnounceShow.order_id == order_id).first()
    if not show:
        raise ResourceNotFound('show id not invalid')
    return show


@sql_wrapper
def get_show_by_template(template_id, term_number):
    show = AnnounceShow.query.filter(AnnounceShow.template_id == template_id)\
                             .filter(AnnounceShow.term_number == term_number)\
                             .first()
    return show


@sql_wrapper
def create_show(template_id, term_number, order_id, user_id):
    announce_show = AnnounceShow()
    announce_show.template_id = template_id
    announce_show.term_number = term_number
    announce_show.order_id = order_id
    announce_show.user_id = user_id
    announce_show.save()
    return announce_show


@sql_wrapper
def update_show(user_id, show_id, title, content, images):
    announce_show = AnnounceShow.query.with_for_update().filter(
        AnnounceShow.id == show_id).one()
    if announce_show.user_id != user_id:
        raise AuthenticateError('not access')
    if announce_show.status == SHOW_STATUS.VERIFY_SUCCESS:
        raise ParamError('status invalid')
    announce_show.title = title
    announce_show.verified_at = now_ts()
    announce_show.content = content
    announce_show.images = images
    announce_show.status = SHOW_STATUS.VERIFY_SUCCESS
    # modify order status
    order = AwardedOrder.query.filter(
        AwardedOrder.order_id == announce_show.order_id).one()
    if order.status == ORDER_STATUS.DEAL:
        order.status = ORDER_STATUS.SHOW
    announce_show.save()


@sql_wrapper
def update_mutable(show_id, dct):
    show = AnnounceShow.query.with_for_update().filter(
        AnnounceShow.id == show_id).one()
    for k in dct:
        setattr(show, k, dct[k])
    show.save()


@sql_wrapper
def verify_show(show_id, status, verify_comment,
                verify_award, highlight_tag):
    if verify_award < 0:
        raise ParamError('award value invalid')
    flags = {
        "need_award": False,
        "push_fail": False
    }
    announce_show = AnnounceShow.query.with_for_update().filter(
        AnnounceShow.id == show_id).one()
    old_status = announce_show.status
    if status != old_status:
        if old_status not in ROAD_MAP or status not in ROAD_MAP[old_status]:
            raise ParamError('status %s -> %s not allowed' %
                             (old_status, status))
        announce_show.status = status
        flags.update(ROAD_MAP[old_status][status].get('flag', {}))
    if flags['push_fail']:
        announce_show.verify_comment = verify_comment
    if flags['need_award'] or status == SHOW_STATUS.VERIFY_PRE:
        announce_show.verify_award = verify_award
    if highlight_tag in HIGHLIGHT_TAG.to_dict():
        announce_show.highlight = highlight_tag
    announce_show.verified_at = now_ts()
    announce_show.save()
    return announce_show, flags['need_award'], flags['push_fail']
