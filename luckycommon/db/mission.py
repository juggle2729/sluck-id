# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.model.mission import AWARD_CREDIT, FreshMission
from luckycommon.account.model.account import Account

from luckycommon.credit.model.credit import RECORD_TYPE, CreditRecord

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import DataError

from django.utils.translation import ugettext as _


_LOGGER = logging.getLogger('lucky')


class FreshMissionDb:

    @classmethod
    @sql_wrapper
    def check_step_a(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id).first()
        if not item:
            item = FreshMission()
            item.user_id = user_id
            item.step_a = 0
        if item.step_a == 0:
            item.step_a = 1
            item.save()
        
    @classmethod
    @sql_wrapper
    def check_step_b(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id).first()
        if not item:
            item = FreshMission()
            item.user_id = user_id
            item.step_b = 0
        if item.step_b == 0:
            item.step_b = 1
            item.save()

    @classmethod
    @sql_wrapper
    def check_step_c(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id).first()
        if not item:
            item = FreshMission()
            item.user_id = user_id
            item.step_c = 0
        if item.step_c == 0:
            item.step_c = 1
            item.save()

    @classmethod
    @sql_wrapper
    def check_step_d(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id).first()
        if not item:
            item = FreshMission()
            item.user_id = user_id
            item.step_d = 0
        if item.step_d == 0:
            item.step_d = 1
            item.save()

    @classmethod
    @sql_wrapper
    def get_step_status(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id).first()
        return item

    @classmethod
    @sql_wrapper
    def activate(cls, user_id):
        item = FreshMission.query.filter(FreshMission.user_id == user_id)\
                                 .with_lockmode('update').first()
        if (not item or item.step_a != 1 or
            item.step_b != 1 or item.step_c != 1 or item.step_d != 1):
            raise DataError('mission not complete')
        if item.status == 1:
            raise DataError('mission has activated')
        item.status = 1
        item.save(auto_commit=False)
        orm.session.commit()
        _LOGGER.info('activate fresh mission succ, %s', user_id)
