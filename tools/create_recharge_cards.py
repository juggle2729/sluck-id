# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.recharge_card import create_recharge_card
from luckycommon.model.recharge_card import ALLOWED_RECHARGE_CARD_AMOUNT

if __name__ == '__main__':
    amount = int(sys.argv[1])
    if amount not in ALLOWED_RECHARGE_CARD_AMOUNT:
        print 'amount not allowed, use one in %s' % ALLOWED_RECHARGE_CARD_AMOUNT

    if len(sys.argv) == 2:
        count = 1
    count = int(sys.argv[2])
    for x in range(count):
        card_id, _card_secret = create_recharge_card(amount)
        print "%s, %s, %s" % (amount, card_id, _card_secret)
