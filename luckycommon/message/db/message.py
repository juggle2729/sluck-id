# -*- coding: utf-8 -*-
import logging

from sqlalchemy import and_, or_

from luckycommon.message.model.message import *
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.orm import get_count

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_messages(conversation_id, user_id, limit=0, offset=0):
    query = Message.query.filter(or_(and_(Message.conversation_id == conversation_id, Message.sender_id == user_id, Message.is_delete_by_sender == False),
                                     and_(Message.conversation_id == conversation_id, Message.receiver_id == user_id, Message.is_delete_by_receiver == False)))
    query = query.order_by(Message.id.desc())
    total = get_count(query)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    result = query.all()
    return result, len(result), total


@sql_wrapper
def get_unread_messages_count(conversation_id, user_id):
    query = Message.query.filter(or_(and_(Message.conversation_id == conversation_id, Message.sender_id == user_id, Message.is_read_by_sender == False),
                                     and_(Message.conversation_id == conversation_id, Message.receiver_id == user_id, Message.is_read_by_receiver == False)))
    count = get_count(query)
    return count


@sql_wrapper
def create_user_message(sender_id, receiver_id, content):
    message = Message()
    message.type = MESSAGE_TYPE.USER
    message.sender_id = sender_id
    message.receiver_id = receiver_id
    message.content = content
    message.save()
    return message


@sql_wrapper
def create_system_message(sender_id, receiver_id, content, msg_type=MESSAGE_TYPE.SYSTEM, command=None):
    message = Message()
    message.type = msg_type
    message.sender_id = sender_id
    message.receiver_id = receiver_id
    message.content = content
    message.command = command
    message.save()
    return message


@sql_wrapper
def get_message_by_id(message_id):
    result = Message.query.filter(Message.id == message_id).all()
    if result:
        return result[0]
    return None


@sql_wrapper
def remove_message(message):
    message.delete()


@sql_wrapper
def remove_message_under_conversation(conversation_id, user_id):
    messages = Message.query.filter(Message.conversation_id == conversation_id).all()
    for message in messages:
        if message.sender_id == user_id:
            message.is_delete_by_sender = True
        if message.receiver_id == user_id:
            message.is_delete_by_receiver = True
    orm.session.commit()


@sql_wrapper
def mark_as_read(message, user_id):
    if message.sender_id == user_id:
        message.is_read_by_sender = True
    if message.receiver_id == user_id:
        message.is_read_by_receiver = True
    message.save()
