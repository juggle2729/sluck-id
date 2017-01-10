# -*- coding: utf-8 -*-
import json
import logging

from django.views.decorators.http import require_GET, require_POST

from luckycommon.notification.model.notification import NOTIFY_TYPE
from luckycommon.tips import handler as tips_handler
from luckycommon.push import handler as push_handler

from luckycommon.cache import redis_cache
from luckycommon.notification.db import notification as db
from luckycommon.db.campaign import RechargeCampaignDb
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.api import token_required, parse_p
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.tz import utc_to_local, now_ts
from luckycommon.utils.exceptions import ParamError

from future.utils import raise_with_traceback
from django.conf import settings

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
def get_notifications(req):
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    user_sync_id = int(query_dct.get('user_sync_id', 0))
    sys_sync_id = int(query_dct.get('sys_sync_id', 0))
    resp_items = []
    max_user_sync_id = 0
    max_sys_sync_id = 0
    user_id = req.user_id
    if user_id:
        user_items = db.get_user_notifications(user_id, user_sync_id)
        for item in user_items:
            if item.sync_id > max_user_sync_id:
                max_user_sync_id = item.sync_id
            extend = item.extend
            ext_obj = {} if not extend else json.loads(extend)
            resp_items.append({
                'id': item.sync_id,
                'notify_type': item.notify_type,
                'content': json.loads(item.content) if item.content else '',
                'extend': ext_obj,
                'created_at': utc_to_local(item.created_at).strftime('%Y-%m-%d %H:%M:%S')
            })

    sys_items = db.get_sys_notifications(sys_sync_id)
    for item in sys_items:
        if item.sync_id > max_sys_sync_id:
            max_sys_sync_id = item.sync_id
        extend = item.extend
        if extend:
            if not p:
                continue
            ext_obj = json.loads(extend)
            filter_list = ext_obj.get('filter_list', [])
            is_valid = False if filter_list else True
            for filter_conf in filter_list:
                filter_cvc = filter_conf.get('cvc')
                client_cvc = p.get('cvc', 0)
                if filter_cvc:
                    max_cvc = filter_cvc.get('max')
                    if max_cvc and client_cvc > max_cvc:
                        continue
                    min_cvc = filter_cvc.get('min')
                    if min_cvc and client_cvc < min_cvc:
                        continue
                filter_chn = filter_conf.get('chn')
                client_chn = p.get('chn')
                if filter_chn and client_chn:
                    include = filter_chn.get('include')
                    if include and client_chn not in include:
                        continue
                    exclude = filter_chn.get('exclude')
                    if exclude and client_chn in exclude:
                        continue
                is_valid = True
            if not is_valid:
                continue
            if 'filter_list' in ext_obj:
                ext_obj.pop('filter_list')
        else:
            ext_obj = {}

        resp_items.append({
            'id': item.sync_id,
            'notify_type': NOTIFY_TYPE.SYSTEM,
            'content': json.loads(item.content) if item.content else '',
            'extend': ext_obj,
            'created_at': utc_to_local(item.created_at).strftime('%Y-%m-%d %H:%M:%S')
        })
    return {
        'max_user_sid': max_user_sync_id,
        'max_sys_sid': max_sys_sync_id,
        'list': resp_items,
    }


@require_GET
@response_wrapper
def get_sys_notifications(req):
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    sync_id = int(query_dct.get('sync_id', 0))

    items = db.get_sys_notifications(sync_id)
    resp_items = []
    for item in items:
        extend = item.extend
        if extend:
            if not p:
                continue
            ext_obj = json.loads(extend)
            filter_list = ext_obj.get('filter_list', [])
            is_valid = False if filter_list else True
            for filter_conf in filter_list:
                filter_cvc = filter_conf.get('cvc')
                client_cvc = p.get('cvc', 0)
                if filter_cvc:
                    max_cvc = filter_cvc.get('max')
                    if max_cvc and client_cvc > max_cvc:
                        continue
                    min_cvc = filter_cvc.get('min')
                    if min_cvc and client_cvc < min_cvc:
                        continue
                filter_chn = filter_conf.get('chn')
                client_chn = p.get('chn')
                if filter_chn and client_chn:
                    include = filter_chn.get('include')
                    if include and client_chn not in include:
                        continue
                    exclude = filter_chn.get('exclude')
                    if exclude and client_chn in exclude:
                        continue
                is_valid = True
            if not is_valid:
                continue     
             
        resp_items.append({
            'id': item.sync_id,
            'content': json.loads(item.content) if item.content else '',
            'created_at': utc_to_local(item.created_at).strftime('%Y-%m-%d %H:%M:%S')
        })

    return {
        'list': resp_items
    }


@require_POST
@response_wrapper
@token_required
def remove(request):
    try:
        clear = request.POST.get('clear', 0)
        notify_type = int(request.POST.get('type', 0))
        remove_list = request.POST.get('list', '[]')
        remove_list = json.loads(remove_list)
    except Exception as e:
        raise_with_traceback(ParamError(e))

    user_id = request.user_id

    db.remove_notifications(user_id, remove_list, clear, notify_type)
    _LOGGER.info('%s remove his %s notifications', user_id, len(remove_list))

    return {}


@require_GET
@response_wrapper
@token_required
def get_tips(req):
    """
    获取待处理消息
    包括中奖、晒单
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    pending_dict = tips_handler.query_all(user_id, p.get('cvc'), p.get('chn'))
    return pending_dict


@require_GET
@response_wrapper
@token_required
def get_tips_v2(req):
    """
    获取待处理消息
    包括中奖、晒单,
    增加cmd和tips的映射
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    pending_dict = tips_handler.query_all(user_id, p.get('cvc'), p.get('chn'))
    cmd_map = tips_handler.CMD_TIPS_MAP
    data = {
        'tips': pending_dict,
        'map': cmd_map
    }
    return data


@require_GET
@response_wrapper
@token_required
def mark_tips_read(req):
    user_id = req.user_id
    cmd = req.GET.get('cmd')
    if cmd:
        redis_cache.notify_discovery_item(user_id, cmd)

    return {}


@require_POST
@response_wrapper
@token_required
def push_shipping(req):
    admin_id = req.user_id
    if admin_id != settings.ADMIN_ID:
        raise err.AuthenticateError('no access')
    query_dct = req.POST.dict()
    user_id = int(query_dct.get('user_id'))
    activity_id = query_dct.get('activity_id')
    order_id = long(query_dct.get('order_id'))
    shipping_info = query_dct.get('shipping_info', '{}')
    shipping_info = json.loads(shipping_info)
    push_handler.push_shipping(order_id, shipping_info)
    return {}
