# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import os
import random
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.model.show import SHOW_STATUS, AnnounceShow

from luckycommon.push import handler as push_handler

from luckycommon.db import show as show_db
from luckycommon.credit.db import credit as credit_db

_LOGGER = logging.getLogger('lucky')


def start():
    item = AnnounceShow.query.filter(AnnounceShow.status == SHOW_STATUS.VERIFY_PRE).first()
    if item:
        pre_award = item.verify_award
        pre_highlight = item.highlight
        show, need_award, need_push_fail = show_db.verify_show(
            item.id, SHOW_STATUS.VERIFY_SUCCESS, '', pre_award, pre_highlight)
        if need_award:
            # add credit award by verify award
            award_credit = show.verify_award
            credit_db.add_credit(show.user_id, award_credit, u'Bonus Testimonial')
            push_handler.push_show_award(show)
        if need_push_fail:
            push_handler.push_verify_fail(show)
        _LOGGER.info('verify show id: %s, user: %s', show.id, show.user_id)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'start':
        rand = random.randint(1, 100)
        if rand <= 50:
            start()
