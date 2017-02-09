# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from luckyadmin.views.user import (UserView, SingleUserView, PermissionView,
                                   SinglePermissionView)
from luckyadmin.views.activity import (ActivityTemplateView,
                                       SingleActivityTemplateView,
                                       ActivityListView)
from luckyadmin.views.order import OrderView, SingleOrderView
from luckyadmin.views.goods import GoodsView, SingleGoodsView
from luckyadmin.views.preset import (PresetView, SinglePresetView,
                                     SingleBannerView, BannerView,
                                     SingleLoadingView, LoadingView,
                                     SingleDiscoveryView, DiscoveryView,
                                     ShortcutView, SingleShortcutView)
from luckyadmin.views.show import ShowView, SingleShowView
from luckyadmin.views.category import CategoryView, SingleCategoryView
from luckyadmin.views.virtual import AwaitVirtualView, SingleAwaitVirtualView
from luckyadmin.views.coupon import (CouponTemplateView,
                                     SingleCouponTemplateView)
from luckyadmin.views.abtest import ABTestView, SingleABTestView
from luckyadmin.stats.vips import MissedVipsView, BackVipsView
from luckyadmin.views.feedback import FeedbackView, UninstallView
from luckyadmin.views.notify import NotificationView, SingleNotificationView

urlpatterns = patterns(
    '',
    # user
    url(r'^user/login/?$', 'luckyadmin.views.user.login'),
    url(r'^user/logout/?$', 'luckyadmin.views.user.logout'),
    url(r'^user/?$', UserView.as_view()),
    url(r'^user/(?P<user_id>\d+)/?$', SingleUserView.as_view()),
    url(r'^permission/?$', PermissionView.as_view()),
    url(r'^permission/(?P<perm_id>\d+)/?$', SinglePermissionView.as_view()),
    # template
    url(r'^activity/template/?$', ActivityTemplateView.as_view()),
    url(r'^activity/?$', ActivityListView.as_view()),
    url(r'^activity/template/(?P<template_id>\d+)/?$',
        SingleActivityTemplateView.as_view()),
    # order
    url(r'^order/?$', OrderView.as_view()),
    url(r'^order/(?P<order_id>\d+)/?$', SingleOrderView.as_view()),
    # goods
    url(r'^goods/?$', GoodsView.as_view()),
    url(r'^goods/(?P<goods_id>\d+)/?$', SingleGoodsView.as_view()),
    # uptoken
    url(r'^uptoken/?$', 'luckyadmin.views.uptoken.get_uptoken'),
    url(r'^image/delete/?$', 'luckyadmin.views.uptoken.delete_image'),
    # show
    url(r'^show/?$', ShowView.as_view()),
    url(r'^show/(?P<show_id>\d+)/?$', SingleShowView.as_view()),
    # preset data
    url(r'^preset/?$', PresetView.as_view()),
    url(r'^preset/(?P<preset_id>\d+)/?$', SinglePresetView.as_view()),
    url(r'^preset/banner/?$', BannerView.as_view()),
    url(r'^preset/banner/(?P<banner_id>\d+)/?$', SingleBannerView.as_view()),
    url(r'^preset/discovery/?$', DiscoveryView.as_view()),
    url(r'^preset/discovery/(?P<discovery_id>\d+)/?$',
        SingleDiscoveryView.as_view()),
    url(r'^preset/loading/?$', LoadingView.as_view()),
    url(r'^preset/loading/(?P<loading_id>\d+)/?$',
        SingleLoadingView.as_view()),
    url(r'preset/shortcut/?$', ShortcutView.as_view()),
    url(r'preset/shortcut/(?P<shortcut_id>\d+)/?$',
        SingleShortcutView.as_view()),
    # category
    url(r'^category/?$', CategoryView.as_view()),
    url(r'^category/(?P<category_id>\d+)/?$', SingleCategoryView.as_view()),
    # virtual account
    url(r'^virtual/?$', AwaitVirtualView.as_view()),
    url(r'^virtual/(?P<user_id>\d+)/?$', SingleAwaitVirtualView.as_view()),
    url(r'^virtual/avatar/?$', 'luckyadmin.views.virtual.upload_avatars'),
    url(r'^virtual/account/(?P<user_id>\d+)/?$',
        'luckyadmin.views.virtual.update_virtual_account'),
    # coupon template
    url(r'^coupon/template/?$', CouponTemplateView.as_view()),
    url(r'^coupon/template/(?P<coupon_template_id>\d+)/?$',
        SingleCouponTemplateView.as_view()),
    url(r'^coupon/add/?$', 'luckyadmin.views.coupon.manual_create_coupon'),
    # abtest
    url(r'^abtest/?$', ABTestView.as_view()),
    url(r'^abtest/(?P<abtest_id>\d+)/?$', SingleABTestView.as_view()),
    # feedback
    url(r'feedback/?$', FeedbackView.as_view()),
    url(r'feedback/uninstall/?$', UninstallView.as_view()),
    #url(r'feedback/uninstall/report/?$',
    #    'luckyadmin.stats.report.get_uninstall_report'),
    url(r'notification/?$', NotificationView.as_view()),
    url(r'notification/(?P<notify_id>\d+)/?$',
        SingleNotificationView.as_view()),
    # for mobile console
    url(r'^stats/?$', "luckyadmin.stats.total.get_stats"),
    url(r'^stats/recharge/?$', "luckyadmin.stats.total.get_recharge_list"),
    url(r'^stats/limit/?$', "luckyadmin.stats.total.set_limit"),
    url(r'^account/(?P<account_id>\d+)/?$',
        "luckyadmin.stats.account.get_account_info"),
    url(r'^account/(?P<account_id>\d+)/recharge/?$',
        "luckyadmin.stats.account.get_recharge_list"),
    url(r'^account/(?P<account_id>\d+)/win/?$',
        "luckyadmin.stats.account.get_win_list"),
    url(r'^account/(?P<account_id>\d+)/coupon/?$',
        "luckyadmin.stats.account.get_coupon_list"),
    url(r'^account/(?P<account_id>\d+)/transaction/?$',
        "luckyadmin.stats.account.get_transaction_list"),
    url(r'^activity/?$', "luckyadmin.stats.activity.get_activities"),
    url(r'^activity/(?P<activity_id>[^/]+)/?$',
        "luckyadmin.stats.activity.get_activity"),
    url(r'^activity/(?P<activity_id>[^/]+)/buyed/?$',
        "luckyadmin.stats.activity.get_buy_record"),
    url(r'^coupon/?$', "luckyadmin.stats.coupon.get_coupons"),
    # for web console
    url(r'^stats/activity/?$',
        "luckyadmin.stats.activity.get_activities_plus"),
    url(r'^stats/order/?$',
        "luckyadmin.stats.order.get_order_list"),
    url(r'^stats/coupon/?$',
        "luckyadmin.stats.coupon.get_coupon_list"),
    url(r'^stats/pay/?$',
        "luckyadmin.stats.pay.get_pay_list"),
    url(r'^stats/missed_vips/?$', MissedVipsView.as_view()),
    url(r'^stats/back_vips/?$', BackVipsView.as_view()),
    # for report
    url(r'^report/overview/user/?$',
        "luckyadmin.report.overview.get_user_overview"),
    url(r'^report/overview/activity/?$',
        "luckyadmin.report.overview.get_activity_overview"),
    url(r"report/overview/cost/?$",
        "luckyadmin.report.overview.get_cost_overview"),
)
