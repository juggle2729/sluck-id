# -*- coding: utf-8 -*-
from __future__ import absolute_import

from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
import time

from luckycommon.cache.redis_cache import get_gwllet_purchase_token, get_gwallet_refund_endtime, \
    set_gwallet_refund_endtime
from luckycommon.account.db.account import black_account


KEY_JSON_FILE = 'tools/secret.json'
GOOGLE_SCOPES_URL = ['https://www.googleapis.com/auth/androidpublisher',]
PACKAGE_NAME = 'com.idyyg.tokohemat'


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
    voidedpurchases_list = []
    result = voidedpurchases.list(packageName=PACKAGE_NAME, maxResults=100, startTime=start_time).execute()
    while True:
        if result.has_key('voidedPurchases'):
            voidedpurchases_list += result['voidedPurchases']
        next_pagetoken =  get_next_pagetoken(result)
        if next_pagetoken == None:
            break
        result = voidedpurchases.list(packageName=PACKAGE_NAME, maxResults=100,
                                      startTime=start_time, token=next_pagetoken).execute()
    return voidedpurchases_list




def black_account_by_purchase():
    voided_time_set = set()
    r = get_voidedpurchases()
    for p in r:
        for info in p:
            purchase_token = info.get['purchaseToken']
            voided_time_millis = info.get['voidedTimeMillis']
            voided_time_set.add(int(voided_time_millis))
            value = get_gwllet_purchase_token(purchase_token)
            if value != None:
                userid = value['user_id']
                orderid = value['order_id']
                black_reason = 'black account by gwallet refund, order id is {0}, voided time is {1}'.format(orderid, voided_time_millis)
                black_account(userid, black_reason)
                print 'black account info: {0} ,userid: {1}, orderid: {2}'.format(purchase_token, userid, orderid)
            else:
                print "Can't find user info, purchase token info: {0}".format(purchase_token)
    next_start_time = max(voided_time_set)
    set_gwallet_refund_endtime(next_start_time)


if __name__ == "__main__":
    black_account_by_purchase()