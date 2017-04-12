# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime
from hashlib import md5
from hashlib import sha1
from random import randint

import requests
from lxml import etree

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

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
from luckycommon.db.activity import get_activity
from luckycommon.db.transaction import add_system_award_transaction
from luckycommon.account.db.account import get_account_status

_LOGGER = logging.getLogger('lucky')


def strip_phone(phone_number):
    phone_number = str(phone_number)
    prefix_list = ['62', '0', '620', '062']
    for prefix in prefix_list:
        phone_number = remove_prefix(phone_number, prefix)
    return phone_number


_PULSA_XML = """<?xml version='1.0' encoding='utf-8'?>
<mp><commands>topup</commands> <username>tokoseribu</username><ref_id>%s</ref_id><hp>%s</hp><pulsa_code>%s</pulsa_code><sign>%s</sign>
</mp>"""

_PULSA_CS_XML = '''<?xml version='1.0' encoding='utf-8'?>
<mp>
<commands>checkstatus</commands>
<username>tokoseribu</username>
<ref_id>%s</ref_id>
<sign>7382ec53a55aea38e052799fa2178fe0</sign>
</mp>'''

_PULSA_URL = 'http://mobilepulsa.com/api/receiver/index.php'

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
COIN_TIDS = {
    802: 100,
    856: 500,
    860: 20,
}
_PULSA_TIDS = {  # 话费 tids
    792: 5000,
    666: 10000,
    793: 25000,
    667: 50000,
    668: 100000,
    794: 500000,
    796: 1000000,
}
_PULSA_ELE_TIDS = {  # 电费
    838: 20000,
    839: 50000,
    840: 100000,
    841: 200000,
    842: 500000,
    843: 1000000,
}

CARRIER_HUAFEI_TIDS = {
    728: 'TEL.5',
    738: 'TEL.10',
    737: 'TEL.20',
    736: 'TEL.25',
    735: 'TEL.50',
    734: 'TEL.100',
    726: 'XL.5',
    749: 'XL.10',
    748: 'XL.15',
    747: 'XL.25',
    746: 'XL.50',
    745: 'XL.100',
    725: 'SF.5',
    756: 'SF.10',
    755: 'SF.20',
    754: 'SF.25',
    753: 'SF.30',
    752: 'SF.50',
    751: 'SF.60',
    750: 'SF.100',
    724: 'TRI.1',
    762: 'TRI.5',
    761: 'TRI.10',
    760: 'TRI.20',
    759: 'TRI.30',
    758: 'TRI.50',
    757: 'TRI.100',
    727: 'IR.5',
    744: 'IR.10',
    743: 'IR.20',
    742: 'IR.25',
    741: 'IR.30',
    740: 'IR.50',
    739: 'IR.100',
}

_STEAM_TIDS = {
    694: 'steam idr12000',
    695: 'steam idr45000',
    661: 'steam idr60000',
    662: 'steam idr90000',
    663: 'steam idr120000',
    664: 'steam idr250000',
    665: 'steam idr400000',
    696: 'steam idr600000',
    779: 'garena v10',
    778: 'garena v20',
    777: 'garena v50',
    776: 'garena v100',
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

_PULSACODE_FOR_CARRIER = {
    'TEL': 'htelkomsel',
    'IR': 'hindosat',
    'XL': 'xld',
    'TRI': 'hthree',
    'SF': 'hsmart',
}


def stringxor(str1, str2):
    orxstr = ""
    for i in range(0, len(str1)):
        rst = ord(list(str1)[i]) ^ ord(list(str2)[i])
        orxstr = orxstr + chr(rst)
    return orxstr


def _get_carrier(phone):
    prefix = phone[:4]
    if prefix not in _CARRIER_PREFIX:
        return None
    else:
        return _CARRIER_PREFIX[prefix]


def _delay_delivery(order_id, user_id, delay_hour):
    gp_timestamp = redis_cache.get_gp_delivery_timestamp(user_id)
    if not gp_timestamp:
        return False
    delay_timestamp = redis_cache.get_delay_timestamp(order_id)
    if not delay_timestamp:
        # gwallet 充值用户
        timestamp = int(time.time()) + 3600 * int(
            delay_hour)  # 28 Fed. 2017  Delay delivery 48 hours
        redis_cache.set_delay_timestamp(order_id, timestamp)
        print 'set order id: %s delay deliver timestamp: %s' % (order_id,
                                                                timestamp)
        return True
    else:
        if int(delay_timestamp) >= int(time.time()):  # 未到发货时间
            print 'order id: %s delay deliver timestamp: %s >= current timestamp' % (
                order_id, delay_timestamp)
            return True
        return False


def shipping_steam(await_order, activity):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    if _delay_delivery(await_order.order_id, user_id, 72):
        return
    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    # do recharge
    print 'begin shipping steam order, %s' % await_order.order_id
    charge_account = receipt_address.get('phone')
    if not charge_account:
        return
    time_t = str(datetime.utcnow())
    time_t = 'T'.join([time_t[:10], time_t[11:19]])
    pay_id = await_order.order_id
    product_id = _STEAM_TIDS[activity.template_id]
    comment = 'test'
    sign = sha1('1612414100' + str(
        pay_id) + '5003G001T001081388505363' + product_id + '1' + comment +
                time_t + 'pOyNeinswa61hv').hexdigest()

    s = requests.post(
        _STEAM_GATE,
        data=_STEAM_REQ % (pay_id, product_id, comment, time_t, sign))
    resp = s.content
    print 'got response from steam: %s' % resp
    if (
            'RspCode</name>\n<value><string>00</string>' in resp or 'RspCode</name>\n<value><string>000</string>') in resp and 'Success' in resp:
        l = etree.fromstring(resp)
        steam_no = l.xpath('//string')[-3].text
        steam_product = 'Rp.' + product_id[9:]
        steam_code = l.xpath('//string')[-2].text
        charge_account = strip_phone(charge_account)
        send_sms([
            charge_account,
        ], 'sms_steam',
            {'steam_product': steam_product,
             'steam_code': steam_code})
        print 'ship steam order done, order_id: %s, user_id: %s, steam_code: %s' % (await_order.order_id, charge_account, steam_code)
        order_db.update_order_info(
            await_order.order_id,
            {'status': ORDER_STATUS.DEAL, 'remark': steam_code}, )
        show_order(await_order)
    else:
        print 'steam response invalid. order_id: %s, resp: %s' % (await_order.order_id, resp)
        order_db.update_order_info(
            await_order.order_id, {'status': ORDER_STATUS.AWARDED}, None, True)
        print resp


def shipping_phone_charge(await_order, activity, withcarrier=False):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    if _delay_delivery(await_order.order_id, user_id, 72):
        return
    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    phone = receipt_address.get('phone')
    print 'shipping phone charge order, order_id: %s, phone: %s' % (await_order.order_id, phone)
    if not phone:
        return
    product = CARRIER_HUAFEI_TIDS[activity.template_id]
    check_status = redis_cache.exists_15phone(phone)
    if check_status:
        print phone, ' already charged 15 mins before, just wait'
        return
    req = _REQ_DATA % (
        product, phone, await_order.order_id, base64.b64encode(
            stringxor(phone[-4:] + '145339', '62LF934757')))
    resp = requests.post(_DATACELL_URL, data=req)
    if '<resultcode>0</resultcode>' in resp.content:
        print 'shipping phone charge order done. order_id: %s' % await_order.order_id
        order_db.update_order_info(await_order.order_id,
                                   {'status': ORDER_STATUS.DEAL})
        show_order(await_order)
        redis_cache.set_15phone(phone)
    else:
        print resp.content, phone, product
        order_db.update_order_info(
            await_order.order_id, {'status': ORDER_STATUS.AWARDED}, None, True)


def shipping_pulsa(await_order, activity):
    user_id = await_order.user_id
    if redis_cache.is_virtual_account(user_id):
        return
    if _delay_delivery(await_order.order_id, user_id, 72):
        return

    receipt_address = {} if not await_order.receipt_address else json.loads(
        await_order.receipt_address)
    # do recharge
    phone = receipt_address.get('phone')
    name = receipt_address.get('name')
    print 'shipping pulsa order, order_id: %s, phone: %s' % (await_order.order_id, phone)
    if not phone:
        return
    recharge_price = _PULSA_TIDS[activity.template_id]
    carrier = _get_carrier(phone)
    if not carrier:
        print 'NO CARRIER', phone
        order_db.update_order_info(
            await_order.order_id, {'status': ORDER_STATUS.AWARDED}, None, True)
        return
    product_prefix = _PULSACODE_FOR_CARRIER[carrier]
    product = product_prefix + str(recharge_price)
    if carrier in ('TRI', 'IR', 'SF'):
        check_status = redis_cache.exists_phone_limit(phone)
        if check_status:
            print phone, ' already charged some mins before, just wait'
            return
    seed = str(randint(100, 99999))
    req = _PULSA_XML % (str(await_order.order_id) + '#' + seed, phone,
                        product, md5('tokoseributokoseribu123*' + str(
        await_order.order_id) + '#' + seed).hexdigest())
    headers = {
        'Content-Type': 'application/xml'
    }  # set what your server accepts
    if get_account_status(await_order.user_id):
        print '[{0}] limit the delivery, account status is banned, ' \
              'user id: {1}, order id: {2}, product id: {3}, phone: {4}, name: {5} ' \
              'activity id: {6}, tid: {7}, term number: {8}, activity price: {9}'.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id, await_order.order_id, product, phone, name,
            activity.id, activity.template_id, activity.term_number, activity.price)
        order_db.update_order_info(await_order.order_id,
                                   {'status': ORDER_STATUS.DEAL})
        return
    resp = requests.post(_PULSA_URL, data=req, headers=headers)
    print 'got pulsa response. order_id: %s, resp: %s' % (await_order.order_id, resp.content)
    if '<status>0</status>' in resp.content:
        print 'shipping pulsa done. order_id: %s' % await_order.order_id
        order_db.update_order_info(await_order.order_id,
                                   {'status': ORDER_STATUS.DEAL})
        show_order(await_order)
        if carrier in ('TRI', 'IR', 'SF'):
            redis_cache.set_phone_limit(phone, carrier)
    else:
        print 'shipping pulsa failed. resp: %s, phone: %s, product: %s' % (resp.content, phone, product)
        order_db.update_order_info(
            await_order.order_id, {'status': ORDER_STATUS.AWARDED}, None, True)


def get_await_list():
    items = AwardedOrder.query.filter(
        AwardedOrder.status == ORDER_STATUS.WAIT_SHIP).all()
    return items


def get_await_coin_list():
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
    print('shipping coin order, order_id: %s, amount: %s' % (await_order.order_id, recharge_price))
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
            order_db.update_order_info(await_order.order_id, {
                'status': ORDER_STATUS.DEAL,
            })
            add_system_award_transaction(
                user_id, award_amount=recharge_price, title=u'đồng xu')
            item.status = 1
            item.save()
            push_handler.push_shipping(await_order.order_id,
                                       {'express': 'coin'})
            print('finish recharge %s coin %s for %s', recharge_price,
                  await_order.order_id, user_id)
            return
    except Exception as e:
        print('send coin to user exception, %s-%s, %s', user_id,
              await_order.order_id, e)


def start():
    await_orders = get_await_list()
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        if not activity:
            continue
        if activity.template_id in COIN_TIDS:
            shipping_coin(await_order, activity)
        if activity.template_id in CARRIER_HUAFEI_TIDS:
            print 'check carrier huafei order, order_id: %s, template_id: %s' % (await_order.order_id, activity.template_id)
            shipping_phone_charge(await_order, activity, withcarrier=True)


def start_steam():
    await_orders = get_await_list()
    print 'steam'
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        if not activity:
            continue
        if activity.template_id in _STEAM_TIDS:
            print 'check steam order, %s %s' % (await_order.order_id, activity.template_id)
            shipping_steam(await_order, activity)


def start_pulsa():
    await_orders = get_await_list()
    for await_order in await_orders:
        activity_id = await_order.activity_id
        activity = get_activity(activity_id)
        if not activity:
            continue
        if activity.template_id in _PULSA_TIDS:
            print 'check pulsa order, %s %s' % (await_order.order_id, activity.template_id)
            shipping_pulsa(await_order, activity)


if __name__ == "__main__":
    start()
    start_steam()
    start_pulsa()
