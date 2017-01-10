# -*- coding: utf-8 -*-
import logging
import random
from datetime import datetime

from django.conf import settings

from luckycommon.account.db import account as account_db
from luckycommon.cache import redis_cache
from luckycommon.db.transaction import add_system_award_transaction
from luckycommon.model.virtual import *
from luckycommon.utils.api import get_city

_LOGGER = logging.getLogger('lucky')

DEFAULT_PASSWORD = 'P@55word!@#ASD'
_ROBOT_AWARD_PRICE = 10000000


def _generate_phone():
    return redis_cache.get_next_virtual_phone()


def create_virtual_account(awaiting_list):
    success_list = []
    for awaiting_account in awaiting_list:
        nick_name = awaiting_account.nick_name
        avatar_id = awaiting_account.avatar_id
        client_ip = awaiting_account.ip
        phone = awaiting_account.phone or _generate_phone()
        phone = str(phone)
        password = awaiting_account.password or DEFAULT_PASSWORD
        try:
            if not avatar_id:
                available_avatar = AvatarPool.query.with_for_update().filter(
                    AvatarPool.used_times == 0).first()
                if available_avatar:
                    avatar_id = available_avatar.avatar_id
                    awaiting_account.avatar_id = avatar_id
                    available_avatar.used_times += 1
                    available_avatar.save()
            account = account_db.create_account({
                'nick_name': nick_name[:20],
                'password': password,
                'avatar_id': avatar_id,
                'phone': phone,
                'email': '',
                'country': settings.COUNTRY,
                'is_virtual': 1
            }, 'channel_virtual', 'package_virtual')
            redis_cache.add_virtual_account(account.id)
            client_city = get_city(client_ip)
            extend = {
                'ip': client_ip,
                'addr': client_city
            }
            user, logon = account_db.login_account('phone', phone, password, extend=extend)
            success_list.append({
                'id': awaiting_account.id,
                'user_id': user.id,
                'token': user.token
            })
            # save to virtual pool
            virtual_account = VirtualPool()
            virtual_account.user_id = user.id
            virtual_account.token = user.token
            virtual_account.save()
            # award
            add_system_award_transaction(user.id, award_amount=_ROBOT_AWARD_PRICE, title=u'系统奖励-v')
            _LOGGER.info('create agent success, uid:%s, token:%s', user.id, user.token)
        except Exception as e:
            _LOGGER.exception('create new virtual account fail.%s', e)
    return success_list


def create():
    items = VirtualAwaitingPool.query.filter(VirtualAwaitingPool.deleted == 0).all()
    if items:
        random_item = random.choice(items)
        _LOGGER.info('choose one random agent from %s length awaiting pool', len(items))
        success_list = create_virtual_account([random_item])
        for obj in success_list:
            VirtualAwaitingPool.query.filter(VirtualAwaitingPool.id == obj['id']).update({
                'deleted': 1,
                'user_id': obj['user_id'],
                'updated_at': datetime.utcnow()
            })
        orm.session.commit()
