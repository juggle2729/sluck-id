from django.conf.urls import patterns, url

from luckyapi.account.auth import AuthCodeView

urlpatterns = patterns(
    '',
    # account
    url(r'^register/?$', 'luckyapi.account.auth.register'),
    url(r'^login/?$', 'luckyapi.account.auth.login'),
    url(r'^third_login/?$', 'luckyapi.account.auth.third_login'),
    url(r'^third_bind/?$', 'luckyapi.account.auth.third_bind'),
    url(r'^logout/?$', 'luckyapi.account.auth.logout'),
    url(r'^user/?$', 'luckyapi.account.user.get_user'),
    url(r'^user/auth_code/?$', AuthCodeView.as_view()),
    url(r'^user/modify/?$', 'luckyapi.account.user.modify_user'),
    url(r'^user/public_profile/?$', 'luckyapi.account.user.get_public_profile'),
    url(r'^reset_password/?$', 'luckyapi.account.auth.reset_password'),
    # qr code
    url(r'^qrcode/?$', 'luckyapi.account.user.get_qr_code'),
    # image code
    url(r'^imagecode/check/?$', 'luckyapi.account.auth.check_image_code'),
    url(r'^imagecode/?$', 'luckyapi.account.auth.create_image_code'),
    # captcha
    url(r'^getcaptcha/?$', 'luckyapi.account.captcha.get_captcha'),
    # receipt
    url(r'^receipts/?$', 'luckyapi.views.receipt.get_receipts'),
    url(r'^receipts/add/?$', 'luckyapi.views.receipt.add_receipt'),
    url(r'^receipts/(?P<receipt_id>[^/]+)/modify/?$', 'luckyapi.views.receipt.modify_receipt'),
    url(r'^receipts/(?P<receipt_id>[^/]+)/remove/?$', 'luckyapi.views.receipt.remove_receipt'),
    # activity
    url(r'^create_template/?$', 'luckyapi.views.activity.create_template'),
    url(r'^template/(?P<template_id>[^/]+)/start/?$', 'luckyapi.views.activity.start_template'),
    url(r'^activitys/?$', 'luckyapi.views.activity.get_activitys'),
    url(r'^groups/(?P<template_id>[^/]+)/terms/(?P<term_number>[^/]+)/?$', 'luckyapi.views.activity.get_activity_detail_by_term'),
    url(r'^activitys/(?P<activity_id>[^/]+)/records/timeline/?$', 'luckyapi.views.activity.get_buy_records_timeline'),
    url(r'^activitys/(?P<activity_id>[^/]+)/records/(?P<record_id>[^/]+)/?$', 'luckyapi.views.activity.get_record_numbers'),
    url(r'^activitys/(?P<activity_id>[^/]+)/records/?$', 'luckyapi.views.activity.get_buy_records'),
    url(r'^activitys/(?P<activity_id>[^/]+)/calclist/?$', 'luckyapi.views.activity.get_calc_record'),
    url(r'^activitys/(?P<activity_id>[^/]+)/billboard/?$', 'luckyapi.views.activity.get_billboard'),
    url(r'^activitys/(?P<activity_id>[^/]+)/users/?$', 'luckyapi.views.activity.get_users_in_activity'),
    url(r'^pk/?$', 'luckyapi.views.pk.get_pk_activitys'),
    # transaction
    url(r'^transactions/?$', 'luckyapi.views.transaction.get_transactions'),
    url(r'^transfer/?$', 'luckyapi.views.transaction.transfer_coin'),
    url(r'^pay/types/?$', 'luckyapi.views.transaction.get_pay_types'),
    url(r'^pay/ready/?$', 'luckyapi.views.transaction.create_pay'),
    url(r'^pay/(?P<pay_id>[^/]+)/submit/?$', 'luckyapi.views.transaction.pay_submit'),
    url(r'^pay/(?P<pay_id>[^/]+)/status/?$', 'luckyapi.views.transaction.get_pay_status'),
    url(r'^pay/paypal/notify/?$', 'luckyapi.views.transaction.paypal_notify'),
    url(r'^pay/paypal/success/?$', 'luckyapi.views.transaction.paypal_success'),
    url(r'^pay/close_webview/?$', 'luckyapi.views.transaction.close_webview'),
    url(r'^pay/paypal/failed/?$', 'luckyapi.views.transaction.paypal_failed'),
    url(r'^pay/coda_pay/proxy/?$', 'luckyapi.views.transaction.coda_proxy'),
    url(r'^pay/coda_pay/gateway/(?P<token>[^/]+)/?$', 'luckyapi.views.transaction.coda_gateway'),
    url(r'^pay/coda_pay/notify/?$', 'luckyapi.views.transaction.coda_notify'),
    url(r'^pay/google_pay/notify/?$', 'luckyapi.views.transaction.google_notify'),
    url(r'^pay/nganluong/return/(?P<pay_id>[^/]+)/?$', 'luckyapi.views.transaction.nganluong_return_page'),
    url(r'^pay/nganluong/notify/?$', 'luckyapi.views.transaction.nganluong_handle_notify'),
    url(r'^pay/nganluong/check_order/?$', 'luckyapi.views.transaction.nganluong_check_order'),
    url(r'^pay/fortumo/notify/?$', 'luckyapi.views.transaction.fortumo_notify'),
    url(r'^pay/payssion/notify/?$', 'luckyapi.views.transaction.payssion_notify'),
    url(r'^pay/precard/(?P<pay_id>[^/]+)/?$', 'luckyapi.views.transaction.precard_gateway'),
    url(r'^pay/self_recharge_card/(?P<pay_id>[^/]+)/?$', 'luckyapi.views.transaction.consume_self_recharge_card'),
    url(r'^pay/check_self_recharge_card/?$', 'luckyapi.views.transaction.check_self_recharge_card'),
    url(r'^pay/indomog/notify/?$', 'luckyapi.views.transaction.indomog_notify'),
    url(r'^pay/notify/indomog/?$', 'luckyapi.views.transaction.indomog_notify'),
    url(r'^pay/notify/doku/?$', 'luckyapi.views.transaction.doku_notify'),
    url(r'^pay/identify/doku/?$', 'luckyapi.views.transaction.doku_identify'),
    url(r'^pay/mimo/notify/?$', 'luckyapi.views.transaction.mimo_notify'),
    url(r'^pay/bluepay/notify/?$', 'luckyapi.views.transaction.bluepay_notify'),
    url(r'^pay/bubble_mimo/notify/?$', 'luckyapi.views.transaction.bubble_mimo_notify'),
    url(r'^pay/huawei_epay/notify/?$', 'luckyapi.views.transaction.huawei_epay_notify'),
    # notification
    url(r'^notifications/?$', 'luckyapi.views.notification.get_notifications'),
    url(r'^sysannounce/?$', 'luckyapi.views.notification.get_sys_notifications'),
    url(r'^notifications/remove/?$', 'luckyapi.views.notification.remove'),
    url(r'^tips/track/?$', 'luckyapi.views.notification.mark_tips_read'),
    # internal push
    url(r'^internal/push/shipping/?$', 'luckyapi.views.notification.push_shipping'),
    # order
    url(r'^activitys/(?P<activity_id>[^/]+)/orders/(?P<order_id>[^/]+)/status/?$', 'luckyapi.views.order.current_status'),
    url(r'^orders/(?P<order_id>[^/]+)/award/?$', 'luckyapi.views.order.award'),
    url(r'^orders/(?P<order_id>[^/]+)/deal/?$', 'luckyapi.views.order.deal'),
    url(r'^passcard/?$', 'luckyapi.views.order.get_available_passcard'),
    # preset
    url(r'^preset/?$', 'luckyapi.views.preset.fetch_preset'),
    url(r'^banners/?$', 'luckyapi.views.preset.fetch_banner'),
    url(r'^shortcut/?$', 'luckyapi.views.preset.fetch_shortcut'),
    url(r'^discovery/?$', 'luckyapi.views.preset.fetch_discovery'),
    # third party(img, push...)
    url(r'^third/qiniu/token/?$', 'luckyapi.views.third.get_qiniu_token'),
    url(r'^third/qiniu/remove/?$', 'luckyapi.views.third.delete_data'),
    url(r'^third/datacell/fail/?$', 'luckyapi.views.third.datacell_f'),
    url(r'^third/datacell/success/?$', 'luckyapi.views.third.datacell_s'),
    url(r'^third/pulsa/?$', 'luckyapi.views.third.mobilepulsa'),
    url(r'^third/huawei_payment_status/?$', 'luckyapi.views.third.huawei_epay_info'),
    # show
    url(r'^my/shows/?$', 'luckyapi.views.show.get_my_shows'),
    url(r'^my/shows/detail/?$', 'luckyapi.views.show.get_my_show_detail'),
    url(r'^user/(?P<user_id>[^/]+)/shows/?$', 'luckyapi.views.show.get_other_shows'),
    url(r'^shows/timeline/?$', 'luckyapi.views.show.get_timeline'),
    url(r'^shows/(?P<show_id>[^/]+)/edit/?$', 'luckyapi.views.show.edit'),
    url(r'^shows/(?P<show_id>[^/]+)/?$', 'luckyapi.views.show.get_show_detail'),
    url(r'^shows/(?P<show_id>[^/]+)/verify/?$', 'luckyapi.views.show.verify'),
    # scrolling
    url(r'^scrolling/?$', 'luckyapi.views.scrolling.fetch_scrolling'),
    url(r'^luckywall/?$', 'luckyapi.views.scrolling.fetch_wall'),
    url(r'^horn/?$', 'luckyapi.views.scrolling.fetch_horn'),
    # shopping cart
    url(r'^cart/list/?$', 'luckyapi.views.cart.list_cart'),
    url(r'^cart/edit/?$', 'luckyapi.views.cart.edit_cart'),
    # coupon
    url(r'^my/coupons/?$', 'luckyapi.views.coupon.get_my_coupons'),
    url(r'^coupons/available/?$', 'luckyapi.views.coupon.get_available_coupons'),
    url(r'^coupons/(?P<group_coupon_id>[^/]+)/snatch/?$', 'luckyapi.views.coupon.snatch_group_coupon'),
    # campaign
    url(r'^campaign/(?P<campaign_id>[^/]+)/achievement/?$', 'luckyapi.views.campaign.fetch_user_achievement'),
    url(r'^campaign/(?P<campaign_id>[^/]+)/level/(?P<level_id>[^/]+)/activate/?$', 'luckyapi.views.campaign.activate_user_achievement'),
    url(r'^campaign/wealthygod/fresh/?$', 'luckyapi.views.campaign.fresh_god'),
    url(r'^campaign/(?P<campaign_name>[^/]+)/recommend/?$', 'luckyapi.views.campaign.recommend_campaign_fresh'),
    url(r'^campaign/(?P<campaign_name>[^/]+)/recommend/coupon/?$', 'luckyapi.views.campaign.recommend_coupon_status'),
    url(r'^campaign/(?P<campaign_name>[^/]+)/recommend/award/?$', 'luckyapi.views.campaign.fetch_recommend_coupon'),
    url(r'^campaign/(?P<campaign_name>[^/]+)/recommend/timeline/?$', 'luckyapi.views.campaign.recommend_award_timeline'),
    url(r'^campaign/(?P<campaign_id>[^/]+)/timeline/?$', 'luckyapi.views.campaign.campaign_award_timeline'),
    url(r'^campaign/quiz_status/?$', 'luckyapi.views.campaign.quiz_status'),
    url(r'^campaign/submit_quiz/?$', 'luckyapi.views.campaign.submit_quiz'),
    # fortune wheel
    url(r'^fortunewheel/timeline/?$', 'luckyapi.views.wheel.get_timeline'),
    url(r'^fortunewheel/awardlist/?$', 'luckyapi.views.wheel.get_award_list'),
    url(r'^fortunewheel/status/?$', 'luckyapi.views.wheel.get_wheel_status'),
    url(r'^fortunewheel/play/?$', 'luckyapi.views.wheel.play_wheel'),
    # first double
    url(r'^firstdouble/status/?$', 'luckyapi.views.campaign.first_double_status'),
    url(r'^firstdouble/apply/?$', 'luckyapi.views.campaign.first_double_apply'),
    # miss return
    url(r'^missreturn/status/?$', 'luckyapi.views.campaign.miss_return_status'),
    # zero
    url(r'^zero/fresh/?$', 'luckyapi.views.campaign.fresh_zero'),
    url(r'^zero/share/?$', 'luckyapi.views.campaign.share_zero'),
    # sunday
    url(r'^sunday/fresh/?$', 'luckyapi.views.campaign.fresh_sunday'),
    url(r'^sunday/apply/?$', 'luckyapi.views.campaign.sunday_apply'),
    # credit
    url(r'^credit/reward_config?$', 'luckyapi.views.credit.reward_config'),
    url(r'^my/credit/?$', 'luckyapi.views.credit.get_my_credit'),
    url(r'^credit/records/?$', 'luckyapi.views.credit.get_credit_records'),
    url(r'^credit/exchange/?$', 'luckyapi.views.credit.credit_exchange'),
    url(r'^credit/pool/?$', 'luckyapi.views.credit.get_credit_pool'),
    url(r'^credit/distribution/?$', 'luckyapi.views.credit.get_latest_distribution'),
    # check
    url(r'^sign/status/?$', 'luckyapi.views.check.sign_status'),
    url(r'^check/sign/?$', 'luckyapi.views.check.check_sign'),
    # social
    url(r'^social/share/?$', 'luckyapi.views.check.submit_share'),
    # partner
    # url(r'^inviter/track/?$', 'luckyapi.views.partner.track_inviter'),
    # url(r'^inviter/add/?$', 'luckyapi.views.partner.add_inviter'),
    # url(r'^inviter/entry/?$', 'luckyapi.views.partner.get_entry'),
    url(r'^partner/reward/records/?$', 'luckyapi.views.partner.reward_record'),
    url(r'^partner/reward/?$', 'luckyapi.views.partner.reward_status'),
    url(r'^partner/accu/?$', 'luckyapi.views.partner.current_accumulation'),
    url(r'^partner/coupon/status/?$', 'luckyapi.views.partner.award_status'),
    url(r'^partner/coupon/(?P<level_id>[^/]+)/activate/?$', 'luckyapi.views.partner.activate_level'),
    # mission
    url(r'^mission/(?P<mission_id>[^/]+)/status/?$', 'luckyapi.views.mission.get_status'),
    url(r'^mission/(?P<mission_id>[^/]+)/activate/?$', 'luckyapi.views.mission.activate'),
    url(r'^mission/(?P<mission_id>[^/]+)/checkstep/(?P<step_id>[^/]+)/?$', 'luckyapi.views.mission.check_step'),
    # recommend
    url(r'^recommend/activitys/?$', 'luckyapi.views.recommend.recommend_activitys'),
    url(r'^recommend/fresh/?$', 'luckyapi.views.recommend.recommend_fresh'),
    # area
    url(r'^regions/?$', 'luckyapi.views.region.get_regions'),
    # category
    url(r'^categorys/?$', 'luckyapi.views.activity.get_all_categorys'),
    url(r'^categorys/(?P<category_id>[^/]+)/?$', 'luckyapi.views.activity.get_category_activitys'),
    # search
    url(r'^search/hotkeys/?$', 'luckyapi.views.activity.get_hot_keys'),
    url(r'^search/?$', 'luckyapi.views.activity.get_search_activitys'),
    url(r'^tids/?$', 'luckyapi.views.activity.get_tids_activitys'),
    # level
    url(r'^my/level/?$', 'luckyapi.views.level.get_my_level'),
    url(r'^level/activate_coupon/?$', 'luckyapi.views.level.activate_coupon'),
    url(r'^my/level/rank/?$', 'luckyapi.views.level.get_level_rank'),
    url(r'^my/level/week_rank/?$', 'luckyapi.views.level.get_level_week_rank'),
    url(r'^my/level/week_rank_list/?$', 'luckyapi.views.level.get_level_week_rank_list'),
    # feedback
    url(r'^feedback/?$', 'luckyapi.feedback.feedback.feedback'),
    url(r'^feedback/uninstall/track/?$', 'luckyapi.feedback.uninstall.create_device_stats'),
    url(r'^feedback/uninstall/reason/?$', 'luckyapi.feedback.uninstall.create_uninstall_reason'),

    # message
    url(r'^conversations/?$', 'luckyapi.views.message.get_conversations'),
    url(r'^conversations/(?P<conversation_id>[^/]+)/messages/?$', 'luckyapi.views.message.get_messages'),
    url(r'^conversations/remove?$', 'luckyapi.views.message.remove_conversation'),
    url(r'^conversations/mark_as_read?$', 'luckyapi.views.message.mark_conversation'),
    url(r'^messages/send?$', 'luckyapi.views.message.send_message'),
)
