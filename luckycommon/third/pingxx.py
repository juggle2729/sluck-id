# -*- coding: utf-8 -*-
import logging
import json

import pingpp
from django.conf import settings
from django.utils.encoding import smart_unicode
from future.utils import raise_with_traceback

from luckycommon.model.pay import PAY_TYPE, PINGXX_CHANNNELS
from luckycommon.third.alipay import verify
from luckycommon.utils.exceptions import PingXXError
from luckycommon.order.db.order import (
    sent_red_envelope_callback, received_pingxx_callback)

_LOGGER = logging.getLogger('ofpay')

pingpp.api_key = settings.API_KEY


def pingxx_create_charge(pay, pay_amount, pay_type):
    extra = dict()
    if pay_type == PAY_TYPE.ALIPAY_WAP:
        extra = dict(
            success_url=settings.SUCCESS_URL,
            cancel_url=settings.CANCEL_URL
        )

    # Pingxx unit is cent, so multiply amount by 100
    pay_amount = str(int(float(pay_amount) * 100))

    charge = pingpp.Charge.create(
        order_no=str(pay.id),
        amount=pay_amount,
        app=dict(id=settings.APP_ID),
        channel=PINGXX_CHANNNELS[pay_type],
        currency='cny',
        client_ip='127.0.0.1',
        subject=u'购买网盘空间',
        body=u'购买网盘空间',
        extra=extra
    )
    return charge


def pingxx_create_redenvelope(order_id, amount, open_id, body=""):
    assert 1 <= amount <= 200
    redenvelope = pingpp.RedEnvelope.create(
        order_no=str(order_id),
        channel="wx_pub",
        amount=amount * 100,
        subject=body or u"红包奖品兑换",
        body=body or u"一元购红包奖品兑换",
        currency='cny',
        app=dict(id=settings.APP_ID),
        extra=dict(send_name=u"一元购go"),
        recipient=open_id,
        description=body or u'红包奖品兑换'
    )
    return redenvelope


def pingxx_create_transfer(order_id, amount, open_id, body=""):
    assert amount >= 1
    transfer = pingpp.Transfer.create(
        order_no=str(order_id),
        channel="wx_pub",
        amount=amount * 100,
        type="b2c",
        currency='cny',
        app=dict(id=settings.APP_ID),
        recipient=open_id,
        description=body or u'奖品兑换')
    return transfer


def _get_req_params(req):
    signature = req.META.get('HTTP_X_PINGPLUSPLUS_SIGNATURE')
    body = smart_unicode(req.body)
    if not verify(signature, body):
        raise_with_traceback(PingXXError('pingpp request verify failed!'))
    return json.loads(body)


def check_redenvelope_status(red_envelope_id):
    redenvelope = pingpp.RedEnvelope.retrieve(red_envelope_id)
    return redenvelope['status']


def check_transfer_status(transfer_id):
    transfer = pingpp.Transfer.retrieve(transfer_id)
    return transfer['status']


def check_redenvelope(request):
    body = _get_req_params(request)
    d = body['data']['object']
    if body['type'] == 'red_envelope.sent':
        sent_red_envelope_callback(d['order_no'])
    elif body['type'] == 'red_envelope.received':
        received_pingxx_callback(d['order_no'])
    elif body['type'] == 'transfer.succeeded':
        received_pingxx_callback(d['order_no'])
    else:
        assert False
