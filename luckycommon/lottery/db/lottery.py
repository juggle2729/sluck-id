# -*- coding: utf-8 -*-
import logging

from luckycommon.lottery.model.lottery import Lottery
from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_lottery_by_phase(phase):
    return Lottery.query.filter(Lottery.phase == phase).first()


@sql_wrapper
def create_lottery(phase, number, reference):
    lottery = Lottery()
    lottery.phase = phase
    lottery.number = number
    lottery.reference = reference
    lottery.save()
    return lottery

@sql_wrapper
def get_latest_lottery():
    return Lottery.query.order_by(Lottery.phase.desc()).first()
