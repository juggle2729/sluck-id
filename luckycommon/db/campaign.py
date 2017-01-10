# -*- coding: utf-8 -*-
import logging

from luckycommon.model import orm
from luckycommon.account.model.account import Account
from luckycommon.model.transaction import *
from luckycommon.model.coupon import *
from luckycommon.model.campaign import *

from luckycommon.utils import id_generator
from luckycommon.utils.tz import now_ts
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils.exceptions import DataError, BalanceInsufficient

from django.utils.translation import ugettext as _


_LOGGER = logging.getLogger('lucky')
_TRACKER = logging.getLogger('tracker')


class RechargeCampaignDb:
    """
    DAO for recharge campaign
    """

    @classmethod
    @sql_wrapper
    def get_level(cls, user_id, campaign_id, level_id):
        item = RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                     .filter(RechargeCampaign.campaign_id == campaign_id)\
                                     .filter(RechargeCampaign.level == level_id).first()
        return item

    @classmethod
    @sql_wrapper
    def get_current_level(cls, user_id, campaign_id):
        query = RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                      .filter(RechargeCampaign.campaign_id == campaign_id)
        query = query.order_by(RechargeCampaign.level.desc()).limit(1)
        item = query.first()
        if not item:
            # init
            item = RechargeCampaign()
            item.campaign_id = campaign_id
            item.user_id = user_id
            item.level = 0
            item.current_price = 0
            item.status = LEVEL_STATUS.UNOPEN
            item.save()
        return item

    @classmethod
    @sql_wrapper
    def get_all_levels(cls, user_id, campaign_id):
        query = RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                      .filter(RechargeCampaign.campaign_id == campaign_id)
        query = query.order_by(RechargeCampaign.level)
        return query.all()

    @classmethod
    @sql_wrapper
    def get_available_levels(cls, user_id, campaign_id):
        return RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                     .filter(RechargeCampaign.campaign_id == campaign_id)\
                                     .filter(RechargeCampaign.status == LEVEL_STATUS.UNOPEN)\
                                     .filter(RechargeCampaign.level > 0).all()

    @classmethod
    @sql_wrapper
    def add_new_level(cls, user_id, campaign_id, level, price):
        item = RechargeCampaign()
        item.campaign_id = campaign_id
        item.user_id = user_id
        item.level = level
        item.current_price = price
        item.status = LEVEL_STATUS.UNOPEN
        item.save()

    @classmethod
    @sql_wrapper
    def update_current_level(cls, user_id, campaign_id, level, price):
        item = RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                     .filter(RechargeCampaign.campaign_id == campaign_id)\
                                     .filter(RechargeCampaign.level == level).one()
        item.current_price = price
        item.save()
                      
    @classmethod
    @sql_wrapper
    def award_level(cls, user_id, campaign_id, level_id, tid_list):
        # do transaction
        item = RechargeCampaign.query.filter(RechargeCampaign.user_id == user_id)\
                                     .filter(RechargeCampaign.campaign_id == campaign_id)\
                                     .filter(RechargeCampaign.level == level_id)\
                                     .filter(RechargeCampaign.status == LEVEL_STATUS.UNOPEN)\
                                     .with_lockmode('update').one()
        # create coupon
        coupon_list = []
        id_list = []
        for tid in tid_list:
            template = CouponTemplate.query.filter(CouponTemplate.id == tid).one()
            coupon = AccountCoupon.create_from_template(template, user_id)
            coupon.save(auto_commit=False)
            orm.session.flush()
            coupon_list.append(coupon)
            id_list.append(coupon.id)
            AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
            _TRACKER.info({'user_id': coupon.user_id,
                           'coupon_id': coupon.id,
                           'type': 'create_coupon',
                           'from': 'recharge_campaign',
                           'price': coupon.price})
        # change level status
        item.status = LEVEL_STATUS.OPENED
        id_list = [str(i) for i in id_list]
        item.coupons = ','.join(id_list)
        item.save(auto_commit=False)
        orm.session.commit()
        return coupon_list


class DailyBuyCampaignDb:
    """
    DAO for daily buy campaign
    """
    INTERNAL_COUNT = 10
    EXPIRE_TS = 7 * 24 * 3600
    MAX_LEVEL = 1

    @classmethod
    @sql_wrapper
    def adjust_level(cls, user_id, campaign_id, date_str, add_amount, amount_unit=10):
        # lock user level record
        query = DailyCampaign.query.filter(DailyCampaign.user_id == user_id)\
                                   .filter(DailyCampaign.campaign_id == campaign_id)\
                                   .filter(DailyCampaign.date == date_str)
        items = query.order_by(DailyCampaign.level.desc()).with_lockmode('update').all()
        if not items:
            # init
            item = DailyCampaign()
            item.campaign_id = campaign_id
            item.user_id = user_id
            item.date = date_str 
            item.level = 0
            item.current_amount = 0
            item.status = LEVEL_STATUS.UNOPEN
            item.save(auto_commit=False)
        else:
            item = items[0]
        current_level = item.level
        current_amount = item.current_amount + add_amount
        added_amount = current_amount - amount_unit * current_level
        item.current_amount = current_amount
        # check next level
        added_level = 0
        while added_amount >= amount_unit:
            # add level
            if current_level+1 > DailyBuyCampaignDb.MAX_LEVEL:
                break
            current_level += 1
            added_level += 1
            new_item = DailyCampaign()
            new_item.campaign_id = campaign_id
            new_item.user_id = user_id
            new_item.date = date_str 
            new_item.level = current_level
            new_item.current_amount = current_amount
            new_item.status = LEVEL_STATUS.UNOPEN
            new_item.save(auto_commit=False)
            _LOGGER.info('%s reached new level %s in %s', user_id, current_level, campaign_id)
            added_amount -= amount_unit
        orm.session.commit()

    @classmethod
    @sql_wrapper
    def get_all_levels(cls, user_id, campaign_id, date_str):
        query = DailyCampaign.query.filter(DailyCampaign.user_id == user_id)\
                                   .filter(DailyCampaign.campaign_id == campaign_id)\
                                   .filter(DailyCampaign.date == date_str)
        query = query.order_by(DailyCampaign.level)
        return query.all()

    @classmethod
    @sql_wrapper
    def get_available_levels(cls, user_id, campaign_id, date_str):
        return DailyCampaign.query.filter(DailyCampaign.user_id == user_id)\
                                  .filter(DailyCampaign.campaign_id == campaign_id)\
                                  .filter(DailyCampaign.date == date_str)\
                                  .filter(DailyCampaign.status == LEVEL_STATUS.UNOPEN)\
                                  .filter(DailyCampaign.level > 0).all()

    @classmethod
    @sql_wrapper
    def get_level(cls, user_id, campaign_id, date_str, level_id):
        item = DailyCampaign.query.filter(DailyCampaign.user_id == user_id)\
                                  .filter(DailyCampaign.campaign_id == campaign_id)\
                                  .filter(DailyCampaign.date == date_str)\
                                  .filter(DailyCampaign.level == level_id).first()
        return item

    @classmethod
    @sql_wrapper
    def award_level(cls, user_id, campaign_id, date_str, level_id):
        # do transaction
        item = DailyCampaign.query.filter(DailyCampaign.user_id == user_id)\
                                     .filter(DailyCampaign.campaign_id == campaign_id)\
                                     .filter(DailyCampaign.date == date_str)\
                                     .filter(DailyCampaign.level == level_id)\
                                     .filter(DailyCampaign.status == LEVEL_STATUS.UNOPEN)\
                                     .with_lockmode('update').one()
        # create coupon
        coupon = GroupCoupon()
        coupon.user_id = user_id
        coupon.title = ''
        coupon.total_count = DailyBuyCampaignDb.INTERNAL_COUNT
        coupon.left_count = DailyBuyCampaignDb.INTERNAL_COUNT
        coupon.expire_ts = now_ts() + DailyBuyCampaignDb.EXPIRE_TS
        coupon.campaign_id = campaign_id
        coupon.save(auto_commit=False)
        orm.session.flush()
        # change level status
        item.status = LEVEL_STATUS.OPENED
        item.coupon_id = coupon.id 
        item.save(auto_commit=False)
        orm.session.commit()
        return coupon


class MoistCampaignDb:
    """
    DAO for moist campaign
    """

    @classmethod
    @sql_wrapper
    def check_in(cls, user_id, campaign_id, recharge_price, award_price):
        item = MoistCampaign.query.filter(MoistCampaign.user_id == user_id)\
                                  .filter(MoistCampaign.campaign_id == campaign_id)\
                                  .with_lockmode('update').first()
        if not item:
            item = MoistCampaign()
            item.campaign_id = campaign_id
            item.user_id = user_id
            item.recharge_price = recharge_price
            item.award_price = award_price
            item.save()
            _LOGGER.info('%s check in moist campaign %s succ.', user_id, campaign_id)
            return True
        _LOGGER.info('%s check in moist campaign %s fail.', user_id, campaign_id)
        return False

    @classmethod
    @sql_wrapper
    def get_status(cls, user_id, campaign_id):
        item = MoistCampaign.query.filter(MoistCampaign.user_id == user_id)\
                                  .filter(MoistCampaign.campaign_id == campaign_id)\
                                  .first()
        return item


class GodCampaignDb:
    """
    DAO for wealth god campaign
    """

    @classmethod
    @sql_wrapper
    def get_status(cls, user_id, date_str):
        item = GodCampaign.query.filter(GodCampaign.user_id == user_id)\
                                .filter(GodCampaign.date == date_str).first()
        return item

    @classmethod
    @sql_wrapper
    def activate(cls, user_id, date_str, level_column, tid_list):
        item = GodCampaign.query.filter(GodCampaign.user_id == user_id)\
                                .filter(GodCampaign.date == date_str)\
                                .with_lockmode('update').one()
        level_status = getattr(item, level_column)
        if level_status != 1:
            raise DataError('level not reached')
        setattr(item, level_column, 2)
        # create coupon
        coupon_list = []
        id_list = []
        for tid in tid_list:
            template = CouponTemplate.query.filter(CouponTemplate.id == tid).one()
            coupon = AccountCoupon.create_from_template(template, user_id)
            coupon.save(auto_commit=False)
            orm.session.flush()
            coupon_list.append(coupon)
            id_list.append(coupon.id)
            AccountCoupon.start_expire_timer(coupon.id, coupon.expire_ts)
        id_list = [str(i) for i in id_list]
        coupons = [] if not item.coupons else item.coupons.split(',')
        coupons.extend(id_list)
        item.coupons = ','.join(coupons)
        item.save(auto_commit=False)
        orm.session.commit()
        return coupon_list

    @classmethod
    @sql_wrapper
    def fresh(cls, user_id, date_str, first_tid, second_tid, third_tid):
        item = GodCampaign.query.filter(GodCampaign.user_id == user_id)\
                                .filter(GodCampaign.date == date_str)\
                                .with_lockmode('update').first()
        if not item:
            item = GodCampaign()
            item.user_id = user_id
            item.date = date_str
            item.first_tid = first_tid
            item.second_tid = second_tid
            item.third_tid = third_tid
            item.save()
        elif item.triple_kill:
            raise DataError('has been triple kill!')
        elif item.fresh_times >= 4:
            raise DataError('reached limit', status=StatusCode.REACH_LIMIT)
        else:
            fresh_times = item.fresh_times
            consume_price = 0
            winned_tids = [] if not item.winned_tids else item.winned_tids.split(',')
            if fresh_times == 1:
                item.fresh_times = 2
            elif fresh_times == 2:
                item.fresh_times = 3
                consume_price = 1
            elif fresh_times == 3:
                item.fresh_times = 4
                consume_price = 10
            if str(item.first_tid) not in winned_tids:
                item.first_tid = first_tid 
            if str(item.second_tid) not in winned_tids:
                item.second_tid = second_tid 
            if str(item.third_tid) not in winned_tids:
                item.third_tid = third_tid 
            # consume account balance
            if consume_price > 0:
                account = Account.query.filter(Account.id == user_id).with_lockmode('update').one()
                if account.balance < consume_price:
                    raise BalanceInsufficient('account balance insufficient')
                account.balance -= consume_price
                account.save(auto_commit=False)
                transaction = Transaction()
                transaction.id = id_generator.generate_long_id('transaction')
                transaction.user_id = user_id
                transaction.type = TRANSACTION_TYPE.BALANCE_BUY
                transaction.title = _('wealth god campaign')
                transaction.price = -consume_price
                transaction.balance = account.balance
                transaction.status = TRANSACTION_STATUS.DONE
                transaction.save(auto_commit=False)
            item.save()
        return item

    @classmethod
    @sql_wrapper
    def register(cls, user_id, date_str, tid):
        item = GodCampaign.query.filter(GodCampaign.user_id == user_id)\
                                .filter(GodCampaign.date == date_str)\
                                .with_lockmode('update').first()
        if not item:
            return
        winned_tids = [] if not item.winned_tids else item.winned_tids.split(',')
        if str(tid) in winned_tids:
            return
        first_tid, second_tid, third_tid = item.first_tid, item.second_tid, item.third_tid
        if str(tid) not in (first_tid, second_tid, third_tid):
            return
        winned_tids.append(str(tid))
        item.winned_tids = ','.join(winned_tids)
        if len(winned_tids) == 1:
            item.first_blood = 1
        elif len(winned_tids) == 2:
            item.double_kill = 1
        elif len(winned_tids) >= 3:
            item.triple_kill = 1
        item.save()
        _LOGGER.info('%s register %s in god campaign', user_id, tid)
