# -*- coding: utf-8 -*-
from luckycommon.model import orm


class Theme(orm.Model):
    """
    content: JSON str
    {
        "theme_color":{
             "global_theme_color":"253,119,56",   //主题色，全局默认的主体色调(背景)
	        "global_theme_text_color" : "r,g,b",
            // ...
        },
        "theme_icon":{
            "main_title_category_icon": "http://xxxxx.png",// 主界面title bar左侧的分类按钮图标
		    "main_title_search_icon": "",
            // ... 
        },
        "main_tab":{
            "text_normal_color":"113,113,120",
            "text_select_color":"253,119,56",
            // ...
        }
    }
    """
    __tablename__ = "theme_lib"
    id = orm.Column(orm.BigInteger, primary_key=True)
    title = orm.Column(orm.TEXT)
    content = orm.Column(orm.TEXT)
    abtest = orm.Column(orm.Integer)
    remark = orm.Column(orm.TEXT)
    active = orm.Column(orm.Boolean)
    start_ts = orm.Column(orm.BigInteger)
    end_ts = orm.Column(orm.BigInteger)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)