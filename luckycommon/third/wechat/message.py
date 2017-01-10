# -*- coding: utf-8 -*-

""" parse message and events from wechat; send message to client;
"""
import re
import logging

import xmltodict
import dicttoxml
from hashlib import sha1
from django.conf import settings

# from luckycommon.cache.redis_cache import get_wechat_token
from luckycommon.third.wechat.encrypt import WXBizMsgCrypt
from luckycommon.utils.exceptions import WechatError

UUID_PATTERN = pattern = re.compile('[0-9a-f\-]{36}', re.I)
_LOGGER = logging.getLogger(__name__)

endecoder = WXBizMsgCrypt(settings.WX_CLIENT_TOKEN,
                          settings.WX_ENCODING_AES_KEY,
                          settings.WX_APP_ID)


def get_uuid(content):
    k = UUID_PATTERN.search(content)
    if k:
        return k.group(0)
    else:
        return ''


def parse_request(req):
    query_dct = req.GET.dict()
    body = req.body
    if query_dct.get('encrypt_type', 'raw') == 'raw':
        # 明文
        return xmltodict.parse(body)['xml']
    else:
        # 密文
        ret, data = endecoder.DecryptMsg(
            body, query_dct['msg_signature'],
            query_dct['timestamp'], query_dct['nonce'])
        if ret != 0:
            raise WechatError('decrypt error, code:%s' % ret)
        return xmltodict.parse(data)['xml']


def resp_request(req, data):
    query_dct = req.GET.dict()
    msg = dicttoxml.dicttoxml(data, root=False)
    msg = '<xml>' + msg + '</xml>'
    if query_dct.get('encrypt_type', 'raw') == 'raw':
        return msg
    else:
        ret, msg = endecoder.EncryptMsg(msg, query_dct['timestamp'],
                                        query_dct['nonce'])
        if ret != 0:
            raise WechatError('encrypt error, code:%s' % ret)
        return msg


def check_token(req):
    # for wechat check token
    query_dct = req.GET.dict()
    params = sorted([settings.WX_CLIENT_TOKEN, query_dct[
                    'timestamp'], query_dct['nonce']])
    if query_dct['signature'] == sha1(''.join(params)).hexdigest():
        return True
    else:
        return False
