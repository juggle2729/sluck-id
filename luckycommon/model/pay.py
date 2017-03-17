# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.custom_enum import CustomEnum


class PayType(CustomEnum):
    NGANLUONG = 1
    FORTUMO_PAY = 2
    PAYPAL_EC = 3
    PRE_CARD_NG = 4
    CODA_PAY = 5
    DOKU_WALLET = 6
    PAYSSION = 7
    EWALLET = 8
    SMS = 9
    CARRIER_BILLING = 10
    TELCO_VOUCHER = 11
    CONVENNIENCE_STORE = 12
    ATM = 13
    ONLINE_BANK = 14
    MOGPLAY = 15
    GAME_ON = 16
    MANDIRI_ECASH = 17
    MIMO_BCA = 18
    CODA_SMS = 19
    GOOGLE_BILLING = 20
    APPLE_IAP = 21
    DOKU_VISA = 22


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
        'icon': '',
        'tag': '',
    },
    PayType.CODA_PAY.value: {
        'name': u'Coda Pay',
        'pay_type': PayType.CODA_PAY.value,
        'comment': u'',
        'highlight': 0,
        'choice': [1, 5, 10, 50, 100, 200, 500],
        'icon': '',
        'tag': '',
    },
    PayType.DOKU_WALLET.value: {
        'name': u'Doku',
        'pay_type': PayType.DOKU_WALLET.value,
        'comment': u'Doku',
        'highlight': 0,
        'choice': [10, 50, 100, 200, 500, 1000],
        'icon': '',
        'tag': '',
    },
    PayType.DOKU_VISA.value: {
        'name': u'Doku Visa',
        'pay_type': PayType.DOKU_VISA.value,
        'comment': u'Doku Visa',
        'highlight': 0,
        'choice': [10, 50, 100, 200, 500, 1000],
        'icon': '',
        'tag': '',
    },
    PayType.PAYSSION.value: {
        'name': u'Payssion',
        'pay_type': PayType.PAYSSION.value,
        'comment': u'PAYSSION ',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
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
    PayType.SMS.value: {
        'name': u'sms',
        'pay_type': PayType.SMS.value,
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
    PayType.CONVENNIENCE_STORE.value: {
        'name': u'Convenience Store',
        'pay_type': PayType.CONVENNIENCE_STORE.value,
        'comment': u'Convenience Store',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': '',
        'tag': '',
    },
    PayType.ATM.value: {
        'name': u'Bank Transfer',
        'pay_type': PayType.ATM.value,
        'comment': u'Bank Transfer',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': '',
        'tag': '',
    },
    PayType.MANDIRI_ECASH.value: {
        'name': u'Bank Transfer',
        'pay_type': PayType.MANDIRI_ECASH.value,
        'comment': u'Bank Transfer',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200, 500],
        'icon': '',
        'tag': '',
    },
    PayType.MOGPLAY.value: {
        'name': u'mogplay',
        'pay_type': PayType.MOGPLAY.value,
        'comment': u'Mogplay',
        'highlight': 0,
        'choice': [],
        'icon': '',
        'tag': '',
    },
    PayType.GAME_ON.value: {
        'name': u'game on',
        'pay_type': PayType.GAME_ON.value,
        'comment': u'Game On',
        'highlight': 0,
        'choice': [],
        'icon': '',
        'tag': '',
    },
    PayType.CODA_SMS.value: {
        'name': u'coda sms',
        'pay_type': PayType.CODA_SMS.value,
        'comment': u'coda sms',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
        'tag': '',
    },
    PayType.MIMO_BCA.value: {
        'name': u'MIMO BCA',
        'pay_type': PayType.MIMO_BCA.value,
        'comment': u'MIMO BCA',
        'highlight': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
        'tag': '',
    },
    PayType.GOOGLE_BILLING.value: {
        'name': u'Google Billing',
        'pay_type': PayType.GOOGLE_BILLING.value,
        'comment': u'GOOGLE BILLING',
        'highlight': 0,
        'choice': [10, 20, 50, 100, 200],
        'icon': '',
        'tag': '',
    },
    PayType.APPLE_IAP.value: {
        'name': u'Apple IAP',
        'pay_type': PayType.APPLE_IAP.value,
        'comment': u'Apple IAP',
        'highliht': 0,
        'choice': [50, 100, 200, 500, 1000, 2000, 5000],
        'icon': '',
        'tag': '',
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
