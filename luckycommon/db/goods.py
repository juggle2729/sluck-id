# -*- coding: utf-8 -*-
import logging

from future.utils import raise_with_traceback

from luckycommon.db.helper import list_object, upsert
from luckycommon.model.stock import Goods
from luckycommon.utils.exceptions import ResourceNotFound
from luckycommon.utils.decorator import sql_wrapper


_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def list_goods(query_dct):
    return list_object(query_dct, Goods)


@sql_wrapper
def create_goods(info):
    return upsert(Goods, info)


@sql_wrapper
def get_goods(goods_id):
    goods = Goods.query.filter(Goods.id == goods_id).first()
    return goods


@sql_wrapper
def delete_goods(goods_id):
    goods = Goods.query.filter(Goods.id == goods_id).first()
    goods.delete()


@sql_wrapper
def add_stock(goods_id, quantity):
    goods = Goods.query.filter(
        Goods.id == goods_id).with_lockmode('update').first()
    if not goods:
        raise_with_traceback(
            ResourceNotFound("goods %s not exists" % goods_id))

    goods.total += quantity
    goods.save()

    return goods


@sql_wrapper
def modify_good_info(goods_id, info):
    return upsert(Goods, info, goods_id)
