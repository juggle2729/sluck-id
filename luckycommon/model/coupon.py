# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime, timedelta

from luckycommon.model import orm
from luckycommon.utils.tz import now_ts, utc_to_local, local_to_utc
from luckycommon.utils.types import Enum
from luckycommon.timer import TIMER_EVENT_TYPE, TimerEvent


COUPON_TYPE = Enum({
    "DIRECT_OFF": (1L, "direct off"),           # 直减
    "CONDITION_OFF": (2L, "off once reached condition")  # 满减
})


COUPON_STATUS = Enum({
    "UNUSED": (1L, "unused"),    # 未使用
    "USED": (2L, "used"),        # 已使用
    "EXPIRED": (4L, "expired"),  # 已过期
})


class CouponTemplate(orm.Model):
    """
    红包模板
    """
    __tablename__ = "coupon_template"
    id = orm.Column(orm.BigInteger, primary_key=True)
    coupon_type = orm.Column(orm.Integer)     # 红包类型
    title = orm.Column(orm.VARCHAR)           # 红包标题，如"新年红包"
    desc = orm.Column(orm.VARCHAR)            # 红包描述，如"满10减1"
    price = orm.Column(orm.Integer)           # 红包金额
    condition_price = orm.Column(orm.Integer) # 满减红包的购买限额
    valid_ts = orm.Column(orm.Integer)        # 红包的有效时间，单位：秒
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class AccountCoupon(orm.Model):
    """
    用户红包
    """
    __tablename__ = "account_coupon"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    template_id = orm.Column(orm.Integer)     # 模板编号
    coupon_type = orm.Column(orm.Integer)     # 红包类型
    title = orm.Column(orm.VARCHAR)           # 红包标题，如"新年红包"
    desc = orm.Column(orm.VARCHAR)            # 红包描述，如"满10减1"
    price = orm.Column(orm.Integer)           # 红包金额
    condition_price = orm.Column(orm.Integer)  # 满减红包的购买限额
    status = orm.Column(orm.Integer)          # 红包状态
    start_ts = orm.Column(orm.Integer)        # 开始时间戳
    expire_ts = orm.Column(orm.Integer)       # 过期时间戳
    extend = orm.Column(orm.TEXT)             # 扩展数据, JSON
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)

    @classmethod
    def start_expire_timer(cls, coupon_id, expire_ts):
        # timer to expire
        event_msg = {'coupon_id': coupon_id}
        TimerEvent.submit(
            TIMER_EVENT_TYPE.COUPON_EXPIRED, event_msg, expire_ts)
        # timer to notify
        dt = utc_to_local(datetime.fromtimestamp(expire_ts))
        notify_date = dt.replace(hour=10, minute=0, second=0) - timedelta(1)
        execute_ts = int(time.mktime(local_to_utc(notify_date).timetuple()))
        if execute_ts - now_ts() > 3600 * 24:
            event_msg = {'coupon_id': coupon_id}
            TimerEvent.submit(
                TIMER_EVENT_TYPE.COUPON_NOTIFY, event_msg, execute_ts)

    @classmethod
    def create_from_template(cls, template, user_id, by=None, extend=None, start_ts=None):
        coupon = cls()
        coupon.user_id = user_id
        coupon.template_id = template.id
        coupon.coupon_type = template.coupon_type
        coupon.title = template.title
        coupon.desc = template.desc
        coupon.price = template.price
        coupon.condition_price = template.condition_price
        coupon.status = COUPON_STATUS.UNUSED
        if not start_ts:
            start_ts = now_ts()
        coupon.start_ts = start_ts
        if by:
            coupon.extend = json.dumps({"add_by": by})
        expire_ts = coupon.start_ts + template.valid_ts
        expire_dt = utc_to_local(datetime.fromtimestamp(expire_ts))
        if template.valid_ts == 0:
            # 当天有效
            expire_dt = expire_dt.replace(hour=23, minute=59, second=59)
        elif expire_dt.hour == 0 and expire_dt.minute == 0 and expire_dt.second == 0:
            expire_dt = expire_dt - timedelta(1)
            expire_dt = expire_dt.replace(hour=23, minute=59, second=59)
        coupon.expire_ts = int(time.mktime(local_to_utc(expire_dt).timetuple()))
        if extend:
            coupon.extend = extend
        return coupon


class GroupCoupon(orm.Model):
    """
    群红包(红包袋)
    """
    __tablename__ = "group_coupon"
    id = orm.Column(orm.BigInteger, primary_key=True)
    user_id = orm.Column(orm.BigInteger)
    title = orm.Column(orm.VARCHAR)           # 红包标题，如"新年红包"
    total_count = orm.Column(orm.Integer)     # 包含的红包数量
    left_count = orm.Column(orm.Integer)      # 剩余的红包数量
    coupons = orm.Column(orm.VARCHAR)         # 摇出的红包编号，{phone:coupon_id} JSON
    expire_ts = orm.Column(orm.Integer)       # 过期时间戳
    campaign_id = orm.Column(orm.VARCHAR)     # 关联的活动编号
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class AwaitingCoupon(orm.Model):
    """
    待领取红包(用于活动)
    """
    __tablename__ = "awaiting_coupon"
    id = orm.Column(orm.BigInteger, primary_key=True)
    template_id = orm.Column(orm.Integer)     # 模板编号
    phone = orm.Column(orm.VARCHAR)
    expire_ts = orm.Column(orm.Integer)       # 过期时间戳
    deleted = orm.Column(orm.Integer, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class CouponScope(orm.Model):
    """
    红包使用范围
    """
    __tablename__ = "coupon_scope"
    id = orm.Column(orm.Integer, primary_key=True)
    coupon_tid = orm.Column(orm.Integer)       # 红包模板编号
    activity_tid = orm.Column(orm.Integer)     # 活动模板编号
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
