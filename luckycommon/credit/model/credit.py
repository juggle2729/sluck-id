# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum


RECORD_TYPE = Enum({
    "IN": (1L, "in"),
    "EXCHANGE": (2L, "exchange"),
})

AWARD_CREDIT_UNIT = 20


class CreditRecord(orm.Model):
    """
    积分记录（积分来源/积分兑换） 
    """
    __tablename__ = "credit_record"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    type = orm.Column(orm.Integer)
    title = orm.Column(orm.VARCHAR)
    amount = orm.Column(orm.Integer)          # 交易的积分额度
    balance = orm.Column(orm.Integer)         # 交易后的积分余额
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class DistributeRecord(orm.Model):
    """
    元宝瓜分记录——记录详细记录
    """
    __tablename__ = "credit_distribution"
    id = orm.Column(orm.Integer, primary_key=True)
    term_id = orm.Column(orm.Integer)         # DistributeTerm id
    user_id = orm.Column(orm.Integer)
    user_info = orm.Column(orm.VARCHAR)
    amount = orm.Column(orm.Integer)          # 分得的元宝
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class DistributeTerm(orm.Model):
    """
    元宝瓜分记录——记录期号日期
    """
    __tablename__ = "credit_distribution_term"
    id = orm.Column(orm.Integer, primary_key=True)
    date = orm.Column(orm.VARCHAR)
    pool_amount = orm.Column(orm.Integer)          # 总元宝
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
