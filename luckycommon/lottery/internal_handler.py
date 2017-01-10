# -*- coding: utf-8 -*-
from luckycommon.lottery.db import lottery as lottery_db
from luckycommon.utils.exceptions import DataError


def get_lottery_by_phase(phase):
    return lottery_db.get_lottery_by_phase(phase)


def save_lottery(phase, number, reference):
    lottery = get_lottery_by_phase(phase)
    if not lottery:
        lottery = lottery_db.create_lottery(phase, number, reference)
        return lottery
    elif lottery.number != number:
        raise DataError('lottery number not consistent. origin: %s, new: %s' % (lottery.number, number))


def get_latest_lottery():
    lottery = lottery_db.get_latest_lottery()
    return lottery
