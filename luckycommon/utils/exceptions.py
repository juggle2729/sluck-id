# -*- coding: utf-8 -*-
from luckycommon.utils.respcode import HttpCode, StatusCode


# Basic Exceptions
class Error(Exception):
    HTTPCODE = HttpCode.SERVER_ERROR
    STATUS = StatusCode.UNKNOWN_ERROR

    def __init__(self, msg='', httpcode=None, status=None):
        super(Error, self).__init__(msg)
        if httpcode:
            self.HTTPCODE = httpcode
        if status:
            self.STATUS = status


class ClientError(Error):
    HTTPCODE = HttpCode.BAD_REQUEST


class ServerError(Error):
    pass


class ThirdPartyError(Error):
    pass


class WechatError(ThirdPartyError):
    pass


class PingXXError(ThirdPartyError):
    STATUS = StatusCode.PINGXX_PLATFORM_ERROR
    pass

# General Exceptions


class ParamError(ClientError):
    STATUS = StatusCode.PARAM_REQUIRED


class DataError(ClientError):
    STATUS = StatusCode.DATA_ERROR


class DbError(ServerError):
    STATUS = StatusCode.DB_ERROR


class CacheError(ServerError):
    STATUS = StatusCode.CACHE_ERROR


# Specific Exception
class ProtocolError(ClientError):
    HTTPCODE = HttpCode.FORBIDDEN
    STATUS = StatusCode.HTTPS_REQUIRED


class SmsPlatformError(ServerError):
    STATUS = StatusCode.SMS_PLATFORM_ERROR


class AuthenticateError(DataError):
    HTTPCODE = HttpCode.UNAUTHORIZED


class PermissionError(ClientError):
    STATUS = StatusCode.NOT_ALLOWED
    HTTPCODE = HttpCode.FORBIDDEN


class NotImplementedError(ServerError):
    HTTPCODE = HttpCode.NOT_IMPLEMENTED


class ResourceInsufficient(ClientError):
    HTTPCODE = HttpCode.FORBIDDEN
    STATUS = StatusCode.RESOURCE_INSUFFICIENT


class ResourceNotFound(ClientError):
    HTTPCODE = HttpCode.NOT_FOUND


class ResourceNotModified(ClientError):
    HTTPCODE = HttpCode.NOT_MODIFIED


class BalanceInsufficient(ClientError):
    pass


class RechargeCardError(Error):
    HTTPCODE = HttpCode.RECHARGED_CARD_ERROR
