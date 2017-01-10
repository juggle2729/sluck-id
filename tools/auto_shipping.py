# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import base64
import sys
from lxml import etree
import requests
from datetime import timedelta
from datetime import datetime
from hashlib import sha1

import os

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckyapi.logic.coupon import send_coupon_to_user
from luckyapi.account.auth import remove_prefix

from luckycommon.push import handler as push_handler
from luckycommon.cache import redis_cache

from luckycommon.order.model.order import AwardedOrder, ORDER_STATUS
from luckycommon.order.handler import show_order
from luckycommon.order.db import order as order_db
from luckycommon.model.shipping import AutoShipping
from luckycommon.third.sms.helper import send_sms
from luckycommon.model.receipt import SHIPPING_TYPE
from luckycommon.db.goods import get_goods
from luckycommon.db.activity import get_activity, get_activity_users
from luckycommon.db.transaction import add_system_award_transaction
#from luckycommon.strategy.handler import is_valid_user

from django.conf import settings

_LOGGER = logging.getLogger('lucky')

def strip_phone(phone_number):
    phone_number = str(phone_number)
    prefix_list = ['62', '0', '620', '062']
    for prefix in prefix_list:
        phone_number = remove_prefix(phone_number, prefix)
    return phone_number


_REQ_DATA = '<?xml version="1.0" ?><datacell><perintah>charge</perintah><oprcode>%s</oprcode><userid>62LFI950</userid><time>145339</time><msisdn>%s</msisdn> <ref_trxid>%s</ref_trxid><sgn>%s</sgn> </datacell>'

_DATACELL_URL = 'http://117.104.201.18:7712/TokoSeribu.php'
_STEAM_GATE = "https://www.indomog.com/indomog2/new_core/index.php/h2h_rpc/server"


_STEAM_REQ = '''
<methodCall>
  <methodName>Shop</methodName>
  <params>
    <param>
      <value>
        <struct>
          <member>
            <name>RMID</name>
            <value>
              <string>1612414100</string>
            </value>
          </member>
          <member>
            <name>QID</name>
            <value>
              <string>%s</string>
            </value>
          </member>
          <member>
            <name>RC</name>
            <value>
              <string>5003</string>
            </value>
          </member>
          <member>
            <name>IPD</name>
            <value>
              <string>G001T001</string>
            </value>
          </member>
          <member>
            <name>EmailHP</name>
            <value>
              <string>081388505363</string>
            </value>
          </member>
          <member>
            <name>ProdID</name>
            <value>
              <string>%s</string>
            </value>
          </member>
		  <member>
            <name>Qty</name>
            <value>
              <string>1</string>
            </value>
          </member>
		  <member>
			<name>ProdAccID</name>
			<value><string></string></value>
			</member>
		<member>
		<name>ProdBillID</name>
		<value><string></string></value>
		</member>
          <member>
            <name>Remark</name>
            <value>
              <string>%s</string>
            </value>
          </member>
          <member>
            <name>Now</name>
            <value>
              <datetime.iso8601>%s</datetime.iso8601>
            </value>
          </member>
          <member>
            <name>Signature</name>
            <value>
              <string>%s</string>
            </value>
          </member>
        </struct>
      </value>
    </param>
  </params>
</methodCall>'''
COIN_TIDS = []

HUAFEI_TIDS = {
    666: 10,
    667: 50,
    668: 100,
}

CARRIER_HUAFEI_TIDS = {
    728:'TEL.5',
    738:'TEL.10',
    737:'TEL.20',
    736:'TEL.25',
    735:'TEL.50',
    734:'TEL.100',
    726:'XL.5',
    749:'XL.10',
    748:'XL.15',
    747:'XL.25',
    746:'XL.50',
    745:'XL.100',
    725:'SF.5',
    756:'SF.10',
    755:'SF.20',
    754:'SF.25',
    753:'SF.30',
    752:'SF.50',
    751:'SF.60',
    750:'SF.100',
    724:'TRI.1',
    762:'TRI.5',
    761:'TRI.10',
    760:'TRI.20',
    759:'TRI.30',
    758:'TRI.50',
    757:'TRI.100',
    727:'IR.5',
    744:'IR.10',
    743:'IR.20',
    742:'IR.25',
    741:'IR.30',
    740:'IR.50',
    739:'IR.100',
}

_STEAM_TIDS = {
    694:'steam idr12000',
    695:'steam idr45000',
    661:'steam idr60000',
    662:'steam idr90000',
    663:'steam idr120000',
    664:'steam idr250000',
    665:'steam idr400000',
    696:'steam idr600000',
    779:'garena v10',
    778:'garena v20',
    777:'garena v50',
    776:'garena v100',
}

_CARRIER_PREFIX = {
        '0812': 'TEL',
        '0813': 'TEL',
        '0821': 'TEL',
        '0822': 'TEL',
        '0823': 'TEL',
        '0851': 'TEL',
        '0852': 'TEL',
        '0853': 'TEL',
        '0814': 'IR',
        '0815': 'IR',
        '0816': 'IR',
        '0855': 'IR',
        '0856': 'IR',
        '0857': 'IR',
        '0858': 'IR',
        '0817': 'XL',
        '0818': 'XL',
        '0819': 'XL',
        '0831': 'XL',
        '0832': 'XL',
        '0834': 'XL',
        '0838': 'XL',
        '0859': 'XL',
        '0877': 'XL',
        '0878': 'XL',
        '0895': 'TRI',
        '0896': 'TRI',
        '0897': 'TRI',
        '0898': 'TRI',
        '0899': 'TRI',
        '0881': 'SF',
        '0882': 'SF',
        '0883': 'SF',
        '0884': 'SF',
        '0885': 'SF',
        '0886': 'SF',
        '0887': 'SF',
        '0888': 'SF',
        '0889': 'SF',
}

def stringxor(str1,str2):
    orxstr=""
    for i in range(0,len(str1)):
        rst=ord(list(str1)[i])^ord(list(str2)[i])
        orxstr=orxstr+ chr(rst)
    return orxstr


def _get_carrier(phone):
    prefix = phone[:4]
    if prefix not in _CARRIER_PREFIX:
        return None
    else:
        return _CARRIER_PREFIX[prefix]

def shipping_steam(await_order, activity):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    #if not is_valid_user(user_id, activity):
    #    print 'found invalid user %s' % user_id
    #    _LOGGER.info('found invalid user %s %s', user_id, await_order.order_id)
    #    # update order
    #    order_db.update_order_by_id(
    #        await_order.order_id,
    #        {
    #            'status': ORDER_STATUS.DEAL,
    #            'ship_status': SHIP_STATUS.ILLEGAL,
    #            'extend': json.dumps({'illegal': 1})
    #        })
    #    # black it
    #    account_db.black_account(user_id)
    #    return
    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    # do recharge
    print 'begin recharge, %s' % await_order.order_id
    charge_account = receipt_address.get('phone')
    if not charge_account:
        return
    # check zero
    time_t = str(datetime.utcnow())
    time_t = 'T'.join([time_t[:10], time_t[11:19]])
    pay_id = await_order.order_id
    product_id = _STEAM_TIDS[activity.template_id]
    comment = 'test'
    sign = sha1('1612414100'+ str(pay_id) + '5003G001T001081388505363' + product_id + '1' + comment + time_t + 'pOyNeinswa61hv').hexdigest()
    
    s = requests.post(_STEAM_GATE, data= _STEAM_REQ%(pay_id, product_id, comment, time_t, sign))
    resp = s.content
    print s.content
    if 'RspCode</name>\n<value><string>00</string>' in resp and 'Success' in resp:
        l = etree.fromstring(resp)
        steam_no = l.xpath('//string')[-3].text
        steam_product = 'Rp.' + product_id[9:]
        steam_code = l.xpath('//string')[-2].text
        charge_account = strip_phone(charge_account)
        send_sms([charge_account,], 'sms_steam', {'steam_product':steam_product, 'steam_code': steam_code})
        print 'done', await_order.order_id, charge_account, steam_code
        order_db.update_order_info(
                await_order.order_id,
                {'status': ORDER_STATUS.DEAL},
        )
        show_order(await_order)
    else:
        print 'beiju', await_order.order_id
        order_db.update_order_info(
                await_order.order_id,
                {'status': ORDER_STATUS.AWARDED}, None, True
        )
        print resp
    


def shipping_phone_charge(await_order, activity, withcarrier=False):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    #if not is_valid_user(user_id, activity):
    #    print 'found invalid user %s' % user_id
    #    _LOGGER.info('found invalid user %s %s', user_id, await_order.order_id)
    #    # update order
    #    order_db.update_order_by_id(
    #        await_order.order_id,
    #        {
    #            'status': ORDER_STATUS.DEAL,
    #            'ship_status': SHIP_STATUS.ILLEGAL,
    #            'extend': json.dumps({'illegal': 1})
    #        })
    #    # black it
    #    account_db.black_account(user_id)
    #    return
    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    # do recharge
    print 'begin recharge, %s' % await_order.order_id
    charge_account = receipt_address.get('phone')
    if not charge_account:
        return
    # check zero
    if withcarrier:
        product = CARRIER_HUAFEI_TIDS[activity.template_id]
    else:
        recharge_price = 0
        recharge_price = HUAFEI_TIDS[activity.template_id]
        carrier = _get_carrier(charge_account)
        if not carrier:
            print 'NO CARRIER', charge_account
            order_db.update_order_info(
                    await_order.order_id,
                    {'status': ORDER_STATUS.AWARDED}, None, True
            )
            return
        product = carrier + '.' + str(recharge_price)
    req = _REQ_DATA % (product, charge_account, await_order.order_id, base64.b64encode(stringxor(charge_account[-4:]+'145339', '62LF934757')))
    resp = requests.post(_DATACELL_URL, data=req)
    if '<resultcode>0</resultcode>' in resp.content or await_order.order_id==24145:
        print 'done', await_order.order_id
        order_db.update_order_info(
                await_order.order_id,
                {'status': ORDER_STATUS.DEAL}
        )
        show_order(await_order)
    else:
        print resp.content, charge_account, product
        order_db.update_order_info(
                await_order.order_id,
                {'status': ORDER_STATUS.AWARDED}, None, True
        )


def shipping(recharge_type, await_order, activity):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    if not is_valid_user(user_id, activity):
        print 'found invalid user %s' % user_id
        _LOGGER.info('found invalid user %s %s', user_id, await_order.order_id)
        # update order
        order_db.update_order_by_id(
            await_order.order_id,
            {
                'status': ORDER_STATUS.DEAL,
                'ship_status': SHIP_STATUS.ILLEGAL,
                'extend': json.dumps({'illegal': 1})
            })
        # black it
        account_db.black_account(user_id)
        return
    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    # do recharge
    print 'begin recharge, %s' % await_order.order_id
    if recharge_type == 'huafei':
        charge_account = receipt_address.get('phone')
        if not charge_account:
            return
        # check zero
        recharge_price = 0
        if activity.template_id == ZERO_TID:
            if activity.goods_id == 410:
                recharge_price = 50
            if activity.goods_id == 411:
                recharge_price = 100
            if activity.goods_id == 220:
                recharge_price = 200
        else:
            recharge_price = HUAFEI_TIDS[activity.template_id]
        success_status = ofpay.tele_charge(
            await_order.order_id, activity.template_id,
            user_id, charge_account, recharge_price)
    elif recharge_type == 'qq':
        charge_account = receipt_address.get('name')
        if charge_account == 'QQ':
            charge_account = receipt_address.get('phone')
        if not charge_account:
            return
        recharge_price = QQ_TIDS[activity.template_id]
        success_status = ofpay.qq_charge(
            await_order.order_id, activity.template_id,
            user_id, charge_account, recharge_price)
    elif recharge_type == 'zhifubao':
        charge_account = receipt_address.get('name')
        if not charge_account:
            return
        recharge_price = ZHIFUBAO_TIDS[activity.template_id]
        success_status = ofpay.ali_charge(
            await_order.order_id, activity.template_id,
            user_id, charge_account, recharge_price)
    else:
        _LOGGER.info('charge type not support')
        return
    _LOGGER.info('finish recharge %s %s for %s, success:%s',
                 recharge_type, await_order.order_id, user_id, success_status)
    if success_status == 0:
        # update order
        order_db.update_order_by_id(
            await_order.order_id,
            {
                'status': ORDER_STATUS.WAIT_SHIP,
                'ship_status': SHIP_STATUS.CHARGING,
                'extend': json.dumps({'by_juhe': 0})
            })
    elif success_status == 2:
        order = order_db.get_awarded_order(await_order.order_id)
        activity = activity_db.get_activity(order.activity_id)
        # shipping coupon
        coupon_price = HUAFEI_COUPON_TIDS.get(activity.template_id)
        if coupon_price:
            number = coupon_price / 10
            try:
                order_db.update_order_by_id(
                    await_order.order_id,
                    {
                        'status': ORDER_STATUS.WAIT_RECEIPT,
                        'ship_status': SHIP_STATUS.CHARGE_FAILED,
                        'extend': json.dumps({
                            'by_juhe': 2,
                            'express': 'coupon'
                        })
                    })
                coupon_extend = {"add_by": "auto_shipping",
                                 "order_id": await_order.order_id}
                coupon_extend = json.dumps(coupon_extend, ensure_ascii=False)
                send_coupon_to_user(order.user_id, COUPON_TID,
                                    number, extend=coupon_extend, coupon_from=u'话费充值')
                push_handler.push_shipping(
                    await_order.order_id, {'express': 'coupon'})
                return
            except Exception as e:
                _LOGGER.exception('send coupon to user exception, %s', e)
        order_db.update_order_by_id(
            await_order.order_id,
            {
                'status': ORDER_STATUS.WAIT_SHIP,
                'ship_status': SHIP_STATUS.CHARGE_FAILED,
                'extend': json.dumps({'by_juhe': 2})
            })


def get_await_list():
    items = AwardedOrder.query.filter(
        AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).all()
    return items


def get_await_coin_list():
    """
    获取以夺宝币方式收货的订单
    """
    items = AwardedOrder.query.filter(
        AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).filter(
        AwardedOrder.shipping_coin == 1).all()
    return items


def shipping_coin(await_order, activity, recharge_price=None):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    if not recharge_price:
        recharge_price = COIN_TIDS[activity.template_id]
    _LOGGER.info('begin recharge, %s, price %s', await_order.order_id, recharge_price)
    print('begin recharge, %s, price %s', await_order.order_id, recharge_price)
    try:
        # 加锁
        item = AutoShipping.query.filter(
            AutoShipping.order_id == await_order.order_id).with_lockmode(
            'update').first()
        if not item:
            item = AutoShipping()
            item.order_id = await_order.order_id
            item.template_id = activity.template_id
            item.user_id = user_id
            item.phone = 'coin'
            item.price = recharge_price
            item.status = 0
            item.shipping_type = SHIPPING_TYPE.COIN
            item.save()
            order_db.update_order_info(
                await_order.order_id,
                {
                    'status': ORDER_STATUS.DEAL,
                })
            add_system_award_transaction(
                user_id, award_amount=recharge_price, title=u'đồng xu')
            item.status = 1
            item.save()
            push_handler.push_shipping(
                await_order.order_id, {'express': 'coin'})
            # show_order(await_order)
            _LOGGER.info('finish recharge %s coin %s for %s', recharge_price, await_order.order_id, user_id)
            print('finish recharge %s coin %s for %s', recharge_price, await_order.order_id, user_id)
            return
    except Exception as e:
        _LOGGER.exception('send coin to user exception, %s-%s, %s', user_id, await_order.order_id, e)
        print('send coin to user exception, %s-%s, %s', user_id, await_order.order_id, e)


def start():
    await_orders = get_await_list()
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        if activity.template_id in COIN_TIDS:
            shipping_coin(await_order, activity)
        if activity.template_id in HUAFEI_TIDS:
            print 'check order, %s %s' % (await_order.order_id, activity.template_id)
            shipping_phone_charge(await_order, activity)
        if activity.template_id in CARRIER_HUAFEI_TIDS:
            print 'check order, %s %s' % (await_order.order_id, activity.template_id)
            shipping_phone_charge(await_order, activity, withcarrier=True)


def start_ex():
    await_orders = get_await_coin_list()
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        print 'check coin order, %s %s' % (await_order.order_id, activity.template_id)
        goods_price = float(get_goods(activity.goods_id).price)
        shipping_coin(await_order, activity, recharge_price=goods_price)

def start_steam():
    await_orders = get_await_list()
    print 'steam'
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        if activity.template_id in _STEAM_TIDS:
            print 'check steam order, %s %s' % (await_order.order_id, activity.template_id)
            shipping_steam(await_order, activity)




if __name__ == "__main__":
    start()
    start_steam()
    #start_ex()
