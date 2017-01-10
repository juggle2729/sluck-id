# -*- coding: utf-8 -*-

from luckycommon.message.db import conversation as conversation_db
from luckycommon.message.db import message as message_db
from luckycommon.utils.tz import dt_to_ts


def get_conversations(user_id, limit, offset):
    return conversation_db.get_conversations(user_id, limit, offset)


def get_conversation_unread_count(conversation_id, user_id):
    return message_db.get_unread_messages_count(conversation_id, user_id)


def get_messages(conversation_id, user_id, limit=0, offset=0):
    return message_db.get_messages(conversation_id, user_id, limit, offset)


def get_message_by_id(message_id):
    message = message_db.get_message_by_id(message_id)
    if message:
        data = {
            'id': message.id,
            'sender_id': message.sender_id,
            'receiver_id': message.receiver_id,
            'type': message.type,
            'content': message.content,
            'command': message.command,
            'created_at': dt_to_ts(message.created_at) * 1000,
        }
        return data
    return None


def send_message(sender_id, receiver_id, content, msg_type=None):
    if not msg_type:
        message = message_db.create_user_message(sender_id, receiver_id, content)
    else:
        message = message_db.create_system_message(sender_id, receiver_id, content, msg_type=msg_type)
    conversation = conversation_db.find_conversation_by_sender_receiver(sender_id, receiver_id)
    if not conversation:
        conversation = conversation_db.create_conversation(sender_id, receiver_id)
    conversation_db.set_last_message(conversation, message)
    return True, 'message sent'


def remove_conversation(user_id, conversation_id):
    conversation = conversation_db.get_conversation_by_id(conversation_id)
    if not conversation:
        return False, 'conversation not found'
    if conversation.initiator != user_id and conversation.participator != user_id:
        return False, 'ACL error'
    conversation_db.mark_as_read(conversation, user_id)
    messages = message_db.get_messages(conversation_id, user_id)[0]
    for message in messages:
        mark_message(user_id, message.id)
    message_db.remove_message_under_conversation(conversation_id, user_id)
    conversation_db.remove_conversation(conversation, user_id)
    return True, 'conversation removed'


def remove_message(user_id, message_id):
    message2remove = message_db.get_message_by_id(message_id)
    if not message2remove:
        return False, 'message not found'
    if message2remove.sender_id != user_id and message2remove.receiver_id != user_id:
        return False, 'ACL error'
    conversation = conversation_db.get_conversation_by_id(message2remove.conversation_id)
    if message_id == conversation.last_message_id:
        second_last_message = get_second_last_message(conversation)
        if second_last_message:
            conversation_db.set_last_message(conversation, second_last_message)
            conversation_db.decrease_count(conversation)
        else:
            conversation_db.remove_conversation(conversation, user_id)
    else:
        conversation_db.decrease_count(conversation)
    message_db.remove_message(message2remove)
    return True, 'message removed'


def get_second_last_message(conversation):
    result, count, total = message_db.get_messages(conversation.id, 2, 0)
    if len(result) > 1:
        return result[1]
    else:
        return None


def mark_conversation(user_id, conversation_id):
    conversation = conversation_db.get_conversation_by_id(conversation_id)
    if not conversation:
        return False, 'conversation not found'
    if conversation.initiator != user_id and conversation.participator != user_id:
        return False, 'ACL error'
    conversation_db.mark_as_read(conversation, user_id)
    messages = message_db.get_messages(conversation_id, user_id)[0]
    for message in messages:
        mark_message(user_id, message.id)
    return True, 'conversation marked as read'


def mark_message(user_id, message_id):
    message = message_db.get_message_by_id(message_id)
    if not message:
        return False, 'message not found'
    if message.sender_id != user_id and message.receiver_id != user_id:
        return False, 'ACL error'
    message_db.mark_as_read(message, user_id)
    return True, 'message marked as read'
