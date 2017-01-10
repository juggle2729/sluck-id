# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from luckycommon.model.category import Category, CategoryActivity

from luckycommon.utils.decorator import sql_wrapper

_LOGGER = logging.getLogger('lucky')


@sql_wrapper
def get_category_aids(category_id):
    tids = []
    items = CategoryActivity.query.filter(
        CategoryActivity.category_id == category_id).all()
    for item in items:
        tids.append(item.template_id)
    return tids


@sql_wrapper
def get_all_categorys():
    return Category.query.order_by(Category.order).all()


@sql_wrapper
def create_category(query_dct):
    category = Category()
    for k, v in query_dct.iteritems():
        if hasattr(Category, k):
            setattr(category, k, v)

    category.updated_at = category.created_at = datetime.utcnow()
    category.save()


@sql_wrapper
def update_category(id, query_dct):
    category = Category.query.with_for_update().filter(
        Category.id == id).one()
    for k, v in query_dct.iteritems():
        if hasattr(Category, k) and k != 'updated_at':
            setattr(category, k, v)
    category.updated_at = datetime.utcnow()
    category.save()


def batch_upsert(query_list):
    # if id exist, it is a `put` for `update`, else it's a `post`
    # for `create`
    for item in query_list:
        if not item.get('id'):
            create_category(item)
        else:
            update_category(item.pop('id'), item)


@sql_wrapper
def delete_category(id):
    category = Category.query.with_for_update().filter(
        Category.id == id).one()
    CategoryActivity.query.filter(
        CategoryActivity.category_id == id).delete()
    category.delete()


@sql_wrapper
def get_related_category(template_id):
    return CategoryActivity.query.filter(
        CategoryActivity.template_id == template_id).all()


@sql_wrapper
def set_category(template_id, category_ids):
    CategoryActivity.query.filter(
        CategoryActivity.template_id == template_id).delete()
    for category_id in category_ids:
        ca = CategoryActivity()
        ca.template_id = template_id
        ca.category_id = category_id
        ca.created_at = ca.updated_at = datetime.utcnow()
        ca.save()


@sql_wrapper
def get_category(category_id):
    return Category.query.filter(Category.id == category_id).first()
