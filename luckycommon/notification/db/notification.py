# -*- coding: utf-8 -*-
from future.utils import raise_with_traceback

from luckycommon.cache.redis_cache import get_sync_id, get_sys_sync_id
from luckycommon.model import orm
from luckycommon.notification.model.notification import *
from luckycommon.utils.decorator import sql_wrapper
from luckycommon.db.helper import list_object, get
from luckycommon.utils.exceptions import ParamError


@sql_wrapper
def generate_notification(
        user_id, content, notify_type=NOTIFY_TYPE.SYSTEM, extend=''):
    notification = Notification()
    notification.user_id = user_id
    notification.sync_id = get_sync_id(user_id)
    notification.notify_type = notify_type
    notification.content = content
    notification.extend = extend
    notification.save()
    return notification.sync_id


@sql_wrapper
def generate_sys_notification(content, status=0, extend=''):
    notification = SysNotification()
    notification.sync_id = get_sys_sync_id() if status else 0
    notification.content = content
    notification.extend = extend
    notification.status = status
    notification.save()
    return notification.sync_id


@sql_wrapper
def list_sys_notification(query_dct):
    return list_object(query_dct, SysNotification)


@sql_wrapper
def update_sys_notification(info, id):
    inst = SysNotification.query.with_for_update().filter(
        SysNotification.id == id).one()
    for k in info:
        if k in ('content', 'extend'):
            setattr(inst, k, info[k])
    if inst.status == NOTIFY_STATUS.UNRELEASED and \
            info.get('status') == NOTIFY_STATUS.RELEASED:
        inst.sync_id = get_sys_sync_id()
    if 'status' in info and inst.status != NOTIFY_STATUS.RELEASED:
        inst.status = info['status']

    inst.save()


@sql_wrapper
def get_sys_notification(id):
    return get(SysNotification, id)


@sql_wrapper
def delete_sys_notification(id):
    inst = SysNotification.query.with_for_update().filter(
        SysNotification.id == id).first()
    if not inst:
        return
    if inst.status != NOTIFY_STATUS.UNRELEASED:
        raise_with_traceback(ParamError('status: %s' % inst.status))
    inst.delete()


@sql_wrapper
def get_user_notifications(user_id, sync_id=0, limit=10):
    query = Notification.query.filter(Notification.user_id == user_id)
    query = query.filter(Notification.sync_id > sync_id)
    query = query.order_by(Notification.sync_id).limit(limit)
    return query.all()


@sql_wrapper
def remove_notifications(user_id, remove_list, clear, notify_type=0):
    """
    按版本号删除消息
    """
    query = Notification.query.filter(Notification.user_id == user_id)
    if not clear:
        query = query.filter(Notification.sync_id.in_(remove_list))
    elif notify_type:
        query = query.filter(Notification.notify_type == notify_type)
    query.delete(synchronize_session='fetch')
    orm.session.commit()


@sql_wrapper
def get_sys_notifications(sync_id=0, limit=10):
    """
    获取系统公告消息, 所有用户共享一个sync id
    """
    query = SysNotification.query.filter(SysNotification.status == NOTIFY_STATUS.RELEASED)\
                                 .filter(SysNotification.sync_id > sync_id)
    query = query.order_by(SysNotification.sync_id).limit(limit)
    return query.all()
