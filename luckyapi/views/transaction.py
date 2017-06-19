# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from future.utils import raise_with_traceback

from luckyapi.logic.recharge_card import get_self_recharge_card_status
from luckyapi.logic.transaction import (
    get_user_transactions, create_pay_id, submit_pay, view_pay_status,
    transfer_to_other, get_transfer_records)
from luckycommon.account.db.account import get_user_by_uid
from luckycommon.cache import redis_cache
from luckycommon.db.pay import get_pay
from luckycommon.model.pay import PayType, PayStatus, AVAILABLE_PAY_TYPES
from luckycommon.order.db.order import get_order, get_order_numbers
from luckycommon.third import coda_pay, fortumo_pay, nganluong, precard, paypal_pay, doku, payssion, bluepay, mimo_pay, \
    google_wallet, iap
from luckycommon.third.doku import doku_check_notify
from luckycommon.third.self_recharge_card import pay_via_self_recharge_card
from luckycommon.utils import exceptions as err
from luckycommon.utils import tz
from luckycommon.utils.api import token_required
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.exceptions import AuthenticateError, RechargeCardError
from luckycommon.utils.respcode import StatusCode

_LOGGER = logging.getLogger('pay')


@require_GET
@response_wrapper
@token_required
def get_transactions(request):
    """
    查看交易记录
    """
    user_id = request.user_id

    try:
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 0))
        transaction_type = int(
            request.GET['type']) if request.GET.get('type') else None
    except Exception as e:
        raise_with_traceback(err.ParamError(e))

    if 24 == transaction_type:
        t_list = get_transfer_records(user_id, page, size)
        data = {
            'list': t_list
        }
        return data
    t_list, count = get_user_transactions(
        user_id, page, size, transaction_type)
    data = {
        'list': t_list,
        'page': page if page > 0 else 1,
        'size': len(t_list),
        'total_count': count
    }
    return data


@require_POST
@response_wrapper
@token_required
def transfer_coin(request):
    """
    转赠夺宝币
    """
    user_id = request.user_id
    try:
        other_id = int(request.POST.get('other'))
        amount = int(request.POST.get('amount'))
    except Exception as e:
        raise_with_traceback(err.ParamError(e))
    transfer_to_other(user_id, other_id, amount)
    return {}


@require_GET
@response_wrapper
@token_required
def get_pay_types(request):
    try:
        user_id = request.user_id
        platform = request.GET.get('platform')
        version_code = request.GET.get('version_code', 1)
        locale = request.GET.get('locale')
        chn = request.GET.get('chn')
    except:
        raise err.ParamError('pay type wrong')

    filtered_available_pay_types = filter_available_pay_types(
        AVAILABLE_PAY_TYPES,
        platform,
        version_code,
        locale,
        chn)

    # temp strategy remove MIMO_TELKOMSEL for new registered user
    user = get_user_by_uid(user_id)
    if user.created_at > datetime(2017, 5, 9) and AVAILABLE_PAY_TYPES[PayType.MIMO_TELKOMSEL.value] in filtered_available_pay_types:
        filtered_available_pay_types.remove(AVAILABLE_PAY_TYPES[PayType.MIMO_TELKOMSEL.value])
    # end temp strategy

    data = {
        'list': filtered_available_pay_types,
        'count': len(filtered_available_pay_types)
    }
    return data


def filter_available_pay_types(pay_types, platform, version_code, locale, chn):
    if platform == 'android' and 131 <= int(version_code) <= 133 and locale == 'id':
        return [
            pay_types[PayType.CODA_PAY.value],
            pay_types[PayType.DOKU_VISA.value],
            pay_types[PayType.DOKU_WALLET.value],
            pay_types[PayType.MIMO_BCA.value],
            pay_types[PayType.BLUEPAY_SDK_MOGPLAY.value],
            pay_types[PayType.BLUEPAY_SDK_GAME_ON.value],
            pay_types[PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value],
            pay_types[PayType.BLUEPAY_SDK_ATM.value],
        ]
    if platform == 'android' and 134 <= int(version_code) <= 135 and locale == 'id':
        return [
            pay_types[PayType.MIMO_TELKOMSEL.value],
            pay_types[PayType.CODA_PAY.value],
            pay_types[PayType.DOKU_VISA.value],
            pay_types[PayType.DOKU_WALLET.value],
            pay_types[PayType.MIMO_BCA.value],
            pay_types[PayType.BLUEPAY_SDK_MOGPLAY.value],
            pay_types[PayType.BLUEPAY_SDK_GAME_ON.value],
            pay_types[PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value],
            pay_types[PayType.BLUEPAY_SDK_ATM.value],
        ]
    if platform == 'android' and 136 <= int(version_code) and locale == 'id':
        return [
            pay_types[PayType.SELF_RECHARGE_CARD.value],
            pay_types[PayType.MIMO_INDOSAT.value],
            pay_types[PayType.MIMO_THREE.value],
            pay_types[PayType.MIMO_XL.value],
            pay_types[PayType.MIMO_TELKOMSEL.value],
            pay_types[PayType.CODA_PAY.value],
            pay_types[PayType.DOKU_VISA.value],
            pay_types[PayType.DOKU_WALLET.value],
            pay_types[PayType.MIMO_BCA.value],
            pay_types[PayType.BLUEPAY_SDK_MOGPLAY.value],
            pay_types[PayType.BLUEPAY_SDK_GAME_ON.value],
            pay_types[PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value],
            pay_types[PayType.BLUEPAY_SDK_ATM.value],
        ]
    if platform == 'android' and locale == 'id':
        return [
            pay_types[PayType.MIMO_BCA.value],
            pay_types[PayType.BLUEPAY_SDK_MOGPLAY.value],
            pay_types[PayType.BLUEPAY_SDK_GAME_ON.value],
            pay_types[PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value],
            pay_types[PayType.BLUEPAY_SDK_ATM.value],
        ]
    if platform == 'ios' and locale == 'id':
        return [
            pay_types[PayType.SELF_RECHARGE_CARD.value],
            pay_types[PayType.MIMO_INDOSAT.value],
            pay_types[PayType.MIMO_THREE.value],
            pay_types[PayType.MIMO_XL.value],
            pay_types[PayType.MIMO_TELKOMSEL.value],
            pay_types[PayType.CODA_PAY.value],
            # pay_types[PayType.BLUEPAY_SMS.value],
            pay_types[PayType.DOKU_VISA.value],
            pay_types[PayType.DOKU_WALLET.value],
            pay_types[PayType.MIMO_BCA.value],
        ]
    if platform == 'web':
        return [
            pay_types[PayType.CODA_PAY.value],
        ]
    return [
        pay_types[PayType.BLUEPAY_SDK_MOGPLAY.value],
        pay_types[PayType.BLUEPAY_SDK_GAME_ON.value],
        pay_types[PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value],
        pay_types[PayType.BLUEPAY_SDK_ATM.value],
    ]


@require_POST
@response_wrapper
@token_required
def create_pay(request):
    try:
        pay_type = int(request.POST.get('type'))
    except:
        raise err.ParamError('pay type wrong')

    pay_id = create_pay_id(request.user_id, pay_type)
    return {'pay_id': str(pay_id)}


DAILY_RECHARGE_LIMIT = 100000


@require_POST
@response_wrapper
@token_required
def pay_submit(request, pay_id):
    try:
        pay_amount = float(request.POST.get('pay_amount'))  # 充值金额
        activity_id = request.POST.get('activity_id', 0)
        quantity = int(request.POST.get('quantity', 0))
        return_url = request.POST.get('return_url')
        buy_list = request.POST.get('buy_list')
        if buy_list:
            buy_list = json.loads(buy_list)
        coupon = request.POST.get('coupon')
        pk_size = request.POST.get('pk_size')
    except:
        raise err.ParamError('pay type wrong')

    user_id = request.user_id

    # check pay_amount
    try:
        date_str = tz.today_str()
        today_stats = redis_cache.get_daily_stats(date_str, user_id) or {}
        today_recharge = today_stats.get('total_recharge', 0)
    except Exception as e:
        _LOGGER.exception('pay submit check pay amount exception, %s', e)
        today_recharge = 0

    if int(today_recharge) + pay_amount > DAILY_RECHARGE_LIMIT:
        raise err.ResourceInsufficient(
            "pay limit reached.", status=StatusCode.REACH_LIMIT)

    pay_context = {}
    pay_context.update({
        'activity_id': activity_id,
        'quantity': quantity,
        'buy_list': buy_list,
        'coupon': coupon,
        'pk_size': pk_size,
    })
    pay_data = submit_pay(user_id, pay_id, pay_amount, pay_context, return_url)
    return pay_data


@require_GET
@response_wrapper
def get_pay_status(request, pay_id):
    pay = view_pay_status(pay_id)
    ext = {} if not pay.extend else json.loads(pay.extend)
    ext.update({
        'type': pay.pay_type,
        'price': pay.price,
        'activity_id': pay.activity_id,
        'quantity': pay.quantity
    })
    if ext.get('refer_order_id'):
        refer_order = get_order(ext['refer_order_id'])
        if refer_order.lucky_numbers:
            refer_order_numbers = refer_order.lucky_numbers.split(',')
        else:
            numbers = get_order_numbers(refer_order.id)
            refer_order_numbers = numbers
        ext.update({
            'refer_order_numbers': refer_order_numbers
        })
    if ext.get('refer_order_list'):
        refer_order_list = ext['refer_order_list']
        refer_list = []
        for refer_order_id in refer_order_list:
            refer_order = get_order(refer_order_id)
            if refer_order.lucky_numbers:
                refer_order_numbers = refer_order.lucky_numbers.split(',')
            else:
                numbers = get_order_numbers(refer_order.id)
                refer_order_numbers = numbers
            refer_list.append({
                'activity_id': refer_order.activity_id,
                'refer_order_numbers': refer_order_numbers
            })
        ext.update({
            'refer_order_list': refer_list
        })
    if pay.status != PayStatus.DONE.value:
        _LOGGER.warn('pay status invalid, pay_id[%s] status[%s]' % (
            pay_id, pay.status))
    data = {
        'status': pay.status,
        'extend': ext
    }
    return data


@require_GET
def paypal_notify(request):
    try:
        token = request.GET.get('token')
        paypal_pay.paypal_do_charge(token)
        return redirect(settings.PAYPAL_SUCCESS_URL)
    except Exception:
        return redirect(settings.PAYPAL_FAILED_URL)


@require_GET
def paypal_success(request):
    return TemplateResponse(request, 'pay_success.html', {'return_url': settings.PAYPAL_RETURN_URL})


@require_GET
def paypal_failed(request):
    return TemplateResponse(request, 'pay_failed.html', {'return_url': settings.PAYPAL_RETURN_URL})


@require_http_methods(["GET", "POST"])
def close_webview(request):
    return TemplateResponse(request, 'close_webview.html')


@require_GET
def coda_proxy(request):
    return TemplateResponse(request, 'coda_proxy.html')


@require_GET
def coda_gateway(request, token):
    return TemplateResponse(request, 'coda_pay_gate.html',
                            {'token': token,
                             'css': settings.CODA_PAY_CSS,
                             'js': settings.CODA_PAY_JS})


@require_GET
def coda_notify(request):
    try:
        coda_pay.coda_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Coda Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


@require_POST
@response_wrapper
def google_notify(request):
    try:
        resp = google_wallet.google_check_notify(request)
        return resp
    except Exception as e:
        _LOGGER.exception('Google Pay notify exception.(%s)' % e)
        return {'msg': e}


@require_POST
@response_wrapper
def iap_notify(request):
    '''
    校验IAP 票据
    :param request:
    :return:
    '''
    if not request.user_id:
        raise AuthenticateError('not login')
    try:
        user_id = request.user_id
        env_flag = iap.check_sandbox_flag(request)
        receipt_dic = json.loads(request.body)
        resp = iap.iap_check_notify(user_id, receipt_dic, env_flag)
        return resp
    except Exception as e:
        _LOGGER.exception('IAP Pay notify exception.(%s)' % e)
        return {'msg': e}


@require_GET
def bluepay_notify(request):
    try:
        bluepay.bluepay_check_notify(request)
        return HttpResponse('status=200', status=200)
    except Exception as e:
        _LOGGER.exception('Blue Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


@require_GET
def nganluong_return_page(request, pay_id):
    check_order_url = settings.NGANLUONG_CHECK_ORDER_URL
    return TemplateResponse(request, 'nganluong_return.html', {'pay_id': pay_id, 'check_order_url': check_order_url})


@require_POST
@response_wrapper
def nganluong_check_order(request):
    pay_id = request.POST.get('pay_id')
    try:
        nganluong.ewallet_check_order(pay_id)
        return {'success': True}
    except Exception as e:
        _LOGGER.exception('nganluong Pay check order exception.(%s)' % e)
        return {'success': False}


@require_POST
def nganluong_handle_notify(request):
    try:
        nganluong.handle_notify(request)
        return HttpResponse('Y', status=200)
    except Exception as e:
        _LOGGER.exception('nganluong Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def payssion_notify(request):
    try:
        payssion.payssion_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Payssion notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


@require_GET
def fortumo_notify(request):
    try:
        fortumo_pay.fortumo_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Coda Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def indomog_notify(request):
    try:
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Indomog Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def mimo_notify(request):
    try:
        mimo_pay.mimo_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('MIMO Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def bubble_mimo_notify(request):
    """ mimopay callback api for bubble and telkomsel """
    try:
        mimo_pay.bubble_mimo_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Bubble MIMO Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def doku_notify(request):
    try:
        doku_check_notify(request)
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Doku Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


def doku_identify(request):
    try:
        return HttpResponse('ResultCode=0', status=200)
    except Exception as e:
        _LOGGER.exception('Doku Pay notify exception.(%s)' % e)
        return HttpResponse('N', status=400)


@require_http_methods(["GET", "POST"])
def precard_gateway(request, pay_id):
    pay = get_pay(pay_id)
    if request.method == "GET":
        if not pay or pay.status != PayStatus.SUBMIT.value:
            return HttpResponse(u'Vui lòng đặt hàng lại', status=200)
        else:
            card_type = request.GET.get('card_type', '')
            card_num = request.GET.get('card_num', '')
            card_secret = request.GET.get('card_secret', '')
            return TemplateResponse(request,
                                    'precard_gateway.html',
                                    {'card_type': card_type, 'card_num': card_num, 'card_secret': card_secret})
    if request.method == "POST":
        try:
            card_type = request.POST.get('card_type')
            card_num = request.POST.get('card_num')
            card_secret = request.POST.get('card_secret')
        except:
            raise err.ParamError('parameter invalid')

        result = precard.pay_via_nganluong(pay, card_num, card_secret, card_type)
        if result:
            pay_status_url = settings.PAY_GATEWAY_STATUS_URL % pay_id
            return TemplateResponse(request, 'pay_status.html', {'pay_status_url': pay_status_url})
        else:
            return HttpResponse(u'Thanh toán thất bại', status=200)


@require_POST
@response_wrapper
@token_required
def consume_self_recharge_card(request, pay_id):
    pay = get_pay(pay_id)
    if not pay:
        raise RechargeCardError(status=StatusCode.PAY_ID_NOT_FOUND)
    if pay.status != PayStatus.SUBMIT.value:
        raise RechargeCardError(status=StatusCode.PAY_STATUS_INVALID)
    card_id = int(request.POST.get('card_id'))
    card_secret = request.POST.get('card_secret').upper()
    success = pay_via_self_recharge_card(pay, card_id, card_secret)
    return {
        'success': success,
    }


@require_GET
@response_wrapper
@token_required
def check_self_recharge_card(request):
    card_id = request.GET.get('card_id')
    status = get_self_recharge_card_status(card_id)
    return {
        'card_status': status,
    }
