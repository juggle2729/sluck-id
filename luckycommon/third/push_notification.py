# -*- coding: utf-8 -*-
import logging
import xinge
import jpush
from django.conf import settings

_LOGGER = logging.getLogger('lucky')

# xinge
_XINGE_IOS_ACCESS_ID = settings.XINGE_IOS_ACCESS_ID
_XINGE_IOS_SECRET = settings.XINGE_IOS_SECRET
_XINGE_IPAD_ACCESS_ID = settings.XINGE_IPAD_ACCESS_ID
_XINGE_IPAD_SECRET = settings.XINGE_IPAD_SECRET
_APNS_ENV = settings.APNS_ENV
_XINGE_ANDROID_ACCESS_ID = settings.XINGE_ANDROID_ACCESS_ID
_XINGE_ANDROID_SECRET = settings.XINGE_ANDROID_SECRET


# JPush
_APP_KEY_GP = '2c6545adc2c68b46f72d316b'
_MASTER_SECRET_GP = 'f2f911d07bb49b5032a42098'
_JPUSH_GP = jpush.JPush(_APP_KEY_GP, _MASTER_SECRET_GP)
_JPUSH_GP.set_logging("INFO")

_APP_KEY_CHANNEL = '9620debaabf6e29b7f9b4eb2'
_MASTER_SECRET_CHANNEL = '0557bcb34b73320add5225b7'
_JPUSH_CHANNEL = jpush.JPush(_APP_KEY_CHANNEL, _MASTER_SECRET_CHANNEL)
_JPUSH_CHANNEL.set_logging("INFO")


def push_to_android(user_id, title, body, payload):
    push_channel = _JPUSH_CHANNEL.create_push()
    push_to_android_via_jpush(push_channel, user_id, title, body, payload)
    push_gp = _JPUSH_GP.create_push()
    push_to_android_via_jpush(push_gp, user_id, title, body, payload)


def push_to_ios(user_id, title, body, payload):
    push_to_ios_via_xinge(user_id, title, body, payload)


def push_to_ipad(user_id, title, body, payload):
    push_to_ipad_via_xinge(user_id, title, body, payload)


def push_to_android_via_jpush(push, user_id, title, body, payload):
    alias = "%s_%s" % (user_id, settings.JPUSH_ENV)
    push.audience = jpush.audience(jpush.alias(alias))
    push.notification = jpush.notification(android=jpush.android(alert=body, title=title, extras=payload))
    push.platform = jpush.platform("android")
    push.send()


def push_to_android_via_xinge(user_id, title, body, payload):
    ret_status, ret_msg = xinge.PushAccountAndroid(_XINGE_ANDROID_ACCESS_ID, _XINGE_ANDROID_SECRET, title, body, payload, user_id)
    _LOGGER.info('push notification to android with return: %s, %s, uid: %s' % (ret_status, ret_msg, user_id))


def push_to_ios_via_xinge(user_id, title, body, payload):
    ret_status, ret_msg = xinge.PushAccountIos(_XINGE_IOS_ACCESS_ID, _XINGE_IOS_SECRET, body, payload, user_id, _APNS_ENV)
    _LOGGER.info('push notification to iOS with return: %s, %s, uid: %s' % (ret_status, ret_msg, user_id))


def push_to_ipad_via_xinge(user_id, title, body, payload):
    ret_status, ret_msg = xinge.PushAccountIos(_XINGE_IPAD_ACCESS_ID, _XINGE_IPAD_SECRET, body, payload, user_id, _APNS_ENV)
    _LOGGER.info('push notification to iPad with return: %s, %s, uid: %s' % (ret_status, ret_msg, user_id))
