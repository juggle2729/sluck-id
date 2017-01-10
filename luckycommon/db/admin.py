# -*- coding: utf-8 -*-
from datetime import datetime

from future.utils import raise_with_traceback
from sqlalchemy.exc import SQLAlchemyError

from luckycommon.model.admin import (User, Permission,
                                     UserToken, ROLE)
from luckycommon.model.admin import orm
from luckycommon.account.db.account import encode_password
from luckycommon.utils.orm import get_count
from luckycommon.utils import exceptions as err
from luckycommon.utils.respcode import StatusCode
from luckycommon.utils import id_generator
from luckycommon.db.helper import (get_orderby, parse_query_dct, list_object,
                                   paginate, generate_filter)


def sql_wrapper(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            orm.session.rollback()
            raise_with_traceback(err.DbError(e))
        except err.Error:
            orm.session.rollback()
            raise
        except Exception as e:
            orm.session.rollback()
            raise_with_traceback(err.Error(e))
        finally:
            orm.session.close()

    return _wrapper


@sql_wrapper
def create_user(email, password, nickname='',
                role=ROLE.FORBIDDEN):
    user = User()
    user.email = email
    user.password = encode_password(password)
    user.nickname = nickname
    user.role = role
    user.created_at = user.updated_at = datetime.utcnow()

    user.save()


@sql_wrapper
def update_user(info, editor_info):
    user = User.query.with_for_update().filter(
        User.id == info['id']).first()
    if not user:
        raise_with_traceback(err.AuthenticateError(
            status=StatusCode.INVALID_USER))
    if info['id'] != editor_info.id and (
            'role' in info and editor_info.role <= int(info['role'])):
        raise_with_traceback(err.PermissionError())

    if 'password' in info:
        info['password'] = encode_password(info['password'])

    for k, v in info.iteritems():
        setattr(user, k, v)

    user.save()
    return user


@sql_wrapper
def list_users(query_dct, origin_role):
    # user can only see lower level users
    query_dct = parse_query_dct(query_dct, User)
    if 'role' in query_dct and origin_role < query_dct['role']:
        raise err.PermissionError()
    elif 'role' not in query_dct:
        query_dct['role'] = {"$lte": origin_role}
    query = User.query.filter(generate_filter(query_dct, User))
    total_count = get_count(query)
    orderby = get_orderby(query_dct.get('$orderby'), User)
    if orderby is not None:
        query = query.order_by(orderby)
    query = paginate(query, query_dct)
    return query.all(), total_count


@sql_wrapper
def get_user(user_id):
    return User.query.filter(User.id == user_id).first()


@sql_wrapper
def login_user(email, password):
    user = User.query.filter(User.email == email).first()
    if not user:
        raise err.AuthenticateError(status=StatusCode.INVALID_USER)

    if user.password != encode_password(password):
        raise err.AuthenticateError(status=StatusCode.WRONG_PASSWORD)

    user_token = UserToken()
    user_token.token = id_generator.generate_uuid()
    user_token.deleted = 0
    user_token.user_id = user.id
    user_token.save()

    user_info = user.as_dict()
    user_info['token'] = user_token.token
    user_info.pop('password', '')
    return user_info


@sql_wrapper
def logout_device(user_id, token):
    UserToken.query.filter(
        UserToken.user_id == user_id).filter(UserToken.token == token).update(
        {'deleted': 1})

    orm.session.commit()


@sql_wrapper
def logout_user(user_id):
    UserToken.query.filter(
        UserToken.user_id == user_id).update({'deleted': 1})
    orm.session.commit()


@sql_wrapper
def get_online_info(user_id, token):
    return UserToken.query.filter(
        UserToken.user_id == user_id).filter(UserToken.token == token).first()


@sql_wrapper
def list_perm(query_dct):
    return list_object(query_dct, Permission)


@sql_wrapper
def create_perm(url, permission, min_role):
    perm = Permission()
    perm.url = url
    perm. permission = permission
    perm.min_role = min_role
    perm.created_at = perm.updated_at = datetime.utcnow()
    perm.save()
    return perm


@sql_wrapper
def get_perm(url=None, perm=None, id=None):
    if id:
        return Permission.query.filter(
            Permission.id == id).first()
    elif url and perm:
        return Permission.query.filter(
            Permission.url == url).filter(
            Permission.permission == perm).first()


@sql_wrapper
def update_perm(id, min_role):
    perm = Permission.query.filter(
        Permission.id == id).with_for_update().first()
    if perm:
        perm.min_role = min_role
        perm.save()
