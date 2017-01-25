# -*- coding: utf-8 -*-
from luckyapi.model import BaseModel


class Template(BaseModel):
    structure = {
        'name': basestring,
        'desc': basestring,
        'images': basestring,
        'graphics': basestring,
        'goods_id': int,
        'target_amount': int,
        'price': int,
        'unit': int,
        'country': basestring
    }


class CalcRecord(BaseModel):
    structure = {
        'lucky_number': basestring,  # 幸运号码
        'calc': {
            'url': basestring,  # 计算详情页面,不为null则跳转打开，否则使用native方式呈现下面的数据
            'result_a': long,
            'result_b': long,
            'a_list': [
                {
                    'time': basestring,  # 夺宝时间
                    'code': basestring,  # 组合数值
                    'name': basestring,  # 用户nick name
                }
            ]
        },
        'reveal_time': basestring,  # 揭晓时间
    }


class Revealed(BaseModel):
    structure = {
        'term': int,  # 期号
        'name': basestring,  # 活动名称
        'activity_id': basestring,
        'lucky_number': basestring,  # 幸运号码
        'reveal_time': basestring,  # 揭晓时间
        'winner': {
            'uid': basestring,  # user_id
            'avatar': basestring,  # avar url
            'nick_name': basestring,  # nick name
            'ip': basestring,  # ip
            'addr': basestring,  # address
            'num_count': int,  # 获奖者的号码个数
            'time': basestring,  # 夺宝时间
        }
    }


class ActivityDetail(BaseModel):
    structure = {
        'id': basestring,
        'gid': int,
        'term': int,  # 当前期号
        'created_at': basestring,
        'latest_term': int,  # 最新一期的期号
        'latest_id': basestring,  # 最新一期的id
        'status': int,  # activity::status 1:进行中  2:即将揭晓  3:已经揭晓
        'goods': {
            'name': basestring,
            'desc': basestring,  # activity::desc
            'images': basestring,  # 组图，activity:images
            'cover': basestring,  # 封面 activity::images[0]
            'detail_url': basestring,  # 商品详情页面，如果为null，则使用graphics数据呈现
            'graphics': basestring,  # 图文详情，activity:graphics
        },
        'price': int,  # 购买一次的单价，默认为1个夺宝币，基本不用
        'buy_limit': int,  # 购买限制，0元购即为1
        'unit': int,  # 购买的最小次数，10元区即为10
        'target_amount': int,  # 目标次数
        'current_amount': int,  # 当前筹集次数
        'my': {
            'numbers': list,  # 我的号码
            'order_id': long,  # 我的中奖订单号
            'status': int,  # 订单状态
        },
        'revealing': {  # 即将揭晓的数据
            'remain_ms': long,
            'calc': {
                'url': basestring,  # 计算详情页面,不为null则跳转打开，否则使用native方式呈现下面的数据
                'result_a': long,
                'result_b': None
            }
        },
        'revealed': {  # 已经揭晓的数据
            'lucky_number': basestring,  # 幸运号码
            'calc': {
                'url': basestring,  # 计算详情页面,不为null则跳转打开，否则使用native方式呈现下面的数据
                'result_a': long,
                'result_b': long
            },
            'reveal_time': basestring,  # 揭晓时间
            'winner': {
                'uid': basestring,  # user_id
                'avatar': basestring,  # avar url
                'nick_name': basestring,  # nick name
                'ip': basestring,  # ip
                'addr': basestring,  # address
                'numbers': list,  # 获奖者的号码列表
                'num_count': int,
                'time': basestring,  # 夺宝时间
            }
        },
        'start_time': basestring,  # 夺宝开始的事件，或者第一次购买的时间
        'is_star': int,
        'star_desc': basestring,
        'is_resell': int,
        'resell_price_h': int,
        'resell_price_l': int,
    }


class ActivityLite(BaseModel):
    structure = {
        'id': basestring,
        'gid': int,  # activity::template_id
        'term': int,  # activity::term_id
        'created_at': basestring,
        'goods': {  # 商品相关数据
            'name': basestring,  # activity::name
            'desc': basestring,  # activity::desc
            'cover': basestring,  # 封面 activity::images[0]
        },
        'unit': int,  # 购买的最小次数，10元区即为10
        'price': int,  # 购买一次的单价，默认为1个夺宝币，基本不用
        'buy_limit': int,  # 购买限制，0元购即为1
        'status': int,  # activity::status
        'target_amount': int,  # activity::target_amount
        'current_amount': int,  # activity:current_amount
        'remain_ms': long,  # 离开奖还剩xxx毫秒
        'lucky_number': basestring,  # 幸运号码
        'winner': {
            'uid': basestring,  # user_id
            'avatar': basestring,  # avar url
            'nick_name': basestring,  # nick name
        },
        'is_star': int,
        'is_resell': int,
        'resell_price': int,
    }
