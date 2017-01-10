# -*- coding: utf-8 -*-
import logging

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.utils.encoding import smart_unicode

from luckycommon.third.wechat.message import (check_token, parse_request,
                                              resp_request, get_uuid)
from luckycommon.third.pingxx import (pingxx_create_redenvelope,
                                      pingxx_create_transfer)
from luckycommon.order.model.order import (RED_ENVELOPE_STATUS,
                                           RED_ENVELOPE_TYPE)
from luckycommon.order.db.order import (send_red_envelope,
                                        get_red_envelope_info)
from luckycommon.cache import redis_cache
from luckycommon.utils.tz import now_ts

_LOGGER = logging.getLogger('ofpay')


def _generate_resp(req, data):
    if not data:
        return HttpResponse('', status=200)
    return HttpResponse(resp_request(req, data), status=200)


def _parse_text_content(content, open_id):
    code = get_uuid(content)
    if code:
        info = get_red_envelope_info(code)
        f = pingxx_create_redenvelope
        if info.get('type', 0) == RED_ENVELOPE_TYPE.TRANSFER:
            f = pingxx_create_transfer

        if not info:
            return u"兑换码不存在"
        elif info.get('status') == RED_ENVELOPE_STATUS.EXCHANGE_FAILED:
            return u'自动兑换失败，等待运营人工处理，请勿再次尝试'
        elif info.get('status') == RED_ENVELOPE_STATUS.EXCHANGED:
            return u'该兑换码已使用。若因微信系统异常导致红包无法正常领取，请不要担心，工作人员将会在2个工作日内核查无误后手动补发。'
        elif not redis_cache.lock_red_envelope(open_id):
            return u'由于微信官方限制，请每隔一分钟兑换一次'
        body = u'%s期%s元红包' % (info['term_number'], info['price'])

        redenvelope = f(info['order_id'], info['price'], open_id, body=body)
        if redenvelope['status'] == 'failed':
            msg = smart_unicode(redenvelope['failure_msg'])
            send_red_envelope(code, open_id, success=False,
                              fail_msg=msg,
                              third_id=redenvelope['id'])
            _LOGGER.error('send red envelope error, order_id: %s, msg:%s',
                          info.get('order_id'), msg)
            return u'自动兑换失败，等待运营人工处理，请勿再次尝试'
        else:
            send_red_envelope(code, open_id, success=True,
                              third_id=redenvelope['id'])
            return ''
    return u'公众号暂无客服人员处理，如有问题请从客户端内反馈，带来不便之处还请谅解。'


class WechatMsgView(TemplateView):

    def get(self, req):
        if check_token(req):
            return HttpResponse(req.GET.get('echostr'), status=200)
        else:
            return HttpResponse('', status=500)

    def post(self, req):
        if not check_token(req):
            # do nothing
            return _generate_resp(req, '')
        params = parse_request(req)
        resp = {
            "ToUserName": params['FromUserName'],
            "FromUserName": params['ToUserName'],
            "CreateTime": now_ts()
        }
        try:
            if params['MsgType'] == 'text':
                content = params['Content']
                resp_content = _parse_text_content(
                    content, params['FromUserName'])
                if not resp_content:
                    return _generate_resp(req, '')
                else:
                    resp['MsgType'] = 'text'
                    resp['Content'] = resp_content
                    return _generate_resp(req, resp)
        except Exception:
            _LOGGER.exception('wechat callback error')
            resp['MsgType'] = 'text'
            resp['Content'] = u'系统错误，请稍后再试。如多次失败，请联系客服人员。'
            return _generate_resp(req, resp)
        return _generate_resp(req, '')
