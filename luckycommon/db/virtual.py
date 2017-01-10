# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from random import shuffle, randint

from sqlalchemy import func

from luckycommon.model.virtual import VirtualAwaitingPool, AvatarPool
from luckycommon.db.helper import list_object
from luckycommon.account.db.account import encode_password, update_account
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.utils.exceptions import PermissionError
from luckycommon.model import orm

_LOGGER = logging.getLogger(__name__)


@sql_wrapper
def list_await_users(query_dct):
    return list_object(query_dct, VirtualAwaitingPool)


@sql_wrapper
def get_unused_count():
    return orm.session.query(func.count(AvatarPool)).filter(
        AvatarPool.used_times == 0).scalar()


@sql_wrapper
def get_await_user(id):
    return VirtualAwaitingPool.query.filter(
        VirtualAwaitingPool.id == id).first()


@sql_wrapper
def upsert_await_user(query_dct):
    user = None
    if 'id' in query_dct:
        user = VirtualAwaitingPool.query.with_for_update().filter(
            VirtualAwaitingPool.id == query_dct.pop('id')).first()
    if not user:
        user = VirtualAwaitingPool()
        user.deleted = 0

    for k, v in query_dct.iteritems():
        if hasattr(VirtualAwaitingPool, k):
            if k == "password":
                user.password = encode_password(v)
            else:
                setattr(user, k, v)

    if 'id' not in query_dct:
        user.created_at = user.updated_at = datetime.utcnow()
    # update account
    if user.user_id:
        info = {'id': user.user_id}
        if 'nick_name' in query_dct:
            info['nick_name'] = user.nick_name
        if 'avatar_id' in query_dct:
            info['avatar_id'] = user.avatar_id
        update_account(info)
    user.save()
    return user


@sql_wrapper
def batch_insert_user(data):
    if not data:
        return
    l = len(data)
    unused_avatars = []
    items = AvatarPool.query.with_for_update().filter(
        AvatarPool.used_times == 0).limit(l).all()
    for item in items:
        unused_avatars.append(item)
    shuffle(unused_avatars)
    engine = orm.get_engine(None, None, None)
    to_inserts = []
    for nick_name, ip in data:
        if randint(1, 100) < 30:
            avatar = unused_avatars.pop(0) if unused_avatars else None
        else:
            avatar = None
        to_inserts.append({
            "nick_name": nick_name,
            "ip": ip,
            "avatar_id": avatar.avatar_id if avatar else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        if avatar:
            avatar.used_times += 1
            avatar.save()
    if to_inserts:
        engine.execute(VirtualAwaitingPool.__table__.insert(), to_inserts)


@sql_wrapper
def delete_user(user_id):
    user = VirtualAwaitingPool.query.with_for_update().filter(
        VirtualAwaitingPool.id == user_id).first()
    if user and user.deleted == 0:
        user.delete()
    else:
        raise PermissionError()


@sql_wrapper
def add_avatars(urls):
    engine = orm.get_engine(None, None, None)
    if urls:
        engine.execute(
            AvatarPool.__table__.insert(),
            [{"avatar_id": url, "used_times": 0,
              "created_at": datetime.utcnow(),
              "updated_at": datetime.utcnow()} for url in urls]
        )
