# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.model.activity import Revealed
from luckyapi.model.show import ShowLite, ShowDetail
from luckyapi.logic.crowdfunding import get_revealed

from luckycommon.cache import redis_cache
from luckycommon.account.db import account as account_db
from luckycommon.model.show import SHOW_STATUS
from luckycommon.db.show import (get_user_shows, get_show_by_id,
                                 get_user_verified_shows, get_latest_highlight_shows,
                                 get_shows_by_time, get_show_by_template)
from luckycommon.db.activity import get_activitys_by_ids, get_activity, get_activity_win

from luckycommon.utils import id_generator
from luckycommon.utils.tz import utc_to_local
from luckycommon.utils.exceptions import AuthenticateError

from future.utils import raise_with_traceback


_LOGGER = logging.getLogger('lucky')

_DEFAULT_PAGE_SIZE = 20


def _create_show_lite_list(show_list):
    id_list = []
    for s in show_list:
        a_id = id_generator.generate_uuid(
            'activity:%s:%s' % (s.template_id, s.term_number))
        id_list.append(a_id)
    activitys = get_activitys_by_ids(id_list)
    a_dict = dict([('%s:%s' % (a.template_id, a.term_number), a)
                   for a in activitys])
    lite_list = []
    id_set = set()
    for show in show_list:
        lite = ShowLite()
        lite.id = show.id
        if lite.id in id_set:
            continue
        id_set.add(lite.id)
        lite.gid = show.template_id
        lite.term = show.term_number
        activity = a_dict.get('%s:%s' % (lite.gid, lite.term))
        lite.unit = activity.unit
        lite.pk = activity.pk
        lite.goods = {
            'name': activity.name,
            'desc': activity.desc,
            'cover': activity.cover or activity.images.split(',')[0]
        }
        if show.status == SHOW_STATUS.WAIT_SHOW:
            revealed_dict = get_revealed(activity, use_cache=True)
            revealed = Revealed()
            revealed.activity_id = activity.id
            revealed.term = activity.term_number
            revealed.pk = activity.pk
            revealed.target_amount = activity.target_amount
            revealed.name = activity.name
            revealed.lucky_number = revealed_dict['lucky_number']
            revealed.reveal_time = revealed_dict['reveal_time']
            revealed.winner = revealed_dict['winner']
            lite.revealed = revealed
            lite.order_id = show.order_id
        else:
            cached_winner = redis_cache.get_activity_winner(activity.id)
            if cached_winner:
                winner_info = json.loads(cached_winner)
                account = account_db.get_account(winner_info.get('uid'), use_cache=True)
                lite.winner = {
                    'uid': winner_info.get('uid'),
                    'avatar': account.avatar_id,
                    'nick_name': account.nick_name,
                    'time': utc_to_local(activity.announced_at).strftime('%Y-%m-%d %H:%M:%S'),
                    'num_count': winner_info.get('num_count') or len(winner_info.get('numbers'))
                }
            else:
                win = get_activity_win(activity.id)
                if win:
                    try:
                        info = {} if not win.announce_info else json.loads(win.announce_info)
                    except Exception:
                        _LOGGER.info('#bug# activity id: %s' % activity.id)
                        info = {}
                    if info.get('winner'):
                        winner_info = info['winner']
                        number_count = winner_info.get(
                            'num_count') or len(winner_info.get('numbers'))
                        account = account_db.get_account(winner_info.get('uid'), use_cache=True)
                        lite.winner = {
                            'uid': winner_info.get('uid'),
                            'avatar': account.avatar_id,
                            'nick_name': account.nick_name,
                            'time': utc_to_local(activity.announced_at).strftime('%Y-%m-%d %H:%M:%S'),
                            'num_count': number_count
                        }
        lite.title = show.title
        lite.content = show.content
        lite.images = show.images
        lite.status = show.status
        if show.status == SHOW_STATUS.VERIFY_PRE:
            lite.status = SHOW_STATUS.WAIT_VERIFY
        lite.highlight = show.highlight
        lite.show_time = utc_to_local(
            show.updated_at).strftime('%Y-%m-%d %H:%M:%S')
        lite.verified_at = show.verified_at
        lite_list.append(lite)

    return lite_list


def view_my_shows(user_id, page, size):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    show_list = get_user_shows(user_id, limit, offset)
    return _create_show_lite_list(show_list)


def view_other_shows(user_id, page, size):
    limit = _DEFAULT_PAGE_SIZE if not size or size > _DEFAULT_PAGE_SIZE else size
    if not page or page < 1:
        page = 1
    offset = 0 if not page else (page - 1) * limit
    show_list = get_user_verified_shows(user_id, limit, offset)
    return _create_show_lite_list(show_list)


def view_shows_timeline(start_ts, max_ts, template_id=None):
    show_list = []
    if not template_id and start_ts == 0 and max_ts == -1:
        show_list.extend(get_latest_highlight_shows())
    s_list = get_shows_by_time(start_ts, max_ts, template_id)
    show_list.extend(s_list)
    return _create_show_lite_list(show_list)


def _create_show_detail(show):
    detail = ShowDetail()
    detail.id = show.id
    detail.gid = show.template_id
    detail.term = show.term_number
    activity = get_activity(None, detail.gid, detail.term)
    detail.unit = activity.unit
    detail.price = activity.target_amount
    detail.goods = {
        'name': activity.name,
        'desc': activity.desc,
        'cover': activity.cover or activity.images.split(',')[0]
    }
    detail.title = show.title
    detail.content = show.content
    detail.images = show.images
    detail.status = show.status
    if show.status == SHOW_STATUS.VERIFY_PRE:
        detail.status = SHOW_STATUS.WAIT_VERIFY
    detail.show_time = utc_to_local(
        show.updated_at).strftime('%Y-%m-%d %H:%M:%S')
    detail.verified_at = show.verified_at
    detail.highlight = show.highlight
    detail.verify_comment = show.verify_comment
    revealed_dict = get_revealed(activity, use_cache=True)
    revealed = Revealed()
    revealed.activity_id = activity.id
    revealed.term = activity.term_number
    revealed.name = activity.name
    revealed.pk = activity.pk
    revealed.lucky_number = revealed_dict['lucky_number']
    revealed.reveal_time = revealed_dict['reveal_time']
    revealed.winner = revealed_dict['winner']
    detail.revealed = revealed
    return detail


def view_show_detail(user_id, show_id):
    show = get_show_by_id(show_id)
    if show.status != SHOW_STATUS.VERIFY_SUCCESS and\
            show.user_id != user_id:
        raise AuthenticateError('not access')
    return _create_show_detail(show)


def view_my_show_detail(user_id, template_id, term_number):
    show = get_show_by_template(template_id, term_number)
    if show.user_id != user_id:
        raise AuthenticateError('not access')
    return _create_show_detail(show)
