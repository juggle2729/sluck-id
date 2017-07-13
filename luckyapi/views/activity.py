# -*- coding: utf-8 -*-
import json
import logging

from luckyapi.model.activity import Template
from luckyapi.logic.crowdfunding import (create_activity_template,
                                         start_next_activity,
                                         view_activitys,
                                         view_my_activitys,
                                         view_activity_detail,
                                         view_revealed_list,
                                         view_calc_record,
                                         view_activitys_by_tids, view_users_in_activity)
from luckycommon.order.handler import (
    view_buy_record_list,
    view_buy_record_list_timeline, view_detail_numbers)

from luckycommon.cache import redis_cache

from luckycommon.account.db import account as account_db
from luckycommon.db import category as category_db
from luckycommon.db import search as search_db
from luckycommon.db import activity as activity_db
from luckycommon.sensor.sensor_handler import get_sensor_status

from luckycommon.utils.api import token_required, parse_p, filter_apples, filter_gp
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import (ParamError, AuthenticateError,
                                          ResourceInsufficient,
                                          ResourceNotFound)

from future.utils import raise_with_traceback

from django.conf import settings
from django.utils.encoding import smart_unicode
from django.views.decorators.http import require_GET, require_POST

_LOGGER = logging.getLogger('lucky')

DEBUG_USER = settings.DEBUG_USER


def _filter_star(request, item_list):
    p = parse_p(request.GET.get('p'))
    if int(p.get('cvc')) <= 124:
        filter_list = []
        for item in item_list:
            filter_list.append(item)
        return filter_list
    else:
        filter_list = []
        for item in item_list:
            if int(item.get('gid')) in (774, 775, 780, 781):
                item['is_star'] = 1
            filter_list.append(item)
        return filter_list


@require_POST
@response_wrapper
@token_required
def create_template(request):
    """
    创建活动模板
    """
    if request.user_id != DEBUG_USER:
        raise AuthenticateError()
    try:
        template = Template()
        data = smart_unicode(request.body)
        template.set_fromdict(json.loads(data))
    except ValueError as e:
        raise ParamError('request body is not valid json.(%s)' % e)

    template = create_activity_template(0, template)
    data = {
        'template_id': template.id
    }

    return data


@require_POST
@response_wrapper
@token_required
def start_template(request, template_id):
    """
    开始活动
    """
    if request.user_id != DEBUG_USER:
        raise AuthenticateError()
    _LOGGER.info('start template %s ...' % template_id)
    activity = start_next_activity(0, template_id)
    if not activity:
        raise ResourceInsufficient('stock insufficient')
    data = {
        'id': activity.id
    }
    return data


@require_GET
@response_wrapper
def get_activitys(request):
    """
    get activity list by parameters
    `sort_id` 1-最热门，2-最新，3-进度
    `unit` 1元区, 10元区
    `status` 活动状态，1-进行中 2-即将揭晓 3-已经揭晓

    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        sort_id = int(request.GET['sort_id']) if request.GET.get(
            'sort_id') else None
        unit = int(request.GET['unit']) if request.GET.get('unit') else None
        status = int(request.GET['status']) if request.GET.get(
            'status') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    activitys, count = view_activitys(page, size, sort_id, unit, status)
    activitys = filter_apples(request, activitys)
    activitys = filter_gp(request, activitys)
    activitys = _filter_star(request, activitys)
    data = {
        'list': activitys,
        'page': page if page > 0 else 1,
        'size': len(activitys),
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
def get_activity_detail(request, activity_id):
    """
    get activity detail
    """
    activity_detail = view_activity_detail(request.user_id, activity_id)
    return activity_detail


@require_GET
@response_wrapper
def get_activity_detail_by_term(request, template_id, term_number):
    """
    get activity detail
    """
    activity_detail = view_activity_detail(request.user_id, template_id=template_id, term_number=term_number, use_cache=True)
    return activity_detail


@require_GET
@response_wrapper
def get_last_revealed(request, template_id):
    """
    往期揭晓
    get last winner of template
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))
    revealed_list, count = view_revealed_list(page, size, template_id)
    data = {
        'list': revealed_list,
        'page': page if page > 0 else 1,
        'size': len(revealed_list),
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
def get_buy_records(request, activity_id):
    """
    购买记录
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        only_me = int(request.GET.get('my', 0))
        other = int(request.GET.get('other', 0))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    if only_me and not request.user_id:
        raise AuthenticateError('not login')

    user_id = request.user_id if only_me else None
    if other:
        user_id = other

    # check version to response seperate data
    tracks = parse_p(request.GET.get('p'))
    client_chn = tracks.get('chn', None)
    client_version_code = int(tracks.get('cvc', 0))
    is_old_version = True
    if not tracks or (client_chn != 'ios' and client_version_code >= 10):
        is_old_version = False
    buy_record_list, count = view_buy_record_list(
        user_id, page, size, activity_id, old_version=is_old_version)
    data = {
        'list': buy_record_list,
        'page': page if page > 0 else 1,
        'size': len(buy_record_list),
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
def get_buy_records_timeline(request, activity_id):
    """
    获取购买记录时间线，不适用于查看单个用户的记录
    ts取订单编号
    """
    try:
        start_ts = int(request.GET.get('start_ts', 0))
        max_ts = int(request.GET.get('max_ts', -1))
    except Exception as e:
        raise_with_traceback(ParamError(e))

    buy_record_list = view_buy_record_list_timeline(
        activity_id, start_ts, max_ts)
    data = {
        'list': buy_record_list,
    }
    return data


@require_GET
@response_wrapper
def get_record_numbers(request, activity_id, record_id):
    """
    获取某一条购买记录的所有号码
    """
    numbers = view_detail_numbers(record_id)
    data = {
        'numbers': numbers
    }
    return data


@require_GET
@response_wrapper
def get_calc_record(request, activity_id):
    """
    查看开奖数据
    """
    calc_record = view_calc_record(activity_id)
    return calc_record


@require_GET
@response_wrapper
def get_billboard(request, activity_id):
    """
    查看商品的榜单：沙发/包尾/土豪
    """
    activity = activity_db.get_activity(activity_id)
    if not (activity.buy_limit == 0 and activity.target_amount > 100):
        raise ResourceNotFound()
    top_set = redis_cache.get_top_buyer(activity_id)
    stats_buy = redis_cache.get_stats_buy(activity_id)
    most_buyer, most_amount = (None, 0) if not top_set else list(top_set)[0]
    first_buyer = stats_buy.get('first')
    last_buyer = stats_buy.get('last')
    data = {}
    if most_buyer:
        rich_account = account_db.get_account(most_buyer, use_cache=True)
        data.update({
            'rich': {
                'uid': rich_account.id,
                'nick_name': rich_account.nick_name,
                'avatar_id': rich_account.avatar_id,
                'buy_amount': most_amount
            }
        })
    if first_buyer:
        first_account = account_db.get_account(first_buyer, use_cache=True)
        data.update({
            'first': {
                'uid': first_account.id,
                'nick_name': first_account.nick_name,
                'avatar_id': first_account.avatar_id
            }
        })
    if last_buyer:
        last_account = account_db.get_account(last_buyer, use_cache=True)
        data.update({
            'last': {
                'uid': last_account.id,
                'nick_name': last_account.nick_name,
                'avatar_id': last_account.avatar_id
            }
        })
    return data


@require_GET
@response_wrapper
def get_users_in_activity(request, activity_id):
    return view_users_in_activity(activity_id)


@require_GET
@response_wrapper
@token_required
def get_my_activitys(request):
    """
    查看我的夺宝记录
    """
    user_id = request.user_id
    if not user_id:
        raise AuthenticateError('not login')

    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        only_win = int(request.GET['win']) if request.GET.get('win') else 0
        status = int(request.GET['status']) if request.GET.get(
            'status') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    a_list, count = view_my_activitys(user_id, page, size, only_win, status)
    data = {
        'list': a_list,
        'page': page if page > 0 else 1,
        'size': size if size else count,
        'total_count': count
    }
    return data


@require_GET
@response_wrapper
def get_all_categorys(request):
    """
    查看所有分类 
    """
    category_list = []
    items = category_db.get_all_categorys()
    for item in items:
        category_list.append({
            'id': item.id,
            'name': item.name,
            'icon': item.icon,
            'tag': item.tag,
        })
    data = {
        'categorys': category_list
    }
    return data


@require_GET
@response_wrapper
def get_category_activitys(request, category_id):
    """
    查看某分类下商品
    """
    try:
        category_id = int(category_id)
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except:
        raise ParamError('param invalid')
    tids = category_db.get_category_aids(category_id)
    activitys = view_activitys_by_tids(tids, page, size)
    activitys = filter_apples(request, activitys)
    activitys = filter_gp(request, activitys)
    activitys = _filter_star(request, activitys)
    data = {
        'list': activitys,
        'page': page if page > 0 else 1,
        'size': len(activitys),
    }
    return data


@require_GET
@response_wrapper
def get_hot_keys(request):
    """
    查看商品搜索热词
    """
    hot_list = []
    hot_keys = redis_cache.get_hot_keys()
    data = {
        'hot_keys': hot_keys
    }
    return data


@require_GET
@response_wrapper
def get_search_activitys(request):
    """
    搜索商品
    """
    try:
        search_key = request.GET.get('key')
        search_key = search_key.strip()
        if not search_key:
            raise
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except:
        raise ParamError('param invalid')
    tids = search_db.get_tids_by_key(search_key)
    activitys = view_activitys_by_tids(tids, page, size)
    activitys = filter_apples(request, activitys)
    activitys = filter_gp(request, activitys)
    activitys = _filter_star(request, activitys)
    if len(activitys) > 0:
        redis_cache.add_hot_key(search_key)
    data = {
        'list': activitys,
        'page': page if page > 0 else 1,
        'size': len(activitys),
    }
    return data


@require_GET
@response_wrapper
def get_tids_activitys(request):
    """
    通过tids查找
    """
    try:
        tids = request.GET.get('tids')
        tids = [int(tid) for tid in json.loads(tids)]
        if not tids:
            raise ParamError('param invalid')
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
    except:
        raise ParamError('param invalid')
    activitys = view_activitys_by_tids(tids, page, size)
    activitys = filter_apples(request, activitys)
    activitys = filter_gp(request, activitys)
    activitys = _filter_star(request, activitys)
    data = {
        'list': activitys,
        'page': page if page > 0 else 1,
        'size': len(activitys),
    }
    return data
