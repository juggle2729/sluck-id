# -*- coding: utf-8 -*-
from luckycommon.message.model import orm
from luckycommon.utils.types import Enum


MESSAGE_TYPE = Enum({
    "USER": (0L, "user"),
    "SYSTEM": (1L, "system"),
    "TRANSFER": (2L, "transfer"),  # 转账自动消息
})


class Message(orm.Model):
    __tablename__ = "message"
    id = orm.Column(orm.BigInteger, primary_key=True)
    conversation_id = orm.Column(orm.BigInteger)
    sender_id = orm.Column(orm.BigInteger)
    receiver_id = orm.Column(orm.BigInteger)
    type = orm.Column(orm.Integer)
    content = orm.Column(orm.TEXT)
    command = orm.Column(orm.TEXT)
    is_read_by_sender = orm.Column(orm.Boolean, default=True)
    is_read_by_receiver = orm.Column(orm.Boolean, default=False)
    is_delete_by_sender = orm.Column(orm.Boolean, default=False)
    is_delete_by_receiver = orm.Column(orm.Boolean, default=False)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
