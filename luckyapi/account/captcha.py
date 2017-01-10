# -*- coding: utf-8 -*-
import logging
from cStringIO import StringIO

from luckycommon.cache import account as account_cache
from luckycommon.utils import exceptions as err
from luckycommon.utils.code import create_validate_code
from luckycommon.utils.decorator import response_wrapper
from luckycommon.utils.id_generator import generate_uuid

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET


_LOGGER = logging.getLogger('lucky')


def create_geetest(request):
    """
    获取geetest验证码
    """
    pass


def create_image_code(req):
    num = req.GET.get('num')
    if not num:
        raise err.ParamError('invalid')
    image, code_str = create_validate_code()
    output = StringIO()
    image.save(output, 'PNG', quality=95)
    _LOGGER.info('create image code, num:%s, code str:%s', num, code_str)
    account_cache.set_image_code(num, code_str)
    return HttpResponse(output.getvalue(), 'image/png')


@require_GET
@response_wrapper
def get_captcha(request):
    return create_image_code(request)


def check_image_code(query_dct):
    code = query_dct.get('code')
    num = query_dct.get('register_num')
    if not code or not num:
        return False
    right_code = account_cache.get_image_code(num)
    if not right_code or code.lower() != right_code.lower():
        # meanwhile, clear the code
        account_cache.clear_image_code(num)
        return False
    return True


def validate_captcha(request, query_dct):
    return check_image_code(query_dct)
