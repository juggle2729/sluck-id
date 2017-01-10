# -*- coding: utf-8 -*-
from luckycommon.model import orm
from luckycommon.utils.types import Enum
from luckyplatform import settings

TEMPLATE_ID = 672

TIME_CONF = [{
    'hour': 12,
    'info': {
        'goods_id': 541,
        'name': u'(0 đồng mua ngay)vinaphone Thẻ cào điện thoại 10k',
        'short_title': u'hóa đơn mua hàng 0d',
        'target_amount': 150 if not settings.DEBUG else 4,
        'cover': 'http://p.lucky-gou.com/o_1avvshh7pcum1f1j43mpu3u3psl.png',
        'images': 'http://p.lucky-gou.com/o_1avvshqc41i8jjv3do5mpd1245t7.png',
        'graphics': ''
    }
}, {
    'hour': 16,
    'info': {
        'goods_id': 541,
        'name': u'(0 đồng mua ngay)vinaphone Thẻ cào điện thoại 10k',
        'short_title': u'hóa đơn mua hàng 0d',
        'target_amount': 150 if not settings.DEBUG else 4,
        'cover': 'http://p.lucky-gou.com/o_1avvshh7pcum1f1j43mpu3u3psl.png',
        'images': 'http://p.lucky-gou.com/o_1avvshqc41i8jjv3do5mpd1245t7.png',
        'graphics': ''
    }
}, {
    'hour': 20,
    'info': {
        'goods_id': 541,
        'name': u'(0 đồng mua ngay)vinaphone Thẻ cào điện thoại 10k',
        'short_title': u'hóa đơn mua hàng 0d',
        'target_amount': 150 if not settings.DEBUG else 4,
        'cover': 'http://p.lucky-gou.com/o_1avvshh7pcum1f1j43mpu3u3psl.png',
        'images': 'http://p.lucky-gou.com/o_1avvshqc41i8jjv3do5mpd1245t7.png',
        'graphics': ''
    }
}
]


class ZeroShare(orm.Model):
    __tablename__ = "zero_share"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    template_id = orm.Column(orm.Integer)
    term_number = orm.Column(orm.Integer)
    share_times = orm.Column(orm.Integer)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)


class ZeroPush(orm.Model):
    __tablename__ = "zero_push"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer)
    need_push = orm.Column(orm.Integer, default=0)
    created_at = orm.Column(orm.DATETIME)
    updated_at = orm.Column(orm.DATETIME)
