# -*- coding: utf-8 -*-
from luckycommon.message.model import orm


class Conversation(orm.Model):
    __tablename__ = "conversation"
    id = orm.Column(orm.BigInteger, primary_key=True)
    initiator = orm.Column(orm.BigInteger)
    participator = orm.Column(orm.BigInteger)
    last_message_id = orm.Column(orm.BigInteger)
    count = orm.Column(orm.BigInteger)
    is_read_by_initiator = orm.Column(orm.Boolean, default=True)
    is_read_by_participator = orm.Column(orm.Boolean, default=False)
    is_delete_by_initiator = orm.Column(orm.Boolean, default=False)
    is_delete_by_participator = orm.Column(orm.Boolean, default=False)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
