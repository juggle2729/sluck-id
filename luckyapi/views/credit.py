# -*- coding: utf-8 -*-
import json
import logging
import datetime

from luckycommon.credit.db import credit as credit_db
from luckycommon.credit.model.check import CHECK_TYPE
from luckycommon.credit import handler as credit_handler

from luckycommon.mission import fresh_mission
from luckycommon.cache import redis_cache

from luckycommon.utils.api import token_required, parse_p
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.decorator import response_wrapper

from future.utils import raise_with_traceback

from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST


_LOGGER = logging.getLogger('lucky')

ICON_DAILY_SIGN = 'http://p.1yuan-gou.com/icon_my_integral1%402x.png'
ICON_DAILY_SHARE = 'http://p.1yuan-gou.com/icon_my_integral2%402x.png'
ICON_BUY = 'http://p.1yuan-gou.com/icon_my_integral3%402x.png'
ICON_PARTNER = 'http://7xov77.com1.z0.glb.clouddn.com/ic_recruiting.png'
ICON_FRESH = 'http://p.1yuan-gou.com/icon_my_integral5%402x.png'


@require_GET
@response_wrapper
@token_required
def get_my_credit(request):
    """
    查看我的积分
    """
    tracks = parse_p(request.GET.get('p'))
    client_chn = tracks.get('chn', None)
    client_version_code = int(tracks.get('cvc', 0))
    old_version = False
    if client_chn in settings.IOS_DEBUG_CONF:
        if client_chn == 'ios' and client_version_code <= 14:
            old_version = True
    elif client_chn and client_version_code <= 15:
        old_version = True

    credit = request.user.credit or 0
    data = {
        'total': credit,
        'category': []
    }
    today_checks = credit_db.get_today_checks(request.user_id)
    today_sign = 0
    today_share = 0
    for check_item in today_checks:
        if check_item.check_type == CHECK_TYPE.DAILY_SIGN:
            today_sign += check_item.check_times
        if check_item.check_type == CHECK_TYPE.DAILY_SHARE:
            today_share += check_item.check_times
    credit_activity = []
    credit_activity.append({
        'icon': ICON_DAILY_SIGN,
        'title': u"Poin Absensi",
        'content': u"Bagikan kebahagiaan, dapatkan poin, menang lebih banyak. Poin absensi bertambah setiap hari (max. 100)",
        'tips': u"Ikut",
        'command': '16#' if old_version else '11#%s/user/my_daily_attendance' % settings.WEB_APP_ROOT_URL,
        'enable': 0 if today_sign > 0 else 1
    })
    credit_activity.append({
        'icon': ICON_BUY,
        'title': u"Pakai Poin",
        'content': u"Pakai 1 Koin, dapatkan 10 Poin",
        'tips': u"Ikut",
        'command': '0#',
        'enable': 1
    })
    # credit_activity.append({
    #     'icon': ICON_PARTNER,
    #     'title': u"mời bạn cùng chơi",
    #     'content': u"Bạn và bạn của bạn đều có giải thưởng",
    #     'tips': u"Kiềm tiền",
    #     'command': '11#%s/user/my_rebate' % settings.WEB_APP_ROOT_URL,
    #     'enable': 1
    # })
    data['category'].append({
        'title': u"Aktivitas Poin",
        'credit_activity': credit_activity
    })
    # if not old_version:
    #     fresh_mission_done = fresh_mission.get_step_status(request.user_id)
    #     data['category'].append({
    #         'title': u"Tín dụng tăng",
    #         'credit_activity': [{
    #             'icon': ICON_FRESH,
    #             'title': u"Nhiệm vụ người mới chơi",
    #             'content': u"Nhanh tay, chuyển 1 tệ",
    #             'tips': u"nhận lì xì",
    #             'command': '11#%s/user/newbie_task' % settings.WEB_APP_ROOT_URL,
    #             'enable': 0 if fresh_mission_done.get('activated') else 1
    #         }]
    #     })
    return data


@require_GET
@response_wrapper
@token_required
def get_credit_records(request):
    """
    查看我的积分记录
    """
    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        record_type = int(
            request.GET['type']) if request.GET.get('type') else None
    except Exception as e:
        raise_with_traceback(ParamError(e))

    r_list, count = credit_handler.get_user_credit_records(
            request.user_id, page, size, record_type)
    data = {
        'list': r_list,
        'total_count': count
    }
    return data


@require_POST
@response_wrapper
@token_required
def credit_exchange(request):
    """
    兑换积分
    """
    exchanged_credit, added_price = credit_db.exchange_credit(request.user_id)
    return {
        'exchanged_credit': exchanged_credit,
        'added_price': added_price
    }


@require_GET
@response_wrapper
def get_credit_pool(request):
    """
    获取元宝池状态
    """
    pool_amount = redis_cache.get_credit_pool() or 0
    count = credit_db.get_sign_user_count()
    return {
        'pool_amount': int(pool_amount),
        'user_count': count
    }


@require_GET
@response_wrapper
def get_latest_distribution(request):
    """
    获取最新一期的元宝瓜分记录
    """
    date, term, d_list = credit_handler.get_latest_distribution()
    return {
        'date': date,
        'term': term,
        'single_amount': 0 if not d_list else d_list[0]['amount'],
        'list': d_list
    }
