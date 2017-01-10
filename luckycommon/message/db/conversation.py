# -*- coding: utf-8 -*-
import logging

from sqlalchemy import or_, and_

from luckycommon.message.model.conversation import *
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.orm import get_count

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_conversations(uid, limit, offset):
    query = Conversation.query.filter(or_(and_(Conversation.initiator == uid, Conversation.is_delete_by_initiator == False),
                                          and_(Conversation.participator == uid, Conversation.is_delete_by_participator == False)))
    query = query.order_by(Conversation.updated_at.desc())
    total = get_count(query)
    if limit > 0:
        query = query.limit(limit)
    if offset > 0:
        query = query.offset(offset)
    result = query.all()
    return result, len(result), total


@sql_wrapper
def find_conversation_by_sender_receiver(sender_id, receiver_id):
    result = Conversation.query.filter(Conversation.initiator == sender_id).filter(Conversation.participator == receiver_id).all() + \
             Conversation.query.filter(and_(Conversation.initiator == receiver_id, Conversation.participator == sender_id)).all()
    if result:
        return result[0]
    return None


@sql_wrapper
def set_last_message(conversation, message):
    conversation.last_message_id = message.id
    if conversation.count:
        conversation.count += 1
    else:
        conversation.count = 1
    message.conversation_id = conversation.id
    conversation.is_delete_by_initiator = False
    conversation.is_delete_by_participator = False
    conversation.save()
    message.save()


@sql_wrapper
def create_conversation(sender_id, receiver_id):
    conversation = Conversation()
    conversation.initiator = sender_id
    conversation.participator = receiver_id
    conversation.save()
    return conversation


@sql_wrapper
def get_conversation_by_id(conversation_id):
    result = Conversation.query.filter(Conversation.id == conversation_id).all()
    if result:
        return result[0]
    return None


@sql_wrapper
def remove_conversation(conversation, user_id):
    if conversation.initiator == user_id:
        conversation.is_delete_by_initiator = True
    if conversation.participator == user_id:
        conversation.is_delete_by_participator = True
    conversation.save()


@sql_wrapper
def decrease_count(conversation):
    if conversation.count > 0:
        conversation.count -= 1
        conversation.save()


@sql_wrapper
def mark_as_read(conversation, user_id):
    if conversation.initiator == user_id:
        conversation.is_read_by_initiator = True
    if conversation.participator == user_id:
        conversation.is_read_by_participator = True
    conversation.save()
