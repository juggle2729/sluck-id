# -*- coding: utf-8 -*-
from datetime import datetime

from luckycommon.utils.decorator import sql_wrapper
from luckycommon.model.iap_receipt import IAPReceipt, IAPInvalidReceipt
from luckycommon.model import orm

@sql_wrapper
def get_receipt_by_transaction_id(transaction_id):
    return IAPReceipt.query.filter(IAPReceipt.id == transaction_id).first()

@sql_wrapper
def get_invalid_receipt_by_hash_text(text):
    return IAPInvalidReceipt.query.filter(IAPInvalidReceipt.id == text).first()



STATUS_CODE_DESCRIPTION= {
    # App Store status code
    '21000': 'The App Store could not read the JSON object you provided.',
    '21002': 'The data in the receipt-data property was malformed or missing.',
    '21003': 'The receipt could not be authenticated.',
    '21004': '''The shared secret you provided does not match the shared secret on file for your account.
Only returned for iOS 6 style transaction receipts for auto-renewable subscriptions.''',
    '21005': 'The receipt server is not currently available.',
    '21006': '''This receipt is valid but the subscription has expired. When this status code
is returned to your server, the receipt data is also decoded and returned as
part of the response. Only returned for iOS 6 style transaction receipts for
auto-renewable subscriptions.''',
    '21007': '''This receipt is from the test environment, but it was sent to the production
environment for verification. Send it to the test environment instead.''',
    '21008': '''This receipt is from the production environment, but it was sent to the test
environment for verification. Send it to the production environment instead.''',
    # Custom status code
    '30000': 'bundle id not match.',
    '30001': 'production id not match',
}


@sql_wrapper
def save_receipt(user_id, pay_id,receipt_data, result_info):
    iap_receipt = IAPReceipt()
    in_app = result_info['receipt']['in_app'][0]
    transaction_id = in_app['transaction_id']
    product_id = in_app['product_id']
    env = result_info.get("environment", "production")
    iap_receipt.id = transaction_id
    iap_receipt.user_id = user_id
    iap_receipt.pay_id = pay_id
    iap_receipt.receipt = receipt_data
    iap_receipt.receipt_info = str(result_info)
    iap_receipt.product_id = product_id
    iap_receipt.environment = env
    iap_receipt.provide_status = 0
    iap_receipt.updated_at = datetime.utcnow()
    iap_receipt.save()


@sql_wrapper
def save_invalid_receipt(hash_text, receipt_data, status_code):
    iap_invalid_receipt = IAPInvalidReceipt()
    iap_invalid_receipt.id = hash_text
    iap_invalid_receipt.receipt = receipt_data
    iap_invalid_receipt.status = status_code
    iap_invalid_receipt.extend = STATUS_CODE_DESCRIPTION.get(str(status_code), 'Other reasons')
    iap_invalid_receipt.updated_at = datetime.utcnow()
    iap_invalid_receipt.save()


@sql_wrapper
def update_receipt_provide_success(transaction_id):
    res = IAPReceipt.query.filter(IAPReceipt.id == transaction_id).filter(IAPReceipt.provide_status == 0).update(
        {
            'provide_status': 1,
            'updated_at': datetime.utcnow()
        }
    )
    if res:
        orm.session.commit()
        return True
    else:
        res = IAPReceipt.query.filter(IAPReceipt.id == transaction_id).filter(IAPReceipt.provide_status == 2).update(
        {
            'provide_status': 1,
            'updated_at': datetime.utcnow()
        }
    )
        if res:
            orm.session.commit()
            return True
        else:
            return False


@sql_wrapper
def update_receipt_provide_fail(transaction_id):
    res = IAPReceipt.query.filter(IAPReceipt.id == transaction_id).filter(IAPReceipt.provide_status == 0).update(
        {
            'provide_status': 2,
            'updated_at': datetime.utcnow()
        }
    )
    if res:
        orm.session.commit()
        return True
    else:
        return False






