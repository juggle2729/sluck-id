# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Category(orm.Model):

    """
    分类信息表
    """
    __tablename__ = "category"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    name = orm.Column(orm.VARCHAR)
    icon = orm.Column(orm.VARCHAR)
    tag = orm.Column(orm.VARCHAR)                 # 'NEW' 'HOT'
    order = orm.Column(orm.Integer, default=0)    # 顺序
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class CategoryActivity(orm.Model):

    """
    活动分类关系表
    """
    __tablename__ = "category_activity"
    id = orm.Column(orm.Integer, primary_key=True, autoincrement=True)
    category_id = orm.Column(orm.Integer)               # 分类编号
    template_id = orm.Column(orm.Integer)               # 活动模板编号
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
