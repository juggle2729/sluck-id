# -*- coding: utf-8 -*-
import logging

from future.utils import raise_with_traceback
from pymongo.errors import PyMongoError
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError

from luckycommon.model import orm
from luckycommon.utils.api import JsonResponse
from luckycommon.utils.exceptions import Error, ServerError, DbError, CacheError
from luckycommon.utils.respcode import StatusCodeDict

_LOGGER = logging.getLogger(__name__)


def _wrap2json(data):
    if data is None:
        data = {}
    elif isinstance(data, dict) or isinstance(data, list):
        return JsonResponse(dict(status=0, msg='', data=data), status=200)
    else:
        return data


def response_wrapper(func):
    def _wrapper(request, *args, **kwargs):

        try:
            return _wrap2json(func(request, *args, **kwargs))
        except ServerError as e:
            _LOGGER.exception('server error!')
            return JsonResponse(
                dict(status=e.STATUS,
                     msg=str(e) or StatusCodeDict.get(e.STATUS)),
                status=e.HTTPCODE)
        except Error as e:
            _LOGGER.exception('catched error %s in %s, uid:%s', e.__class__.__name__, request.path, request.user_id)
            return JsonResponse(
                dict(status=e.STATUS,
                     msg=str(e) or StatusCodeDict.get(e.STATUS)),
                status=e.HTTPCODE)
        except Exception as e:
            _LOGGER.exception('unexcepted error!!')
            return JsonResponse(
                dict(status=Error.STATUS, msg=str(e) or u'未知错误'),
                status=Error.HTTPCODE)

    return _wrapper


def sql_wrapper(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            orm.session.rollback()
            raise_with_traceback(DbError(e))
        except Error:
            orm.session.rollback()
            raise
        except Exception as e:
            orm.session.rollback()
            raise_with_traceback(Error(e))
        finally:
            orm.session.close()

    return _wrapper


def cache_wrapper(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RedisError as e:
            raise_with_traceback(CacheError(e))
        except Error:
            raise
        except Exception as e:
            raise_with_traceback(Error(e))

    return _wrapper


def mongo_wrapper(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PyMongoError as e:
            raise_with_traceback(DbError(e))
        except Error:
            raise
        except Exception as e:
            raise_with_traceback(Error(e))

    return _wrapper
