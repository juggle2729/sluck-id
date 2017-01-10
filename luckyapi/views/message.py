# -*- coding: utf-8 -*-
import logging

from django.views.decorators.http import require_GET, require_POST
from future.utils import raise_with_traceback

from luckycommon.account import handler as account_handler
from luckycommon.message import handler as message_handler
from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import ParamError
from luckycommon.utils.tz import dt_to_ts

_LOGGER = logging.getLogger('lucky')


@require_GET
@response_wrapper
@token_required
def get_conversations(req):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))
    limit = 0 if size <= 0 else size
    offset = 0 if page <= 0 else (page - 1) * limit
    items, count, total = message_handler.get_conversations(int(req.user_id), limit, offset)
    resp_items = []
    for item in items:
        if item.initiator == int(req.user_id):
            user_id = item.participator
        else:
            user_id = item.initiator
        unread = message_handler.get_conversation_unread_count(item.id, int(req.user_id))
        resp_items.append({
            'id': item.id,
            'user': account_handler.get_user_info_by_uid(user_id),
            'last_message': message_handler.get_message_by_id(item.last_message_id),
            'unread': unread,
            'updated_at': dt_to_ts(item.created_at) * 1000,
        })
    data = {
        'list': resp_items,
        'size': count,
        'total': total
    }
    return data


@require_GET
@response_wrapper
@token_required
def get_messages(req, conversation_id):
    query_dct = req.GET.dict()
    page = int(query_dct.get('page', 0))
    size = int(query_dct.get('size', 0))
    limit = 0 if size <= 0 else size
    offset = 0 if page <= 0 else (page - 1) * limit
    items, count, total = message_handler.get_messages(int(conversation_id), int(req.user_id), limit, offset)
    resp_items = []
    for item in items:
        resp_items.append({
            'id': item.id,
            'sender_id': item.sender_id,
            'receiver_id': item.receiver_id,
            'type': item.type,
            'content': item.content,
            'command': item.command,
            'created_at': dt_to_ts(item.created_at) * 1000,
        })
    participator_id = int(items[0].sender_id)
    if participator_id == int(req.user_id):
        participator_id = items[0].receiver_id
    data = {
        'list': resp_items,
        'participator': account_handler.get_user_info_by_uid(participator_id),
        'size': count,
        'total': total
    }
    return data


@require_POST
@response_wrapper
@token_required
def send_message(req):
    query_dct = req.POST.dict()
    receiver_id = query_dct.get('user_id')
    content = query_dct.get('content')
    if not receiver_id:
        raise_with_traceback(ParamError('parameter receiver_id is missing'))
    if not content:
        raise_with_traceback(ParamError('parameter content is missing'))
    if int(receiver_id) == int(req.user_id):
        raise_with_traceback(ParamError('You can not send message to yourself'))

    success, msg = message_handler.send_message(int(req.user_id), int(receiver_id), content)
    if success:
        return {'msg': msg}
    else:
        raise_with_traceback(ParamError(msg))


@require_POST
@response_wrapper
@token_required
def remove_conversation(req):
    query_dct = req.POST.dict()
    conversation_id = query_dct.get('conversation_id')
    if not conversation_id:
        raise_with_traceback(ParamError('parameter conversation_id is missing'))
    success, msg = message_handler.remove_conversation(int(req.user_id), int(conversation_id))
    if success:
        return {'msg': msg}
    else:
        raise_with_traceback(ParamError(msg))


@require_POST
@response_wrapper
@token_required
def remove_message(req):
    query_dct = req.POST.dict()
    message_id = int(query_dct.get('message_id'))
    if not message_id:
        raise_with_traceback(ParamError('parameter message_id is missing'))
    success, msg = message_handler.remove_message(int(req.user_id), int(message_id))
    if success:
        return {'msg': msg}
    else:
        raise_with_traceback(ParamError(msg))


@require_POST
@response_wrapper
@token_required
def mark_message(req):
    query_dct = req.POST.dict()
    message_id = int(query_dct.get('message_id'))
    if not message_id:
        raise_with_traceback(ParamError('parameter message_id is missing'))
    success, msg = message_handler.mark_message(int(req.user_id), int(message_id))
    if success:
        return {'msg': msg}
    else:
        raise_with_traceback(ParamError(msg))


@require_POST
@response_wrapper
@token_required
def mark_conversation(req):
    query_dct = req.POST.dict()
    conversation_id = int(query_dct.get('conversation_id'))
    if not conversation_id:
        raise_with_traceback(ParamError('parameter conversation_id is missing'))
    success, msg = message_handler.mark_conversation(int(req.user_id), int(conversation_id))
    if success:
        return {'msg': msg}
    else:
        raise_with_traceback(ParamError(msg))
