# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.custom_enum import CustomEnum


class PayType(CustomEnum):
    NGANLUONG = 1
    FORTUMO_PAY = 2
    PAYPAL_EC = 3  # point
    PRE_CARD_NG = 4
    CODA_PAY = 5
    DOKU_WALLET = 6  # point
    PAYSSION = 7
    EWALLET = 8
    BLUEPAY_SDK_SMS = 9
    CARRIER_BILLING = 10
    TELCO_VOUCHER = 11
    BLUEPAY_SDK_CONVENNIENCE_STORE = 12
    BLUEPAY_SDK_ATM = 13
    ONLINE_BANK = 14
    BLUEPAY_SDK_MOGPLAY = 15
    BLUEPAY_SDK_GAME_ON = 16
    MANDIRI_ECASH = 17
    MIMO_BCA = 18
    CODA_SMS = 19
    GOOGLE_BILLING = 20
    APPLE_IAP = 21
    DOKU_VISA = 22  # point
    MIMO_TELKOMSEL = 23  # point
    BLUEPAY_SMS = 24
    HUAWEI_EPAY = 25
    SELF_RECHARGE_CARD = 26
    MIMO_INDOSAT = 27
    MIMO_THREE = 28
    MIMO_XL = 29


class PayStatus(CustomEnum):
    WAIT = 0
    SUBMIT = 1
    DONE = 2
    FAIL = 4
    CANCEL = 8


AVAILABLE_PAY_TYPES = {
    PayType.PAYPAL_EC.value: {
        'name': u'Paypal express checkout',
        'pay_type': PayType.PAYPAL_EC.value,
        'comment': u'',
        'highlight': 0,
        'choice': [200, 500, 1000, 2000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_3.png',
        'tag': 'http://p.1yuan-gou.com/ic_pay_10x.png',
    },
    PayType.CODA_PAY.value: {
        'name': u'Coda Pay',
        'pay_type': PayType.CODA_PAY.value,
        'comment': u'',
        'highlight': 0,
        'choice': [10, 50, 100, 200],
        'icon': 'http://p.1yuan-gou.com/codapay_sms.png',
        'tag': '',
    },
    PayType.DOKU_WALLET.value: {
        'name': u'Doku',
        'pay_type': PayType.DOKU_WALLET.value,
        'comment': u'Doku',
        'highlight': 0,
        'choice': [10, 50, 100, 200, 500, 1000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_6.png',
        'tag': 'http://p.1yuan-gou.com/ic_pay_10x.png',
    },
    PayType.DOKU_VISA.value: {
        'name': u'Doku Visa',
        'pay_type': PayType.DOKU_VISA.value,
        'comment': u'Doku Visa',
        'highlight': 0,
        'choice': [10, 50, 100, 200, 500, 1000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_22.png',
        'tag': 'http://p.1yuan-gou.com/ic_pay_10x.png',
    },
    PayType.PAYSSION.value: {
        'name': u'Payssion',
        'pay_type': PayType.PAYSSION.value,
        'comment': u'PAYSSION ',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_7.png',
        'tag': '',
    },
    PayType.EWALLET.value: {
        'name': u'E-Wallet',
        'pay_type': PayType.EWALLET.value,
        'comment': u'E-Wallet',
        'open_type': u'',
        'providers': [
            {'name': u'doku', 'type': 3},
            {'name': u'mandiri', 'type': 4},
        ],
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
        'tag': '',
    },
    PayType.BLUEPAY_SDK_SMS.value: {
        'name': u'sms',
        'pay_type': PayType.BLUEPAY_SDK_SMS.value,
        'comment': u'sms test',
        'highlight': 0,
        'choice': [5, 10, 20, 25, 50, 100, 200],
        'icon': '',
        'tag': '',
    },
    PayType.CARRIER_BILLING.value: {
        'name': u'Phone Billing',
        'pay_type': PayType.CARRIER_BILLING.value,
        'comment': u'cb ',
        'open_type': u'',
        'providers': [
            {'name': u'telpomsel', 'type': 6},
            {'name': u'indosat', 'type': 7},
            {'name': u'xl', 'type': 8},
            {'name': u'h3i', 'type': 9},
            {'name': u'bolt', 'type': 10},
        ],
        'highlight': 0,
        'choice': [5, 10, 20, 25, 50, 100, 200],
        'icon': '',
        'tag': '',
    },
    PayType.TELCO_VOUCHER.value: {
        'name': u'Vouchers',
        'pay_type': PayType.TELCO_VOUCHER.value,
        'comment': u'Vouchers',
        'open_type': u'',
        'providers': [
            {'name': u'telpomsel', 'type': 16},
            {'name': u'sevelin', 'type': 11},
            {'name': u'smartfren', 'type': 12},
        ],
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
        'tag': '',
    },
    PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value: {
        'name': u'Convenience Store',
        'pay_type': PayType.BLUEPAY_SDK_CONVENNIENCE_STORE.value,
        'comment': u'Convenience Store',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': 'http://p.1yuan-gou.com/ic_pay_12.png',
        'tag': '',
    },
    PayType.BLUEPAY_SDK_ATM.value: {
        'name': u'Bank Transfer',
        'pay_type': PayType.BLUEPAY_SDK_ATM.value,
        'comment': u'Bank Transfer',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': 'http://p.1yuan-gou.com/ic_pay_13.png',
        'tag': '',
    },
    PayType.MANDIRI_ECASH.value: {
        'name': u'Bank Transfer',
        'pay_type': PayType.MANDIRI_ECASH.value,
        'comment': u'Bank Transfer',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': 'http://p.1yuan-gou.com/ic_pay_17.png',
        'tag': '',
    },
    PayType.BLUEPAY_SDK_MOGPLAY.value: {
        'name': u'mogplay',
        'pay_type': PayType.BLUEPAY_SDK_MOGPLAY.value,
        'comment': u'Mogplay',
        'highlight': 0,
        'choice': [],
        'icon': 'http://p.1yuan-gou.com/ic_pay_15.png',
        'tag': 'http://p.1yuan-gou.com/ic_pay_10x.png',
    },
    PayType.BLUEPAY_SDK_GAME_ON.value: {
        'name': u'game on',
        'pay_type': PayType.BLUEPAY_SDK_GAME_ON.value,
        'comment': u'Game On',
        'highlight': 0,
        'choice': [],
        'icon': 'http://p.1yuan-gou.com/ic_pay_16.png',
        'tag': 'http://p.1yuan-gou.com/ic_pay_10x.png',
    },
    PayType.CODA_SMS.value: {
        'name': u'coda sms',
        'pay_type': PayType.CODA_SMS.value,
        'comment': u'coda sms',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': 'http://p.1yuan-gou.com/codapay_sms.png',
        'tag': '',
    },
    PayType.MIMO_BCA.value: {
        'name': u'MIMO BCA',
        'pay_type': PayType.MIMO_BCA.value,
        'comment': u'MIMO BCA',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_18.png',
        'tag': '',
    },
    PayType.GOOGLE_BILLING.value: {
        'name': u'Google Billing',
        'pay_type': PayType.GOOGLE_BILLING.value,
        'comment': u'GOOGLE BILLING',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200],
        'icon': 'http://p.1yuan-gou.com/ic_pay_20.png',
        'tag': '',
    },
    PayType.APPLE_IAP.value: {
        'name': u'Apple IAP',
        'pay_type': PayType.APPLE_IAP.value,
        'comment': u'Apple IAP',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': 'http://p.1yuan-gou.com/ic_pay_21.png',
        'tag': '',
    },
    PayType.MIMO_TELKOMSEL.value: {
        'name': u'MIMO TELKOMSEL',
        'pay_type': PayType.MIMO_TELKOMSEL.value,
        'comment': u'MIMO TELKOMSEL',
        'highlight': 0,
        'choice': [10, 50],
        'icon': 'http://p.1yuan-gou.com/ic_tsel_new.png',
        'tag': '',
    },
    PayType.MIMO_INDOSAT.value: {
        'name': u'MIMO INDOSAT',
        'pay_type': PayType.MIMO_INDOSAT.value,
        'comment': u'MIMO INDOSAT',
        'highlight': 0,
        'choice': [10, 20, 50, 100],
        'icon': 'http://p.1yuan-gou.com/indosat.png',
        'tag': '',
    },
    PayType.MIMO_THREE.value: {
        'name': u'MIMO THREE',
        'pay_type': PayType.MIMO_THREE.value,
        'comment': u'MIMO THREE',
        'highlight': 0,
        'choice': [10, 20, 50, 100],
        'icon': 'http://p.1yuan-gou.com/three.png',
        'tag': '',
    },
    PayType.MIMO_XL.value: {
        'name': u'MIMO XL',
        'pay_type': PayType.MIMO_XL.value,
        'comment': u'MIMO XL',
        'highlight': 0,
        'choice': [10, 20, 50, 100],
        'icon': 'http://p.1yuan-gou.com/xl.png',
        'tag': '',
    },
    PayType.BLUEPAY_SMS.value: {
        'name': u'Bluepay sms',
        'pay_type': PayType.BLUEPAY_SMS.value,
        'comment': u'Bluepay',
        'highlight': 0,
        'choice': [5, 10, 50, 100, 200, 500],
        'icon': 'http://p.1yuan-gou.com/bluepay_sms.png',
        'tag': '',
    },
    PayType.HUAWEI_EPAY.value: {
        'name': u'Huaweipay',
        'pay_type': PayType.HUAWEI_EPAY.value,
        'comment': u'Huaweiepay',
        'highlight': 0,
        'choice': [1, 5, 10, 50, 100, 200, 500],
        'icon': 'http://p.1yuan-gou.com/huaweipay.png',
        'tag': '',
    },
    PayType.SELF_RECHARGE_CARD.value: {
        'name': u'Recharge Card',
        'pay_type': PayType.SELF_RECHARGE_CARD.value,
        'comment': u'recharge card',
        'highlight': 0,
        'choice': [],
        'icon': 'http://p.1yuan-gou.com/ic_tokopay.png',
        'tag': 'http://p.1yuan-gou.com/ic_50x.png',
        'agents': [
            {
                'name': 'Bank Transfer',
                'phone': 'Line: anggiaulima\nLine: mawanara',
            },
        ],
    },
}


class Pay(orm.Model):
    __tablename__ = "pay"
    id = orm.Column(orm.BigInteger, primary_key=True, autoincrement=False)
    user_id = orm.Column(orm.BigInteger)
    pay_type = orm.Column(orm.Integer)  # 支付类型
    status = orm.Column(orm.Integer)  # 交易是否完成，默认为0
    price = orm.Column(orm.FLOAT)  # 金额
    activity_id = orm.Column(orm.VARCHAR)  # 为购买活动而充值
    quantity = orm.Column(orm.Integer)
    # JSON， {'activity_id': xxx, 'quantity': 10}，关联购买信息
    extend = orm.Column(orm.TEXT)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
