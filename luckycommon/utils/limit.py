
# -*- coding: utf-8 -*-
import json
import logging

from future.utils import raise_with_traceback
from luckycommon.db import abtest as abtest_db
from luckycommon.cache import account as account_cache
from luckycommon.utils.api import get_client_ip
from luckycommon.utils.exceptions import Error, PermissionError

_LOGGER = logging.getLogger('lucky')
INTERNAL_IPS = ['113.57.172.122', '120.26.57.89', '47.88.214.13',
                '120.27.162.212', '121.41.6.238', '54.169.136.207']


def frequency_limit(func):
    """
    API频率限制
    """
    def _wrapper(req, *args, **kwargs):
        ip = get_client_ip(req)
        if ip not in INTERNAL_IPS:
            checked = account_cache.check_ip_pay_limit(ip, req.user_id)

            if not checked:
                _LOGGER.error(
                    'frequency limit, ip:%s, user_id:%s', ip, req.user_id)
                raise PermissionError()
        return func(req, *args, **kwargs)

    return _wrapper


def check_abtest(user_id, chn, item):
    if 'abtest' not in item:
        return True
    try:
        abtest_id = item['abtest']
        abtest_item = abtest_db.get_abtest(abtest_id)
        if not abtest_item:
            return True
        abtest_dict = json.loads(abtest_item.content)
        if 'user_id' in abtest_dict:
            if not user_id:
                return False    # 是否对匿名用户开放
            user_id_range = abtest_dict['user_id']
            uid_suffix = str(user_id)[-2:]
            if uid_suffix < user_id_range[0] or uid_suffix > user_id_range[1]:
                return False
    except:
        return True
    return True
