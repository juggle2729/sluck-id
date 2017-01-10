# -*- coding: utf-8 -*-
import logging

from django.views.decorators.http import require_GET

from luckycommon.tips.handler import CommandTips
from luckycommon.preset.handler import view_preset, view_banner, view_discovery, view_shortcut
from luckycommon.utils.api import parse_p
from luckycommon.utils.decorator import response_wrapper

from django.conf import settings


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@require_GET
@response_wrapper
def fetch_preset(req):
    """
    获取预置数据
    eg:
    {
        'last_modified': 2,
        'notify':{
            '_disable_activate':  true, # 关闭周期性通知
            'wake':[{             # 触发性
                    'status': 0,  # 用户状态 0-安装未注册 1-注册未购买 2-长时间未启动
                    'period': 24, # 推送周期，hour
                    'weight': 100,
                    'condition': 1, #状态持续时间，单位：小时
                    'title': '',
                    'content': '',
                    'command': ''
                }
            ],
            'activate':[{         # 周期性通知
                    'type': 0,
                    'period': 24, # 推送周期，hour
                    'time': '22:00', # 推送时间点
                    'start_date': '2015-12-08',
                    'end_date': '2015-12-10',
                    'optional': [{
                            'title': '',
                            'content': '',
                            'command': ''
                        }
                    ],
            }],
        },
        'scrolling': {
            'stay': 5,  #展示时间,
            'fetch_interval': 600,    # 取数据间隔时间
        },
        'ipay':{
            'webmode': 0            # 0:审核模式; 1:发布模式
        },
        'pages':[],     # loading ids
        'shortcut':[],  # shortcut ids
        'banner': [],   # banner ids
        'discovery': [] # discovery ids
    }
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    last_modified = int(query_dct.get('last_modified', 0))
    p = parse_p(query_dct.get('p'))
    _TRACKER.info({"type": "active", "user_id": user_id or 1,
                   "aid": p.get('aid'),
                   "chn": p.get('chn'),
                   'pkg': p.get('pkg', 'com.dollar.lucky.eus'),
                   'code': p.get('code'),
                   'market': p.get('market')
                   })
    _LOGGER.debug('p is %s' % p)
    data = view_preset(p.get('cvc'), p.get('chn'), last_modified, user_id)
    if p.get('market') == 'gp' and str(p.get('cvc')) == str(settings.GP_VERSION_CODE) and settings.GP_FLAG:
        _LOGGER.debug('gp censor enable')
        data.update({'gp_flag': not settings.GP_FLAG})
        data.update({'coin_flag': not settings.GP_FLAG})
    else:
        _LOGGER.debug('gp censor disable')
        data.update({'gp_flag': True})
        data.update({'coin_flag': True})

    return data


@require_GET
@response_wrapper
def fetch_shortcut(req):
    """
    获取shortcut数据
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    shortcut_list = view_shortcut(
        p.get('cvc'), p.get('chn'), user_id)
    data = {
        'list': shortcut_list
    }
    return data


@require_GET
@response_wrapper
def fetch_banner(req):
    """
    获取banner数据
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    banner_list = view_banner(
        p.get('cvc'), p.get('chn'), user_id)
    data = {
        'list': banner_list
    }
    return data


URL_CAMPAIGN_MAP = {
    '/discovery/new_year_share_coupon': 'new_daily_buy_level',
    '/discovery/new_year_coupon': 'new_recharge_level'
}


@require_GET
@response_wrapper
def fetch_discovery(req):
    """
    获取discovery数据
    """
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    discovery_list = view_discovery(p.get('cvc'), p.get('chn'),
                                    user_id)
    for discovery in discovery_list:
        cmd = discovery['cmd']
        auto_ack = True if p.get('chn') == 'ios' else False
        notify_count = CommandTips().query_by_cmd(
            req.user_id, cmd, auto_ack=auto_ack)
        discovery['notify'] = 1 if notify_count > 0 else 0

    data = {
        'list': discovery_list
    }
    return data
