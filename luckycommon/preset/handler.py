# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.preset.model import CMD_MODULES
from luckycommon.preset.model.preset import DEVICE_TYPE
from luckycommon.preset.db.preset import get_preset
from luckycommon.preset.db.discovery import get_discovery
from luckycommon.preset.db.banner import get_banner
from luckycommon.preset.db.shortcut import get_shortcut
from luckycommon.preset.db.loading import get_loading
from luckycommon.utils.limit import check_abtest
from luckycommon.utils.exceptions import ResourceNotModified, ResourceNotFound
from luckycommon.utils.tz import now_ts

_LOGGER = logging.getLogger(__name__)


def _chn2type(chn):
    if chn == 'gp_ios':
        return DEVICE_TYPE.QG_IOS
    elif chn == 'int_ios_us':
        return DEVICE_TYPE.INT_IOS_US
    elif chn == 'int_ios_tw':
        return DEVICE_TYPE.INT_IOS_TW
    elif chn == 'int_ios_uk':
        return DEVICE_TYPE.INT_IOS_UK
    elif chn is not None:
        return DEVICE_TYPE.ANDROID
    else:
        return DEVICE_TYPE.WAP


def _get_preset(app_version, device_type):
    preset = get_preset(app_version=app_version, device_type=device_type)
    if not preset:
        raise ResourceNotFound()
    data = {} if not preset.content else json.loads(preset.content)
    data['last_modified'] = preset.last_modified
    return data


def view_preset(app_version, chn, last_modified, user_id):
    device_type = _chn2type(chn)
    data = _get_preset(app_version, device_type)
    for k in ('discovery', 'banner'):
        data.pop(k, None)
    # check abtest for loading pages
    for k, func in {
        'pages': get_loading,
        'shortcut': get_shortcut
    }.iteritems():
        item_ids = data.pop(k, None)
        if item_ids:
            data[k] = []
            for item_id in item_ids:
                item = func(item_id)
                if not item:
                    _LOGGER.error('%s id %s not exist', k, item_id)
                    continue
                item = item.as_dict()
                if not check_abtest(user_id, chn, item):
                    continue
                for t in 'abtest', 'remark', 'created_at', 'updated_at':
                    item.pop(t, None)
                data[k].append(item)

    return data


def _check_complete(user_id, cmd):
    """
    检查活动是否完成
    """
    if not user_id:
        return False
    relation_module = CMD_MODULES.get(cmd)
    if relation_module:
        check_complete = getattr(relation_module, 'check_complete')
        if check_complete:
            return check_complete(user_id) 
    return False


def view_discovery(app_version, chn, user_id):
    device_type = _chn2type(chn)
    data = _get_preset(app_version, device_type)
    data.pop('last_modified')
    item_ids = data.get('discovery', [])
    resp = []
    ts = now_ts()
    for item_id in item_ids:
        item = get_discovery(item_id)
        if not item:
            _LOGGER.error('discovery id %s not exist', item_id)
        else:
            if ts < item.start_ts or ts > item.end_ts:
                continue
            item = item.as_dict()
            if not check_abtest(user_id, chn, item):
                continue
            cmd = item.get('cmd')
            if _check_complete(user_id, cmd):
                continue
            resp.append({
                'icon': item.get('icon'),
                'title': item.get('title'),
                'desc': item.get('desc'),
                'cmd': cmd,
                'tag': item.get('tag') or '',
            })
    return resp[:6]


def view_banner(app_version, chn, user_id):
    device_type = _chn2type(chn)
    data = _get_preset(app_version, device_type)
    data.pop('last_modified')
    item_ids = data.get('banner', [])
    resp = []
    ts = now_ts()
    for item_id in item_ids:
        item = get_banner(item_id)
        if not item:
            _LOGGER.error('banner id %s not exist', item_id)
        else:
            if ts < item.start_ts or ts > item.end_ts:
                continue
            item = item.as_dict()
            if not check_abtest(user_id, chn, item):
                continue
            cmd = item['cmd']
            if _check_complete(user_id, cmd):
                continue
            resp.append({
                'image': item['image'],
                'cmd': cmd,
            })
    return resp[:6]


def view_shortcut(app_version, chn, user_id):
    device_type = _chn2type(chn)
    data = _get_preset(app_version, device_type)
    data.pop('last_modified')
    item_ids = data.get('shortcut', [])
    resp = []
    remove_list = []
    ts = now_ts()
    for item_id in item_ids:
        item = get_shortcut(item_id)
        if not item:
            _LOGGER.error('shortcut id %s not exist', item_id)
        else:
            item = item.as_dict()
            if not check_abtest(user_id, chn, item):
                continue
            cmd = item['command']
            if _check_complete(user_id, cmd):
                remove_list.append({
                    'id': item['id'],
                    'title': item['title'],
                    'command': cmd,
                    'icon': item['icon'],
                })
                continue
            resp.append({
                'id': item['id'],
                'title': item['title'],
                'command': cmd,
                'icon': item['icon'],
            })
    r_list = resp[:4]
    if len(r_list) < 4:
        resp.extend(remove_list)
    return resp[:4]
