# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum

from django.conf import settings
from django.utils.translation import ugettext as _


CAMPAIGN_TYPE = Enum({
    "RECHARGE_CAMPAIGN": (1L, "recharge campaign A"),  # 累积充值送红包活动
    "DAILY_BUY_CAMPAIGN": (2L, "daily buy campaign"),   # 每日购买活动
    "MOIST_CAMPAIGN": (3L, "moist campaign"),       # 充50送88活动
    "WEALTH_GOD_CAMPAIGN": (4L, "god of wealth campaign"),   # 财神指路活动
    "NEW_RECHARGE_CAMPAIGN": (5L, "recharge campaign A"),  # 单次充值送红包活动
})


LEVEL_STATUS = Enum({
    "UNREACHED": (-1, "unreached"),  # 等级未达成
    "UNOPEN": (0L, "unopen"),        # 红包未拆开
    "OPENED": (1L, "opened"),        # 红包已拆开
})


CAMPAIGN_DICT = {
    '10010': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': _('recharge campaign'),
        'url': '',
        'start_time': '2016-02-02 00:00:00',
        'end_time': '2016-02-22 23:59:59',
    },
    '10011': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': _('recharge campaign stage 2'),
        'url': '',
        'start_time': '2016-04-06 00:00:00',
        'end_time': '2016-04-30 23:59:59',
    },
    '10012': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': _('recharge campaign stage 3'),
        'url': '',
        'start_time': '2016-05-04 00:00:00',
        'end_time': '2016-05-17 23:59:59',
    },
    '10013': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': _('recharge campaign stage 4'),
        'url': '',
        'start_time': '2016-05-21 00:00:00',
        'end_time': '2016-05-31 23:59:59',
    },
    '10014': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': _('recharge campaign stage 5'),
        'url': '',
        'start_time': '2016-06-01 00:00:00',
        'end_time': '2016-06-15 23:59:59',
    },
    '10016': {
        'type': CAMPAIGN_TYPE.RECHARGE_CAMPAIGN,
        'title': u'抢万元红包',
        'url': '',
        'start_time': '2016-07-11 00:00:00',
        'end_time': '2016-07-20 23:59:59',
    },
    '20010': {
        'type': CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN,
        'title': _('daily buy campaign'),
        'url': '',
        'start_time': '2016-02-02 00:00:00',
        'end_time': '2016-02-22 23:59:59',
    },
    '20011': {
        'type': CAMPAIGN_TYPE.DAILY_BUY_CAMPAIGN,
        'title': _('daily buy campaign stage 2'),
        'url': '',
        'start_time': '2016-04-06 00:00:00',
        'end_time': '2016-04-30 23:59:59',
    },
    '30010': {
        'type': CAMPAIGN_TYPE.MOIST_CAMPAIGN,
        'title': _('moist campaign'),
        'url': '%s/discovery/charge_fifty' % (settings.WEB_APP_ROOT_URL),
        'start_time': '2016-03-14 00:00:00',
        'end_time': '2016-12-31 23:59:59',
    },
    '40010': {
        'type': CAMPAIGN_TYPE.WEALTH_GOD_CAMPAIGN,
        'title': _('wealth god campaign'),
        'url': '',
        'start_time': '2016-03-01 00:00:00',
        'end_time': '2026-03-01 23:59:59',
    },
    '50010': {
        'type': CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN,
        'title': u'端午节',
        'url': '',
        'start_time': '2016-06-04 00:00:00',
        'end_time': '2016-06-17 23:59:59',
    },
    '50011': {
        'type': CAMPAIGN_TYPE.NEW_RECHARGE_CAMPAIGN,
        'title': u'七月充值活动',
        'url': '',
        'start_time': '2016-07-01 00:00:00',
        'end_time': '2016-07-10 23:59:59',
    },
}


class RechargeCampaign(orm.Model):
    """
    充值送红包活动
    """
    __tablename__ = "recharge_campaign"
    id = orm.Column(orm.BigInteger, primary_key=True)
    campaign_id = orm.Column(orm.Integer)     # 活动编号，如10010
    user_id = orm.Column(orm.Integer)         # 用户编号
    level = orm.Column(orm.Integer)           # 达成的等级, 1:20, 2:50...
    current_price = orm.Column(orm.Integer)   # 当前达成的红包金额
    status = orm.Column(orm.Integer, default=0)          # 红包是否打开，0：未打开， 1：已打开
    coupons = orm.Column(orm.VARCHAR)         # 打开的红包编号，以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class DailyCampaign(orm.Model):
    """
    每日购买活动
    """
    __tablename__ = "daily_buy_campaign"
    id = orm.Column(orm.BigInteger, primary_key=True)
    campaign_id = orm.Column(orm.Integer)     # 活动编号，如20010
    user_id = orm.Column(orm.Integer)         # 用户编号
    date = orm.Column(orm.VARCHAR)            # 日期 '2015-12-30'
    level = orm.Column(orm.Integer)           # 今日第N次达成目标
    current_amount = orm.Column(orm.Integer)  # 当前购买人次
    status = orm.Column(orm.Integer)          # 红包是否分享，0：未分享， 1：已分享
    coupon_id = orm.Column(orm.Integer)       # 分享的群红包编号
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class MoistCampaign(orm.Model):
    """
    充50送88活动
    """
    __tablename__ = "moist_campaign"
    id = orm.Column(orm.BigInteger, primary_key=True)
    campaign_id = orm.Column(orm.Integer)
    user_id = orm.Column(orm.Integer)
    recharge_price = orm.Column(orm.Integer)
    award_price = orm.Column(orm.Integer)
    coupons = orm.Column(orm.VARCHAR)            # 赠送的红包编号，以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


GOD_FRESH_LIMIT = 3    # 财神指路刷新次数上限


class GodCampaign(orm.Model):
    """
    财神指路活动
    """
    __tablename__ = "god_campaign"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    date = orm.Column(orm.VARCHAR)                    # 日期 '2015-12-30'
    first_tid = orm.Column(orm.VARCHAR)               # 第一个商品id
    second_tid = orm.Column(orm.VARCHAR)              # 第二个商品id
    third_tid = orm.Column(orm.VARCHAR)               # 第三个商品id
    first_blood = orm.Column(orm.Integer, default=0)  # 0:未达成  1:已达成，待激活  2:已激活
    double_kill = orm.Column(orm.Integer, default=0)
    triple_kill = orm.Column(orm.Integer, default=0)
    fresh_times = orm.Column(orm.Integer, default=1)  # 刷新次数
    winned_tids = orm.Column(orm.VARCHAR)             # 已中奖的tid，逗号分隔
    coupons = orm.Column(orm.VARCHAR)                 # 已领取的红包id，逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class RecommendCampaign(orm.Model):
    """
    推荐活动
    """
    __tablename__ = "recommend_campaign"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    campaign_name = orm.Column(orm.VARCHAR)
    date = orm.Column(orm.VARCHAR)                    # 日期 '2015-12-30'
    coupons = orm.Column(orm.VARCHAR)                 # 已领取的红包id，逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class NewRechargeCampaign(orm.Model):
    """
    新充值送红包活动
    """
    __tablename__ = "new_recharge_campaign"
    id = orm.Column(orm.BigInteger, primary_key=True)
    campaign_id = orm.Column(orm.Integer)     # 活动编号，如10010
    user_id = orm.Column(orm.Integer)         # 用户编号
    level = orm.Column(orm.Integer)           # 达成的等级, 1:20, 2:50...
    current_price = orm.Column(orm.Integer)   # 当前达成的红包金额
    status = orm.Column(orm.Integer, default=0)          # 红包是否打开，0：未打开， 1：已打开
    coupons = orm.Column(orm.VARCHAR)         # 打开的红包编号，以逗号分隔
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
