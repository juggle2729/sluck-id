# -*- coding: utf-8 -*-
from __future__ import absolute_import

from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build

from luckycommon.cache.redis_cache import get_gwllet_purchase_token
from luckycommon.account.db.account import black_account


KEY_JSON_FILE=''
GOOGLE_SCOPES_URL=['https://www.googleapis.com/auth/androidpublisher',]
PACKAGE_NAME='com.idyyg.tokohemat'



def get_voidedpurchases():
    credential = ServiceAccountCredentials.from_json_keyfile_name(KEY_JSON_FILE, scopes=GOOGLE_SCOPES_URL)
    s = build('androidpublisher', 'v2', http= credential.authorize(Http()))
    purchases = s.purchases()
    voidedpurchases = purchases.voidedpurchases()
    voidedpurchases_list = voidedpurchases.list(packageName=PACKAGE_NAME, maxResults=100).execute()
    print voidedpurchases_list
    return voidedpurchases_list.get('voidedPurchases')



def black_account_by_purchase():
    p = get_voidedpurchases()
    for info in p:
        purchase_token = info.get['purchaseToken']
        voided_time_millis = info.get['voidedTimeMillis']
        value = get_gwllet_purchase_token(purchase_token)
        if value != None:
            userid = value['user_id']
            orderid = value['order_id']
            black_reason = 'black account by gwallet refund, order id is {0}, voided time is {1}'.format(orderid, voided_time_millis)
            black_account(userid, black_reason)
            print 'black account info: {0} ,userid: {1}, orderid: {2}'.format(purchase_token, userid, orderid)
        else:
            print "Can't find user info, purchase token info: {0}".format(purchase_token)













