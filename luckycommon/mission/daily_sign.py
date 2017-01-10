# -*- coding: utf-8 -*-
import logging

from luckycommon.credit.model.check import CHECK_TYPE
from luckycommon.credit.db import credit as credit_db


_LOGGER = logging.getLogger('lucky')


def check_complete(user_id):
    today_checks = credit_db.get_today_checks(user_id)
    for check_item in today_checks:
        if check_item.check_type == CHECK_TYPE.DAILY_SIGN:
            return True
    return False
