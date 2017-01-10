# -*- coding: utf-8 -*-
import json
import logging

from luckycommon.social.model.share import *
from luckycommon.social.db import share as share_db

from luckycommon.utils.tz import local_now
from luckycommon.utils import exceptions as err


def submit_share(user_id, share_type):
    if share_type not in SHARE_TYPE.to_dict():
        raise err.ParamError('share type invalid')
    date_str = local_now().strftime('%Y-%m-%d')
    share_item = share_db.submit(user_id, date_str, share_type)
    share_extend = {} if not share_item.extend else json.loads(share_item.extend)
    return share_extend
