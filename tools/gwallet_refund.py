# -*- coding: utf-8 -*-
from __future__ import absolute_import

from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
import time
from datetime import datetime
import sys
import os

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.cache.redis_cache import get_gwallet_purchase_token, get_gwallet_refund_endtime, \
    set_gwallet_refund_endtime
from luckycommon.account.db.account import black_account
from luckycommon.db.pay import get_pay


KEY_JSON_FILE = 'tools/secret.json'
GOOGLE_SCOPES_URL = ['https://www.googleapis.com/auth/androidpublisher',]
PACKAGE_NAME = 'com.idyyg.tokohemat'


def _get_format_datetime(timestamp=None):
    if timestamp:
        timestamp = timestamp / 1000.0
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_start_time():
    end_time = get_gwallet_refund_endtime()
    if end_time == None:
        end_time = time.time() * 1000  - 3600 * 72 * 1000
        end_time = int(end_time)
    return str(end_time)


def get_next_pagetoken(result):
    if result.has_key('tokenPagination'):
        tokenPagination = result['tokenPagination']
        if tokenPagination.has_key('nextPageToken'):
            return tokenPagination['nextPageToken']
    return None

def get_voidedpurchases():
    credential = ServiceAccountCredentials.from_json_keyfile_name(KEY_JSON_FILE, scopes=GOOGLE_SCOPES_URL)
    s = build('androidpublisher', 'v2', http= credential.authorize(Http()))
    purchases = s.purchases()
    voidedpurchases = purchases.voidedpurchases()
    start_time = get_start_time()
    start_time = long(start_time)
    print _get_format_datetime(),'Start time is: {0} ms'.format(start_time)
    voidedpurchases_list = []
    result = voidedpurchases.list(packageName=PACKAGE_NAME, maxResults=100, startTime=start_time).execute()
    while True:
        if result.has_key('voidedPurchases'):
            for p in result['voidedPurchases']:
                voidedpurchases_list.append(p)
        next_pagetoken =  get_next_pagetoken(result)
        if next_pagetoken == None:
            break
        result = voidedpurchases.list(packageName=PACKAGE_NAME, maxResults=100,
                                      startTime=start_time, token=next_pagetoken).execute()
    return voidedpurchases_list




def black_account_by_purchase():
    voided_time_set = set()
    r = get_voidedpurchases()
    print _get_format_datetime(), 'voidedpurchases list: {0}'.format(r)
    for info in r:
        print info
        purchase_token = info.get('purchaseToken')
        voided_time_millis = info.get('voidedTimeMillis')
        purchase_time_millis = info.get('purchaseTimeMillis')
        voided_time_set.add(int(voided_time_millis))
        value = get_gwallet_purchase_token(purchase_token)
        print _get_format_datetime(),"Get gwallet purchase info in redis: {0}".format(value)
        if len(value) != 0:
            userid = value['user_id']
            orderid = value['order_id']
            payid = value.get('pay_id', 0)
            if not payid:
                pay_price = None
                pay_charge_time = None
            else:
                pay = get_pay(payid)
                pay_price = pay.price
                pay_charge_time =  pay.updated_at
            black_reason = 'black account by gwallet refund, order id is {0}, ' \
                           'voided time is {1}, ' \
                           'black time is {2}'.format(
                orderid, _get_format_datetime(voided_time_millis), _get_format_datetime())
            black_account(userid, black_reason)
            print _get_format_datetime(), 'black account info: {0}, ' \
                                          'userid: {1}, orderid: {2}' \
                                          'payid: {3}, price: {4}, chargetime: {5}' \
                                          'purchase time: {6}, refund time: {7}.'.format(
                purchase_token, userid, orderid, payid, pay_price, pay_charge_time,
                _get_format_datetime(purchase_time_millis), _get_format_datetime(voided_time_millis))
        else:
            print _get_format_datetime(),"Can't find user info, purchase token info: {0}".format(purchase_token)
    if len(voided_time_set) != 0:
        next_start_time = max(voided_time_set)
        set_gwallet_refund_endtime(next_start_time)


if __name__ == "__main__":
    black_account_by_purchase()