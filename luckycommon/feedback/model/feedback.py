# -*- coding: utf-8 -*-
from luckycommon.feedback.model import orm


class Feedback(orm.Model):
    __tablename__ = "feedback"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    nick_name = orm.Column(orm.VARCHAR)
    qq = orm.Column(orm.VARCHAR)
    phone = orm.Column(orm.VARCHAR)
    content = orm.Column(orm.TEXT)
    chn = orm.Column(orm.VARCHAR)
    cvc = orm.Column(orm.VARCHAR)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
