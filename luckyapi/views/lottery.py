# -*- coding: utf-8 -*-
import logging

from luckycommon.level.handler import get_user_level

from luckycommon.utils.limit import check_abtest
from luckycommon.utils.api import parse_p, token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ResourceNotFound

from django.conf import settings
from django.views.decorators.http import require_GET


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


@require_GET
@response_wrapper
@token_required
def fresh(req):
    """
    获取时时彩状态
    response: {
        'status': 1,       # 当前状态， 1:进行中 2:结算中
        'remain_ts': 100,  # 剩余倒计时
        'my': {
            'balance': 10000, # 当前夺宝币余额
            'credit': 10000   # 当前元宝余额
        },
        'res_index': 2, # 当前的转盘结果
    }
    """
    user = req.user
    user_id = req.user_id
    query_dct = req.GET.dict()
    p = parse_p(query_dct.get('p'))
    if p:
        # for client filter
        checked = check_abtest(user_id, p.get('chn'), {'abtest': 1})
        if not checked:
            raise ResourceNotFound()
    data = {
        'status': 1,
        'remain_ts': 50,
        'cmd': '11#%s/discovery/countdown_turntable' % settings.WEB_APP_ROOT_URL,
    }
    if not p:
        # for web, need sign
        data.update({
            'my': {
                'balance': user.balance,
                'credit': user.credit,
            }
        })
    return data
