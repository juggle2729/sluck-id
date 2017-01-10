from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    # order v2
    url(r'^activitys/pay/?$', 'luckyapi.views.order_v2.batch_pay'),
    url(r'^activitys/(?P<activity_id>[^/]+)/pay/?$', 'luckyapi.views.order_v2.pay'),
    # activity v2
    url(r'^my/activitys/?$', 'luckyapi.views.activity_v2.get_my_activitys'),
    url(r'^user/(?P<user_id>[^/]+)/activitys/?$', 'luckyapi.views.activity_v2.get_other_activitys'),
    url(r'^activitys/(?P<activity_id>[^/]+)/?$',
        'luckyapi.views.activity_v2.get_activity_detail'),
    url(r'^activitys/(?P<activity_id>[^/]+)/revealed?$',
        'luckyapi.views.activity_v2.get_activity_revealed'),
    url(r'^groups/(?P<template_id>[^/]+)/winners/?$',
        'luckyapi.views.activity_v2.get_last_revealed'),
    url(r'^groups/(?P<template_id>[^/]+)/latest/?$',
        'luckyapi.views.activity_v2.get_latest_activity'),
    # tips v2
    url(r'^tips/?$', 'luckyapi.views.notification.get_tips_v2'),
)
