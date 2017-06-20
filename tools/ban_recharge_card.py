# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

# add up one level dir into sys path

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.recharge_card import get_card_by_id
from luckycommon.model.recharge_card import RechargeCardStatus

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'input card_id list with comma separated'
    card_id_list = sys.argv[1].split(',')
    activate = False
    if len(sys.argv) == 3:
        option = sys.argv[2]
        if 'activate' == option:
            activate = True
    for card_id in card_id_list:
        card = get_card_by_id(card_id)
        if not card:
            print 'card_id: %s not found' % card_id
            continue
        if card.pay_id or card.user_id:
            print 'card already used, can not ban or activate again. card_id: %s' % card_id
            continue
        if activate:
            if card.status == RechargeCardStatus.INVALID.value:
                card.status = RechargeCardStatus.VALID.value
                card.save()
                print 'activate card. card_id: %s' % card_id
            else:
                print 'card already valid. card_id: %s' % card_id
        if not activate:
            if card.status == RechargeCardStatus.VALID.value:
                card.status = RechargeCardStatus.INVALID.value
                card.save()
                print 'ban card. card_id: %s' % card_id
            else:
                print 'card already invalid. card_id: %s' % card_id

