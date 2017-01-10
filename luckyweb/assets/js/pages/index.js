'use strict';
//  Author: AdminDesigns.com
//
//  This file is reserved for changes made by the use.
//  Always seperate your work from the theme. It makes
//  modifications, and future theme updates much easier
//

var LuckyConsole = function ($, _) {
    var app = null;
    var opModelCls = function () {
        var Template = Backbone.Model.extend({
            defaults: {
                "name": "",
                "short_title": "",
                "desc": "",
                "images": "",
                "price": 1,
                "goods_id": "",
                "unit": 1,
                "target_amount": 100,
                "country": "cn",
                "current_term": 0,
                "status": 0,
                "graphics": "",
                "weight": 0,
                "buy_limit": 0,
                "category_ids": [],
                "pk": 0
            },
            urlRoot: "/admin/activity/template/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var TemplateCollection = Backbone.Collection.extend({
            model: Template,
            url: "/admin/activity/template/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Activity = Backbone.Model.extend({
            defaults: {
                id: '',
                name: '',
                price: 1,
                unit: 1,
                status: 1,
                current_amount: 0,
                target_amount: 0,
                winner: '',
                term_number: 0,
                order_id: '',
                is_virtual: false,
            },
            urlRoot: "/admin/activity/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ActivityCollection = Backbone.Collection.extend({
            model: Activity,
            url: "/admin/activity/",
            total: 0,
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Order = Backbone.Model.extend({
            defaults: {
                activity_id: 0,
                activity_name: '',
                goods_quantity: 0,
                total_price: 0,
                buyer: 0,
                lucky_numbers: [],
                status: 0,
                ship_status: 0,
                pay_at: '',
                receipt_address: '',
                goods_price: '',
                goods_id: '',
                source_type: '',
                is_virtual: false,
                extend: ''
            },
            urlRoot: '/admin/order/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var OrderCollection = Backbone.Collection.extend({
            model: Order,
            url: "/admin/order/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var RedEnvelope = Backbone.Model.extend({
            defaults: {
                user_id: 0,
                open_id: '',
                third_id: 0,
                order_id: 0,
                price: 0,
                updated_at: '',
                created_at: ''
            },
            urlRoot: '/admin/order/red_envelope/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var RedEnvelopeCollection = Backbone.Collection.extend({
            model: RedEnvelope,
            url: "/admin/order/red_envelope/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var ChargeCard = Backbone.Model.extend({
            defaults: {
                user_id: 0,
                order_id: '',
                card_info: []
            },
            urlRoot: '/admin/order/charge_card/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var CardStock = Backbone.Model.extend({
            defaults: {
                list: []
            },
            urlRoot: '/admin/goods/stock/',
            parse: function (resp) {
                if (resp.data) {
                    return resp.data;
                }
                return resp;
            }
        });

        var Show = Backbone.Model.extend({
            defaults: {
                template_id: null,
                template_name: '',
                term_number: null,
                order_id: null,
                user_id: null,
                status: 1,
                content: '',
                images: '',
                verify_comment: '',
                verify_award: 0,
                highlight: 0
            },
            urlRoot: "/admin/show/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ShowCollection = Backbone.Collection.extend({
            model: Show,
            url: "/admin/show/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Category = Backbone.Model.extend({
            defaults: {
                name: '',
                icon: '',
                tag: '',
                order: 0,
                created_at: '',
                updated_at: ''
            },
            urlRoot: '/admin/category/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var CategoryCollection = Backbone.Collection.extend({
            model: Category,
            url: '/admin/category/',
            total: 0,
            idNameDct: {},
            parse: function (response) {
                this.total = response.data.total_count;
                var that = this;
                _.each(response.data.list, function (item) {
                    that.idNameDct[item.id] = item.name;
                });
                return response.data.list;
            }
        });

        var Virtual = Backbone.Model.extend({
            defaults: {
                nick_name: '',
                avatar_id: '',
                ip: '',
                phone: '',
                deleted: 0,
                created_at: '',
                updated_at: ''
            },
            urlRoot: '/admin/virtual',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var VirtualCollection = Backbone.Collection.extend({
            model: Virtual,
            url: '/admin/virtual',
            total: 0,
            unused_avatar_count: '',
            parse: function (response) {
                this.total = response.data.total_count;
                this.unused_avatar_count = response.data.unused_avatar_count;
                return response.data.list;
            }
        });

        var CouponTemplate = Backbone.Model.extend({
            defaults : {
                title: "",
                coupon_type: 1,
                desc: "",
                price: 0,
                condition_price: 0,
                valid_ts: 3 * 24 * 60 * 60,
                activity_tids: '',
                activity_categories: '',
                scope_all: 1,
                cmd: '',
                remark: '',
                created_at: '',
                updated_at: ''
            },

            urlRoot: '/admin/coupon/template/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var CouponTemplateCollection = Backbone.Collection.extend({
            model: CouponTemplate,
            url: '/admin/coupon/template/',
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var ABTest = Backbone.Model.extend({
            defaults: {
                name: '',
                created_at: '',
                updated_at: ''
            },
            urlRoot: '/admin/abtest/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ABTestCollection = Backbone.Collection.extend({
            model: ABTest,
            url: '/admin/abtest/',
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Feedback = Backbone.Model.extend({
            defaults: {
                user_id: '',
                nick_name: '',
                qq: '',
                phone: '',
                content: '',
                chn: '',
                cvc: '',
                created_at: '',
                updated_at: ''
            },
            urlRoot: '/admin/feedback/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var FeedbackCollection = Backbone.Collection.extend({
            model: Feedback,
            url: '/admin/feedback/',
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Notification = Backbone.Model.extend({
            defaults: {
                content: {
                    title: '',
                    content: '',
                },
                extend: {
                    filter_list: [],
                    alert: {
                        image: '',
                        cmd: ''
                    }
                },
                status: 0,
                expire_ts: null,
                created_at: '',
                updated_at: ''
            },
            urlRoot: '/admin/notification/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var NotificationCollection = Backbone.Collection.extend({
            model: Notification,
            url: '/admin/notification/',
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        return {
            Template: Template,
            TemplateCollection: TemplateCollection,
            Activity: Activity,
            ActivityCollection: ActivityCollection,
            Order: Order,
            OrderCollection: OrderCollection,
            RedEnvelope: RedEnvelope,
            RedEnvelopeCollection: RedEnvelopeCollection,
            ChargeCard: ChargeCard,
            CardStock: CardStock,
            Show: Show,
            ShowCollection: ShowCollection,
            Category: Category,
            CategoryCollection: CategoryCollection,
            Virtual: Virtual,
            VirtualCollection: VirtualCollection,
            CouponTemplate: CouponTemplate,
            CouponTemplateCollection: CouponTemplateCollection,
            ABTest: ABTest,
            ABTestCollection: ABTestCollection,
            Feedback: Feedback,
            FeedbackCollection: FeedbackCollection,
            Notification: Notification,
            NotificationCollection: NotificationCollection,
        };
    } ();

    var presetModelCls = function () {
        var Preset = Backbone.Model.extend({
            defaults: {
                "device_type": 0,
                "title": '',
                "remark": '',
                "min_version": 0,
                "max_version": null,
                "content": {
                    'notify': {
                        '_disable_activate': false,
                        'wake': [{ //触发性
                            'status': 0, //用户状态 0-安装未注册 1-注册未购买 2-长时间未启动
                            'period': 24, //推送周期，hour
                            'weight': 100,
                            'condition': 1, //状态持续时间，单位：小时
                            'title': '',
                            'content': '',
                            'command': ''
                        }],
                        'activate': [{ //周期性通知
                            'type': 0, //预留
                            'period': 24, //推送周期，hour
                            'time': '22:00', //推送时间点
                            'start_date': '2015-12-08',
                            'end_date': '2015-12-10',
                            'optional': [{
                                'title': '',
                                'content': '',
                                'command': ''
                            }],
                        }]
                    },
                    'scrolling': {
                        'stay': 5,
                        'fetch_interval': 600
                    },
                    'ipay': {
                        "webmode": 0
                    },
                    'theme_config':[{id:'',title:''}],
                    'theme': 0,
                    'homepage_contact': '',
                    'view_config': {
                        'banner': 1,
                        'boldline': 4,
                        'shortcut': 2,
                        'zero_fresh': 0,
                        'revealed': 5
                    }
                }
            },
            urlRoot: "/admin/preset/",
            parse: function (response) {
                if (response.data && response.data.content) {
                    if (!response.data.content.scrolling) {
                        response.data.content.scrolling =
                            this.defaults.content.scrolling;
                    }
                    return response.data;
                }
                return response;
            }
        });
        var PresetCollection = Backbone.Collection.extend({
            model: Preset,
            url: "/admin/preset/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                _.each(response.data.list, function (data) {
                    data.device_type = ADQ.utils.getDeviceTypeStr(data.device_type);
                });
                return response.data.list;
            }
        });

        var Banner = Backbone.Model.extend({
            defaults: {
                "title": "",
                "abtest": -1,
                "start_ts": moment().unix() + 1000,
                "end_ts": moment().unix() + 1000,
                "image": "",
                "cmd": ""
            },
            urlRoot: "/admin/preset/banner/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var BannerCollection = Backbone.Collection.extend({
            model: Banner,
            url: "/admin/preset/banner/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Discovery = Backbone.Model.extend({
            defaults: {
                "start_ts": moment().unix() + 1000,
                "end_ts": moment().unix() + 1000,
                "title": "",
                "desc": "",
                "tag": "",
                "icon": "",
                "cmd": "",
                "abtest": -1
            },
            urlRoot: "/admin/preset/discovery/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var DiscoveryCollection = Backbone.Collection.extend({
            model: Discovery,
            url: "/admin/preset/discovery/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                response.data.list.push({'id': 'group1', 'title': '分组分隔符'});
                response.data.list.push({'id': 'group2', 'title': '分组分隔符'});
                response.data.list.push({'id': 'group3', 'title': '分组分隔符'});
                return response.data.list;
            }
        });

        var Loading = Backbone.Model.extend({
            defaults: {
                "start_date": '',
                "end_date": '',
                "title": "",
                "desc": "",
                "imageUrl": "",
                "command": "",
                "abtest": -1
            },
            urlRoot: "/admin/preset/loading/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var LoadingCollection = Backbone.Collection.extend({
            model: Loading,
            url: "/admin/preset/loading/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Shortcut = Backbone.Model.extend({
            defaults: {
                'icon': '',
                'title': '',
                'command': ''
            },
            urlRoot: "/admin/preset/shortcut/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ShortcutCollection = Backbone.Collection.extend({
            model: Shortcut,
            url: "/admin/preset/shortcut/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        var Theme = Backbone.Model.extend({
            defaults: {
                'title': '',
                'remark': '',
                'start_ts': moment().unix() + 1000,
                'end_ts': moment().unix() + 1000,
                'abtest': -1,
                'content': {
                    theme_color: {},
                    theme_icon: {},
                    main_tab: {
                        item_icon:{
                            main: {}, draw: {}, discover: {}, cart:{}, my: {}
                        }
                    }
                }    
            },
            urlRoot: "/admin/preset/theme/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ThemeCollection = Backbone.Collection.extend({
            model: Theme,
            url: "/admin/preset/theme/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        var Homepage = Backbone.Model.extend({
           defaults: {
               'title': "",
               'abtest': -1,
               'icon': '',
               'cmd': ''
           },
           urlRoot: '/admin/preset/homepage/',
           parse: function (response) {
               if (response.data) {
                   return response.data;
               }
               return response;
           }
        });
        var HomepageCollection = Backbone.Collection.extend({
            model: Homepage,
            url: "/admin/preset/homepage/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                response.data.list.push({'id': 'group1', 'name': '分组用分隔符', 'remark': '分组用分隔符1'});
                response.data.list.push({'id': 'group2', 'name': '分组用分隔符', 'remark': '分组用分隔符2'});
                response.data.list.push({'id': 'group3', 'name': '分组用分隔符', 'remark': '分组用分隔符3'});
                return response.data.list;
            }
        });
        return {
            Preset: Preset,
            PresetCollection: PresetCollection,
            Banner: Banner,
            BannerCollection: BannerCollection,
            Discovery: Discovery,
            DiscoveryCollection: DiscoveryCollection,
            Loading: Loading,
            LoadingCollection: LoadingCollection,
            Shortcut: Shortcut,
            ShortcutCollection: ShortcutCollection,
            Theme: Theme,
            ThemeCollection: ThemeCollection,
            Homepage: Homepage,
            HomepageCollection: HomepageCollection
        }
    } ();

    var statsModelCls = function () {
        var Account = Backbone.Model.extend({
            defaults: {
                id: 0,
                avatar_id: "",
                country: "cn",
                created_at: "",
                updated_at: "",
                phone: "",
                nick_name: "",
                ip: "",
                addr: "",
                is_virtual: false,
                balance: 0,
                active_days: 0,
                user_stats: {
                    chn: "none",
                    aid: "none",
                    pay: {
                        total: 0,
                        count: 0
                    },
                    win: {
                        total: 0,
                        count: 0
                    },
                    recharge: {
                        total: 0
                    }
                },
                daily_stats: {
                    pay: {
                        total: 0,
                        count: 0
                    },
                    win: {
                        total: 0,
                        count: 0
                    },
                    recharge: {
                        total: 0,
                        count: 0
                    }
                }
            },
            urlRoot: "/admin/account/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return this.defaults;
            }
        });
        var AccountCoupon = Backbone.Model.extend({
            defaults: {
                user_id: 0,
                coupon_type: 1,
                title: '',
                desc: '',
                price: 0,
                condition_price: 0,
                status: 1,
                start_ts: '',
                expire_ts: '',
            },
            initialize: function () {
                this.user_id = 1;
            },
            urlRoot: function () {
                return "/admin/" + this.user_id + '/coupon/';
            },
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var AccountCouponCollection = Backbone.Collection.extend({
            model: AccountCoupon,
            initialize: function (options) {
                this.user_id = options.user_id;
            },
            url: function () {
                return "/admin/account/" + this.user_id + '/coupon/';
            },
            total: 0,
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                var list = response.data.list || [];
                return list;
            }
        });
        var AccountTransaction = Backbone.Model.extend({
            defaults: {
                user_id: '',
                type: '',
                title: '',
                price: 0,
                balance: 0.0,
                order_id: '',
                extend: {},
                created_at: '',
                updated_at: '',
                pay_id: '',
                status: ''
            },
            url: function () {
                return "/admin/account/" + this.user_id + '/transaction/';
            },
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        })
        var AccountTransactionCollection = Backbone.Collection.extend({
            model: AccountTransaction,
            initialize: function (options) {
                this.user_id = options.user_id;
            },
            url: function () {
                return "/admin/account/" + this.user_id + "/transaction/";
            },
            total: 0,
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                var list = response.data.list || [];
                return list;
            }
        })
        var Activity = Backbone.Model.extend({
            defaults: {
                id: '',
                name: '',
                price: 1,
                unit: 1,
                status: 1,
                current_amount: 0,
                target_amount: 0,
                virtual_amount: 0,
                buyer_count: 0,
                virtual_count: 0,
                winner: '',
                term_number: 0,
                max_virtual: 0,
                max_real: 0,
                goods_id: 0,
                announced_at: '',
                is_winner_virtual: false,
                winner_buy_count: 1
            },
            urlRoot: "/admin/stats/activity/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ActivityCollection = Backbone.Collection.extend({
            model: Activity,
            url: "/admin/stats/activity/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                this.overview = response.data.overview;
                return response.data.list;
            }
        });
        var Order = Backbone.Model.extend({
            defaults: {
                id: '',
                activity_id: '',
                total_price: 1,
                buyer: 1,
                status: 2,
                pay_at: 0,
                created_at: 0,
                is_virtual: false,
                activity_name: '',
                term_number: 0,
                activity_status: '',
                activity_type: 0,
            },
            urlRoot: "/admin/stats/order/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var OrderCollection = Backbone.Collection.extend({
            model: Order,
            url: "/admin/stats/order/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                this.overview = response.data.overview;
                return response.data.list;
            }
        });
        var Coupon = Backbone.Model.extend({
            defaults: {
                user_id: 0,
                coupon_type: 1,
                desc: '',
                price: 0,
                condition_price: 0,
                title: '',
                status: 0,
                start_ts: 0,
                expire_ts: 0,
                from: '',
                target: ''
            },
            urlRoot: "/admin/stats/coupon/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var CouponCollection = Backbone.Collection.extend({
            model: Coupon,
            url: "/admin/stats/coupon/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                var list = response.data.list || [];
                this.overview = response.data.overview;
                return list;
            }
        });
        var Pay = Backbone.Model.extend({
            defaults: {
                id: '',
                user_id: 0,
                pay_type: 0,
                status: 2,
                price: 0,
                activity_id: 0,
                activity_name: '',
                user_type: 0,
                created_at: '',
                updated_at: '',
            },
            urlRoot: "/admin/stats/pay/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var PayCollection = Backbone.Collection.extend({
            model: Pay,
            url: "/admin/stats/pay/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                this.overview = response.data.overview;
                return response.data.list;
            }
        });
        var Uninstall = Backbone.Model.extend({
            defaults: {
                _id: '',
                total_pay: '',
                uid: '',
                type: '',
                run_count: '',
                created_at: '',
                remove_at: '',
                reason: []
            },
            urlRoot: '/admin/feedback/uninstall/',
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var UninstallCollection = Backbone.Collection.extend({
            model: Uninstall,
            url: '/admin/feedback/uninstall/',
            total: 0,
            overview: {},
            parse: function (response) {
                this.total = response.data.total_count;
                this.overview = response.data.overview;
                return response.data.list;
            }
        });
        return {
            Account: Account,
            AccountCouponCollection: AccountCouponCollection,
            ActivityCollection: ActivityCollection,
            OrderCollection: OrderCollection,
            CouponCollection: CouponCollection,
            PayCollection: PayCollection,
            AccountTransaction: AccountTransaction,
            AccountTransactionCollection: AccountTransactionCollection,
            Uninstall: Uninstall,
            UninstallCollection: UninstallCollection
        };
    } ();

    var vipsModelCls = function () {
        var MissedVips = Backbone.Model.extend({
            defaults: {
                uid: '',
                nick_name: '',
                phone: '',
                chn: '',
                active_days: 0,
                created_time: '',
                updated_time: '',
                lost_days: 3,
                rank: 1,
                recharge_amount: 0,
                pay_count: 0,
                win_count: 0,
                win_amount: 0,
                status: '',
                type: 1,
                user_type: 0,
                back_recharge: 0,
                used_coupon: 0,
                created_at: '',
                updated_at: ''
            },
            urlRoot: "/admin/stats/vips/missed/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var MissedVipsCollection = Backbone.Collection.extend({
            model: MissedVips,
            url: "/admin/stats/vips/missed/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                this.overview = response.data.overview;
                return response.data.list;
            }
        });
        var BackVips = Backbone.Model.extend({
            defaults: {
                call_at: '',
                calc_at: '',
                lost_days: 3,
                total_count: 0,
                back_count: 0,
                back_rate: 0,
                recharge_count: 0,
                recharge_amount: 0,
                recharge_rate: 0,
                recharge_arpu: 0,
                win_count: 0,
                win_amount: 0,
                win_rate: 0,
                coupon_amount: 0,
                pay_count: 0
            },
            urlRoot: "/admin/stats/vips/back/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var BackVipsCollection = Backbone.Collection.extend({
            model: MissedVips,
            url: "/admin/stats/vips/back/",
            total: 0,
            overview: {},
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        var ActiveVips = Backbone.Model.extend({
            defaults: {
                uid: '',
                type: '',
                pay_amount: 3,
                win_count: 0,
                win_amount: 0,
                created_at: '',
                updated_at: '',
                nick_name: 0,
                phone: '',
                created_time: '',
                visit_time: 0,
                add_time: 0,
            },
            urlRoot: "/admin/stats/vips/active/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var ActiveVipsCollection = Backbone.Collection.extend({
            model: ActiveVips,
            url: "/admin/stats/vips/active/",
            total: 0,
            parse: function (response) {
                if (!response.data) {
                    return [];
                }
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        return {
            MissedVips: MissedVips,
            MissedVipsCollection: MissedVipsCollection,
            BackVips: BackVips,
            BackVipsCollection: BackVipsCollection,
            ActiveVips: ActiveVips,
            ActiveVipsCollection: ActiveVipsCollection,
        }
    } ();

    var reportModelCls = function () {
        var UserOverview = Backbone.Model.extend({
            defaults: {
                today: {},
                yesterday: {},
                this_month: {},
                all: {}
            },
            url: "/admin/report/overview/user/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return this.defaults;
            }
        });
        var ActivityOverview = Backbone.Model.extend({
            defaults: {
                today: {},
                yesterday: {},
                this_month: {},
                all: {}
            },
            url: "/admin/report/overview/activity/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return this.defaults;
            }
        });
        var CostOverview = Backbone.Model.extend({
            defaults: {
                today: {},
                yesterday: {},
                this_month: {},
            },
            url: "/admin/report/overview/cost/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return this.defaults;
            }
        });
        var DailyReport = Backbone.Model.extend({
            defaults: {
            },
            url: "/admin/report/daily/",
            list: [],
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                }
                return response.data;
            }
        });
        var RechargeReport = Backbone.Model.extend({
            defaults: {
            },
            url: "/admin/report/daily/recharge/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
            }
        });
        var TacticsReport = Backbone.Model.extend({
            defaults: {
            },
            total: {},
            list: [],
            url: "/admin/report/daily/tactics/",
            parse: function (response) {
                if (response.data) {
                    this.total = response.data.total;
                    this.list = response.data.list;
                    return response.data;
                }
                return this.defaults;
            }
        });
        var CoinReport = Backbone.Model.extend({
            defaults: {
            },
            url: "/admin/report/daily/resource/coin/",
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                    this.gen_dist = response.data.gen_dist;
                    this.cost_dist = response.data.cost_dist;
                    return response.data;
                }
                return this.defaults;
            }
        });
        var CreditReport = Backbone.Model.extend({
            defaults: {
            },
            url: "/admin/report/daily/resource/credit/",
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                    this.gen_dist = response.data.gen_dist;
                    this.cost_dist = response.data.cost_dist;
                    return response.data;
                }
                return this.defaults;
            }
        });
        var CouponReport = Backbone.Model.extend({
            defaults: {
            },
            url: "/admin/report/daily/resource/coupon/",
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                    this.gen_dist = response.data.gen_dist;
                    this.cost_dist = response.data.cost_dist;
                    return response.data;
                }
                return this.defaults;
            }
        });
        var ShippingReport = Backbone.Model.extend({
            default: {},
            url: "/admin/report/daily/shipping/",
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                    this.info = response.data.info;
                    return response.data;
                }
                return this.defaults;
            }
        });
        var Top100List = Backbone.Model.extend({
            defaults: {
            },
            list: [],
            url: "/admin/report/top100/",
            parse: function (response) {
                if (response.data) {
                    this.list = response.data.list;
                    return response.data;
                }
                return this.defaults;
            }
        });

        return {
            UserOverview: UserOverview,
            ActivityOverview: ActivityOverview,
            CostOverview: CostOverview,
            DailyReport: DailyReport,
            RechargeReport: RechargeReport,
            TacticsReport: TacticsReport,
            CoinReport: CoinReport,
            CreditReport: CreditReport,
            CouponReport: CouponReport,
            Top100List: Top100List,
            ShippingReport: ShippingReport,
        };
    } ();

    var consoleModelCls = function () {
        var User = Backbone.Model.extend({
            defaults: {
                "nickname": "",
                "email": "",
                "role": 0,
                "created_at": "",
                "updated_at": ""
            },
            urlRoot: "/admin/user/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var UserCollection = Backbone.Collection.extend({
            model: User,
            url: "/admin/user/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        var Permission = Backbone.Model.extend({
            defaults: {
                "url": "",
                "permission": "",
                "min_role": 0,
                "desc": "",
                "created_at": 1,
                "updated_at": ""
            },
            urlRoot: "/admin/permission/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var PermissionCollection = Backbone.Collection.extend({
            model: Permission,
            url: "/admin/permission/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        var Record = Backbone.Model.extend({
            defaults: {
                "resource": "",
                "resource_id": "",
                "action": 0,
                "content": "",
                "created_at": 1,
            },
            urlRoot: "/admin/record/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var RecordCollection = Backbone.Collection.extend({
            model: Record,
            url: "/admin/record/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        return {
            User: User,
            UserCollection: UserCollection,
            Permission: Permission,
            PermissionCollection: PermissionCollection,
            Record: Record,
            RecordCollection: RecordCollection
        };
    } ();

    var goodsModelCls = function () {
        var Goods = Backbone.Model.extend({
            defaults: {
                name: '',
                price: 0.00,
                unit: 0,
                sold: 0,
                total: 100,
                num: 1,
                source: '',
                extend: '',
                shipping_type: '',
                source_name: '',
                source_type: null,
                category_id: '',
                category_name: [],
                category_path: [],
                brand_id: '',
                brand_name: ''
            },
            urlRoot: "/admin/goods/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var GoodsCollection = Backbone.Collection.extend({
            model: Goods,
            url: "/admin/goods/",
            total: 0,
            stock: [],
            parse: function (response) {
                this.total = response.data.total_count;
                this.stock = response.data.stock;
                return response.data.list;
            }
        });

        var Category = Backbone.Model.extend({
            defaults: {
                name: '',
                parent_id: null,
                created_at: '',
                updated_at: ''
            },
            urlRoot: "/admin/goods/category/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var CategoryCollection = Backbone.Collection.extend({
            model: Category,
            url: "/admin/goods/category/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Source = Backbone.Model.extend({
            defaults: {
                name: '',
                parent_id: null,
                created_at: '',
                updated_at: ''
            },
            urlRoot: "/admin/goods/source/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var SourceCollection = Backbone.Collection.extend({
            model: Source,
            url: "/admin/goods/source/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });

        var Brand = Backbone.Model.extend({
            defaults: {
                name: '',
                parent_id: null,
                created_at: '',
                updated_at: ''
            },
            urlRoot: "/admin/goods/brand/",
            parse: function (response) {
                if (response.data) {
                    return response.data;
                }
                return response;
            }
        });
        var BrandCollection = Backbone.Collection.extend({
            model: Brand,
            url: "/admin/goods/brand/",
            total: 0,
            parse: function (response) {
                this.total = response.data.total_count;
                return response.data.list;
            }
        });
        return {
            Goods: Goods,
            GoodsCollection: GoodsCollection,

            Category: Category,
            CategoryCollection: CategoryCollection,

            Source: Source,
            SourceCollection: SourceCollection,

            Brand: Brand,
            BrandCollection: BrandCollection
        }
    } ();

    var _deleteItem = function (e, collection) {
        var itemId = $(e.currentTarget).closest('tr').data('id'),
            item = collection.get(itemId);
        $.confirm({
            title: '确认操作',
            content: '确认删除ID为' + itemId + '的项么？',
            confirmButton: '确认',
            cancelButton: '取消',
            icon: 'fa fa-warning',
            theme: 'bootstrap',
            backgroundDismiss: true,
            keyboardEnabled: true,
            confirmButtonClass: 'btn-danger',
            confirm: function () {
                item.destroy({
                    success: function () {
                        ADQ.notify.success();
                    },
                    error: function (m, r) {
                        ADQ.notify.notifyResp(r);
                    },
                    wait: true
                });
            },
        });
    };

    var presetViewCls = function () {
        var PresetListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click .add-new': 'createNew',
                'click .clone': 'cloneNew',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.PresetCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            createNew: function (event) {
                return _createOrClone(event, '/admin/preset/');
            },
            cloneNew: function (e) {
                return _createOrClone(e, '/admin/preset/',
                    $(e.currentTarget).closest('tr').data('id'));
            },
            doSearch: function () {
                var searched = {},
                    options = this.options;
                searched.version = parseInt($('#searchVersion').val());
                searched.device_type = parseInt($('#searchDeviceType').val());
                if (!isNaN(searched.version)) {
                    options.version = searched.version;
                }
                options.device_type = searched.device_type;
                ADQ.utils.saveSearched('preset', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    presets: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.preset_searched || '{}')
                }));
                var that = this;
                ADQ.utils.getPaginator(that.options, this.collection.total, '#preset/');
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var _createOrClone = function (event, url, base) {
            event.preventDefault()
            var data = {};
            if (base) {
                data.base = parseInt(base);
            }
            $.post(url, JSON.stringify(data)).fail(function (d) {
                ADQ.notify.notifyResp(d);
            }).done(function (d) {
                ADQ.notify.success();
                setTimeout(function () {
                    location.reload();
                }, 500);
            });
            return false;
        }
        var PresetListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/PresetList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new PresetListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ShortcutPanel = Backbone.View.extend({
            tagName: 'li',
            className: 'dd-item',
            template: 'preset/ShortcutPanel.html',
            events: {
              'click .delete-shortcut': 'deleteShortcut'
            },
            initialize: function (options) {
                // options is shortcutIds...
                this.shortcuts = new presetModelCls.ShortcutCollection();
                this.shortcutIds = options;
                this.collection = new presetModelCls.ShortcutCollection();
                this.collection.bind('change reset', this.renderWithData, this);
            },
            load: function () {
                var that = this;
                this.shortcuts.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        $orderby: 'title'
                    },
                    success: function () {
                        var models = [],
                            m = null;
                        _.each(that.shortcutIds, function (id) {
                            m = that.shortcuts.get(id);
                            if(m)models.push(m);
                        });
                        that.collection.reset(models);
                    }
                });
            },
            render: function () {
                this.$el.html(this.template({
                    shortcuts: this.collection.toJSON(),
                    allShortcuts: this.shortcuts.toJSON()
                }));
                return this;
            },
            deleteShortcut: function (e) {
                e.preventDefault();
                var id = parseInt($(e.target).data('id'));
                this.collection.remove(id);
                this.renderWithData();
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    shortcuts: this.collection.toJSON(),
                    allShortcuts: this.shortcuts.toJSON()
                }));
                var that = this;
                $('#inputShortcut').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                $('#addShortcut').magnificPopup({
                    items: {
                        src: '#addShortcutPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: true,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAddShortcut').off('click').click(function () {
                                var selected = $('#inputShortcut').val();
                                $.magnificPopup.close();
                                _.each(selected, function (s) {
                                    that.collection.add(that.shortcuts.get(s));
                                });
                                that.renderWithData();
                            });
                        },

                    }
                });
                this.$el.find('.image-popup').each(function(i, e){
                    $(e).magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="#preset/shortcut/' + item.el.data('id') +
                                '/" target="_blank">编辑项目</a>';
                        }
                    }
                })});
                this.$el.find('.sortable').each(function (i, e) {
                    $(e).sortable();
                });
                $('.dd').nestable('destroy').nestable();
                return this;
            }
        });
        var BannerPanel = Backbone.View.extend({
            tagName: 'li',
            className: 'dd-item',
            template: 'preset/BannerPanel.html',
            events: {
              'click .delete-banner': 'deleteBanner'
            },
            initialize: function (options) {
                // options is bannerIds...
                this.banners = new presetModelCls.BannerCollection();
                this.bannerIds = options;
                this.collection = new presetModelCls.BannerCollection();
                this.collection.bind('change reset', this.renderWithData, this);
            },
            load: function () {
                var that = this;
                this.banners.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        $orderby: 'title'
                    },
                    success: function () {
                        var models = [],
                            m = null;
                        _.each(that.bannerIds, function (id) {
                            m = that.banners.get(id);
                            if(m)models.push(m);
                        });
                        that.collection.reset(models);
                    }
                });
            },
            render: function () {
                this.$el.html(this.template({
                    banners: this.collection.toJSON(),
                    allBanners: this.banners.toJSON()
                }));
                return this;
            },
            deleteBanner: function (e) {
                e.preventDefault();
                var id = parseInt($(e.target).data('id'));
                this.collection.remove(id);
                this.renderWithData();
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    banners: this.collection.toJSON(),
                    allBanners: this.banners.toJSON()
                }));
                var that = this;
                $('#inputBanner').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                $('#addBanner').magnificPopup({
                    items: {
                        src: '#addBannerPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: true,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAddBanner').off('click').click(function () {
                                var selected = $('#inputBanner').val();
                                $.magnificPopup.close();
                                _.each(selected, function (s) {
                                    that.collection.add(that.banners.get(s));
                                });
                                that.renderWithData();
                            });
                        },

                    }
                });
                this.$el.find('.image-popup').each(function(i, e){
                    $(e).magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="#preset/banner/' + item.el.data('id') +
                                '/" target="_blank">编辑项目</a>';
                        }
                    }
                })});
                this.$el.find('.sortable').each(function (i, e) {
                    $(e).sortable();
                });
                $('.dd').nestable('destroy').nestable();
                return this;
            }
        });
        var DiscoveryPanel = Backbone.View.extend({
            tagName: 'li',
            className: 'dd-item',
            template: 'preset/DiscoveryPanel.html',
            events: {
              'click .delete-discovery': 'deleteDiscovery'
            },
            initialize: function (options) {
                // options is discoveryIds...
                this.discoverys = new presetModelCls.DiscoveryCollection();
                this.discoveryIds = options;
                this.collection = new presetModelCls.DiscoveryCollection();
                this.collection.bind('change reset', this.renderWithData, this);
            },
            load: function () {
                var that = this;
                this.discoverys.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        $orderby: 'title'
                    },
                    success: function () {
                        var models = [],
                            m = null;
                        _.each(that.discoveryIds, function (id) {
                            m = that.discoverys.get(id);
                            if (m) models.push(m);
                        });
                        that.collection.reset(models);
                    }
                });
            },
            render: function () {
                this.$el.html(this.template({
                    discoverys: this.collection.toJSON(),
                    allDiscoverys: this.discoverys.toJSON()
                }));
                return this;
            },
            deleteDiscovery: function (e) {
                e.preventDefault();
                var id = parseInt($(e.target).data('id'));
                this.collection.remove(id);
                this.renderWithData();
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    discoverys: this.collection.toJSON(),
                    allDiscoverys: this.discoverys.toJSON()
                }));
                var that = this;
                $('#inputDiscovery').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                $('#addDiscovery').magnificPopup({
                    items: {
                        src: '#addDiscoveryPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: true,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAddDiscovery').off('click').click(function () {
                                var selected = $('#inputDiscovery').val();
                                $.magnificPopup.close();
                                _.each(selected, function (s) {
                                    that.collection.add(that.discoverys.get(s));
                                });
                                that.renderWithData();
                            });
                        },

                    }
                });
                this.$el.find('.image-popup').each(function(i, e){
                    $(e).magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="#discovery/' + item.el.data('id') +
                                '/" target="_blank">编辑项目</a>';
                        }
                    }
                })});
                this.$el.find('.sortable').each(function (i, e) {
                    $(e).sortable();
                });
                $('.dd').nestable('destroy').nestable();
                return this;
            }
        });
        var LoadingPanel = Backbone.View.extend({
            tagName: 'li',
            className: 'dd-item',
            template: 'preset/LoadingPanel.html',
            events: {
              'click .delete-loading': 'deleteLoading'
            },
            initialize: function (options) {
                // options is loadingIds...
                this.loadings = new presetModelCls.LoadingCollection();
                this.loadingIds = options;
                this.collection = new presetModelCls.LoadingCollection();
                this.collection.bind('change reset', this.renderWithData, this);
            },
            load: function () {
                var that = this;
                this.loadings.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        $orderby: 'title'
                    },
                    success: function () {
                        var models = [],
                            m = null;
                        _.each(that.loadingIds, function (id) {
                            m = that.loadings.get(id);
                            if (m) models.push(m);
                        });
                        that.collection.reset(models);
                    }
                });
            },
            render: function () {
                this.$el.html(this.template({
                    loadings: this.collection.toJSON(),
                    allLoadings: this.loadings.toJSON()
                }));
                return this;
            },
            deleteLoading: function (e) {
                e.preventDefault();
                var id = parseInt($(e.target).data('id'));
                this.collection.remove(id);
                this.renderWithData();
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    loadings: this.collection.toJSON(),
                    allLoadings: this.loadings.toJSON()
                }));
                var that = this;
                $('#inputLoading').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                $('#addLoading').magnificPopup({
                    items: {
                        src: '#addLoadingPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: true,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAddLoading').off('click').click(function () {
                                var selected = $('#inputLoading').val();
                                $.magnificPopup.close();
                                _.each(selected, function (s) {
                                    that.collection.add(that.loadings.get(s));
                                });
                                that.renderWithData();
                            });
                        },

                    }
                });
                this.$el.find('.image-popup').each(function(i, e){
                    $(e).magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="#preset/loading/' + item.el.data('id') +
                                '/" target="_blank">编辑项目</a>';
                        }
                    }
                })});
                this.$el.find('.sortable').each(function (i, e) {
                    $(e).sortable();
                });
                $('.dd').nestable('destroy').nestable();
                return this;
            }
        });
        var HomepagePanel = Backbone.View.extend({
            tagName: 'li',
            className: 'dd-item',
            template: 'preset/HomepagePanel.html',
            events: {
                'click .delete-homepage': 'deleteHomepage'
            },
            initialize: function (options) {
                // options is homepageIds
                this.homepages = new presetModelCls.HomepageCollection();
                this.homepageIds = options;
                this.collection = new presetModelCls.HomepageCollection();
                this.collection.bind('change reset', this.renderWithData, this);
            },
            load: function () {
                var that = this;
                this.homepages.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        $orderby: 'name'
                    },
                    success: function () {
                        var models = [],
                            m = null;
                        _.each(that.homepageIds, function (id) {
                            m = that.homepages.get(id);
                            if (m) models.push(m);
                        });
                        that.collection.reset(models);
                    }
                });
            },
            render: function () {
                this.$el.html(this.template({
                    homepages: this.collection.toJSON(),
                    allHomepages: this.homepages.toJSON(),
                }));
                return this;
            },
            deleteHomepage: function (e) {
                e.preventDefault();
                var id = parseInt($(e.target).data('id'));
                this.collection.remove(id);
                this.renderWithData();
                return false;
            },
            renderWithData: function (e) {
                this.$el.html(this.template({
                    homepages: this.collection.toJSON(),
                    allHomepages: this.homepages.toJSON()
                }));
                var that = this;
                $('#inputHomepage').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200
                });
                $('#addHomepage').magnificPopup({
                    items: {
                        src: '#addHomepagePanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: true,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAddHomepage').off('click').click(function () {
                                var selected = $('#inputHomepage').val();
                                $.magnificPopup.close();
                                _.each(selected, function (s) {
                                    that.collection.add(that.homepages.get(s));
                                });
                                that.renderWithData();
                            });
                        },
                    }
                });
                this.$el.find('.image-popup').each(function (i,e){
                    $(e).magnificPopup({
                        type: 'image',
                        closeOnContentClick: true,
                        mainClass: 'mfp-img-mobile',
                        image: {
                            verticalFit: true,
                            titleSrc: function (item) {
                                return '<a href="#preset/homepage/' + item.el.data('id') + 
                                    '/" target="_blank">编辑项目</a>';
                            }
                        }
                    });
                });
                this.$el.find('.sortable').each(function (i, e) {
                    $(e).sortable();
                });
                $('.dd').nestable('destroy').nestable();
                return this;
            }
        });
        var PannelWrapper = Backbone.View.extend({
            events: {
                'change #inputDeviceType': 'checkIOS',
            },
            template: "preset/PannelWrapper.html",
            initialize: function (options) {
                this.info = options.preset;
                this.theme_config = this.getThemeConfig();
                this.homepage_contacts = {
                    "qq#share#service": "一键加群 &nbsp; 分享夺宝 &nbsp; 我的客服",
                    "qq#service#share": "一键加群 &nbsp; 我的客服 &nbsp; 分享夺宝",
                    "share#qq#service": "分享夺宝 &nbsp; 一键加群 &nbsp; 我的客服",
                    "share#service#qq": "分享夺宝 &nbsp; 我的客服 &nbsp; 一键加群",
                    "service#qq#share": "我的客服 &nbsp; 一键加群 &nbsp; 分享夺宝",
                    "service#share#qq": "我的客服 &nbsp; 分享夺宝 &nbsp; 一键加群",
                    "": "隐藏"
                };   
            },
            render: function () {
                this.$el.html(this.template({
                    info: this.info,
                    theme_config: this.theme_config,
                    homepage_contacts: this.homepage_contacts
                }));
                return this;
            },
            getThemeConfig: function () {
                // 获取所有theme配置
                var theme_config = null;
                $.ajax({
                    type: 'get',
                    async: false,
                    url: '/admin/preset/theme/?$size=100',
                    success: function (data) {
                        theme_config = data.data.list; 
                    }
                });
                return theme_config;
         },
            checkIOS: function (e) {
                var val;
                if (e) {
                    val = ADQ.utils.calcDeviceType($(e.target).val());
                } else {
                    val = this.info['device_type'];
                }
                if (ADQ.utils.isIOS(val)) {
                    $('#iosSpecific').show();
                } else {
                    $('#iosSpecific').hide();
                }
            }
        });
        var PresetDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/PresetDetail.html",
            events: {
                'click #save': 'toSaveOrCreate',
                'click #expandAll': 'expandAll',
                'click #collapseAll': 'collapseAll'
            },
            initialize: function (options) {
                this.model = new presetModelCls.Preset();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('reset change', this.renderWithData, this);
            },
            getInputs: function () {
                var isAllRight = true;
                var _composeJson = function (data, elem) {
                    var $this = $(elem);
                    if ($this.hasClass('placeholder')) return data;
                    if ($this.is('[data-field]')) {
                        var field = $this.data('field');
                        if ($this.is('ol')) {       // key
                            if ($this.data('type') == 'dict') {
                                data[field] = {};
                                $this.children().each(function (i, e) {
                                    _composeJson(data[field], e);
                                });
                            } else if ($this.data('type') == 'flat') {   //flat array
                                var t = [];
                                $this.children().each(function (i, e) {
                                    _composeJson(t, e);
                                });
                                data[field] = t;
                                return data;
                             }else{ //default is array
                                data[field] = [];
                                $this.children().each(function (i, e) {
                                    var t = _composeJson({}, e);
                                    if ( _.isEmpty(t)) {
                                        return data;
                                    }
                                    data[field].push(t);
                                    return data;
                                });
                            }
                        } else {            // value
                            var v = ADQ.utils.getInput(elem);
                            if (v == $this.data('useless')) return data;
                            if (!$this.is('.placeholder') && !ADQ.utils.validElement(elem)) {
                                $this.removeClass("state-success").addClass("state-error");
                                isAllRight = false;
                            }
                            if (_.isArray(data)) data.push(v);
                            else data[field] = v;
                            return data;
                        }
                    } else if ($this.find('[data-field]')) {
                        $this.children().each(function (i, e) {
                            _composeJson(data, e);
                        });
                        return data;
                    }

                    return data;
                };
                var attrs = ADQ.utils.getAllInput('#commAttr');
                attrs.device_type = ADQ.utils.calcDeviceType(attrs.device_type);
                if (!attrs.max_version) attrs.max_version = null;
                attrs.content = {};
                _composeJson(attrs.content, '#root');
                if (!isAllRight) {
                    return null;
                }
                if (!ADQ.utils.isIOS(attrs.device_type)) {
                    delete attrs.content.ipay;
                }
                try{
                    attrs.content.theme = parseInt(attrs.content.theme);
                } catch (e) {
                    console.log(e.message);
                }
                return attrs;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                if (!ADQ.utils.simpleCheck('#commAttr')) {
                    ADQ.notify.error('错误', '输入错误，请检查');
                    return;
                }
                var attrs = this.getInputs();
                if (attrs == null) {
                    this.expandAll();
                    ADQ.notify.error('错误', '输入错误，请检查');
                    return;
                }
                //FIXME: model randomly rollback for some reason to debug
                var href = location.href.split('/');
                this.model.set('id', parseInt(href[href.length - 2]));
                attrs.content.homepage_contact = attrs.homepage_contact;
                attrs.content.view_config = {
                    'zero_fresh': parseInt($('#ViewConfigZeroFresh').val() || 0),
                    'banner': parseInt($('#ViewConfigBanner').val() || 0),
                    'shortcut': parseInt($('#ViewConfigShortcut').val() || 0),
                    'scrolling': parseInt($('#ViewConfigScrolling').val() || 0),
                    'revealed': parseInt($('#ViewConfigRevealed').val() || 0),
                    'boldline': parseInt($('#ViewConfigBoldline').val() || 0),
                };
                delete attrs.content.theme_config;
                delete attrs.homepage_contact;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, data) {
                        ADQ.notify.notifyResp(data);
                    }
                });
                return false;
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                this.load();
                return this;
            },
            expandAll: function () {
                $('.dd').nestable('expandAll');
            },
            collapseAll: function () {
                $('.dd').nestable('collapseAll');
            },
            renderWithData: function () {
                this.$el.html(this.template({}));
                var info = this.model.toJSON(),
                    wrapper = new PannelWrapper({
                        preset: this.model.toJSON()
                    });
                $('#content').append(wrapper.render().el);
                wrapper.checkIOS();

                var shortcut = new ShortcutPanel(info.content.shortcut || []);
                $('#root').append(shortcut.render().el);
                shortcut.load();
                var banner = new BannerPanel(info.content.banner || []);
                $('#root').append(banner.render().el);
                banner.load();
                var discovery = new DiscoveryPanel(info.content.discovery || []);
                $('#root').append(discovery.render().el);
                discovery.load();
                var loading = new LoadingPanel(info.content.pages || []);
                $('#root').append(loading.render().el);
                loading.load();
                var homepage = new HomepagePanel(info.content.homepage || []);
                $('#root').append(homepage.render().el);
                homepage.load();
                $('.multiselect').multiselect();
                return this;
            },
            load: function () {
                var that = this;
                if (this.model.get('id')) {
                    this.model.fetch({
                        reset: true,
                        error: function (data) {
                            ADQ.notify.notifyResp(data);
                        }
                    })
                }else{
                    this.renderWithData();
                }
            }
        });

        var BannerListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.BannerCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            doSearch: function () {
                var searched = {},
                    options = {},
                    now = moment().unix();
                searched.status = parseInt($('#searchStatus').val());
                searched.title = $('#searchTitle').val();
                if (searched.title) {
                    options.title = { $like: searched.title };
                }
                if (searched.status == 1) {         //过期
                    options.end_ts = { "$lt": now };
                } else if (searched.status == 2) {  //生效中
                    options.start_ts = { "$lte": now };
                    options.end_ts = { "$gt": now };
                } else if (searched.status == 3) {  //待生效
                    options.start_ts = { "$gt": now };
                }
                ADQ.utils.saveSearched('banner', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/banner/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    banners: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.banner_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/banner/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/banner/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var BannerListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/BannerList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BannerListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var BannerDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Banner();
                if (options.bannerId) {
                    this.model.set('id', options.bannerId);
                }
                this.abtests = new opModelCls.ABTestCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误，请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content');
                attrs.start_ts = moment(attrs.start_ts).unix();
                attrs.end_ts = moment(attrs.end_ts).unix();
                if (attrs.abtest == -1) attrs.abtest = null;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    abtests: this.abtests.toJSON()
                }));
                $('.multiselect').multiselect();
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                ADQ.utils.getSingleUploader('uploadImage');
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                })
            }
        });
        var BannerDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/BannerDetail.html",
            initialize: function (bannerId) {
                this.bannerId = bannerId;
            },
            render: function () {
                var view = new BannerDetailView(this.bannerId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var DiscoveryListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.DiscoveryCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            doSearch: function () {
                var searched = {},
                    options = {},
                    now = moment().unix();
                searched.title = $('#searchTitle').val();
                if (searched.title) {
                    options.title = { $like: searched.title };
                }
                searched.status = parseInt($('#searchStatus').val());
                if (searched.status == 1) {         //过期
                    options.end_ts = { "$lt": now };
                } else if (searched.status == 2) {  //生效中
                    options.start_ts = { "$lte": now };
                    options.end_ts = { "$gt": now };
                } else if (searched.status == 3) {  //待生效
                    options.start_ts = { "$gt": now };
                }
                ADQ.utils.saveSearched('discovery', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/discovery/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    discoverys: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.discovery_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/discovery/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/discovery/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var DiscoveryListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/DiscoveryList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new DiscoveryListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var DiscoveryDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Discovery();
                if (options.discoveryId) {
                    this.model.set('id', options.discoveryId);
                }
                this.abtests = new opModelCls.ABTestCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误，请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content');
                attrs.start_ts = moment(attrs.start_ts).unix();
                attrs.end_ts = moment(attrs.end_ts).unix();
                if (attrs.abtest == -1) attrs.abtest = null;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    abtests: this.abtests.toJSON()
                }));
                $('.multiselect').multiselect();
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                ADQ.utils.getSingleUploader('uploadIcon');
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                })
            }
        });
        var DiscoveryDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/DiscoveryDetail.html",
            initialize: function (discoveryId) {
                this.discoveryId = discoveryId;
            },
            render: function () {
                var view = new DiscoveryDetailView(this.discoveryId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var LoadingListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.LoadingCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            doSearch: function () {
                var searched = {},
                    options = {},
                    now = moment().format('YYYY-MM-DD');
                searched.status = parseInt($('#searchStatus').val());
                searched.title = $('#searchTitle').val();
                if (searched.title) {
                    options.title = { $like: searched.title };
                }
                if (searched.status == 1) {         //过期
                    options.start_date = { "$lt": now };
                } else if (searched.status == 2) {  //生效中
                    options.start_date = { "$lte": now };
                    options.end_date = { "$gt": now };
                } else if (searched.status == 3) {  //待生效
                    options.start_date = { "$gt": now };
                }
                ADQ.utils.saveSearched('loading', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/loading/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    loadings: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.loading_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/loading/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/loading/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var LoadingListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/LoadingList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new LoadingListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var LoadingDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Loading();
                if (options.loadingId) {
                    this.model.set('id', options.loadingId);
                }
                this.abtests = new opModelCls.ABTestCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误，请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content');
                if (attrs.abtest == -1) attrs.abtest = null;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    abtests: this.abtests.toJSON()
                }));
                $('.multiselect').multiselect();
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                ADQ.utils.getSingleUploader('uploadImage');
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                })
            }
        });
        var LoadingDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/LoadingDetail.html",
            initialize: function (loadingId) {
                this.loadingId = loadingId;
            },
            render: function () {
                var view = new LoadingDetailView(this.loadingId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var ShortcutListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.ShortcutCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            doSearch: function () {
                var searched = {},
                    options = {},
                    now = moment().format('YYYY-MM-DD');
                searched.status = parseInt($('#searchStatus').val());
                searched.title = $('#searchTitle').val();
                if (searched.title) {
                    options.title = { $like: searched.title };
                }
                if (searched.status == 1) {         //过期
                    options.start_date = { "$lt": now };
                } else if (searched.status == 2) {  //生效中
                    options.start_date = { "$lte": now };
                    options.end_date = { "$gt": now };
                } else if (searched.status == 3) {  //待生效
                    options.start_date = { "$gt": now };
                }
                ADQ.utils.saveSearched('shortcut', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/shortcut/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    shortcuts: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.shortcut_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/shortcut/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/shortcut/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var ShortcutListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/ShortcutList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ShortcutListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ShortcutDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Shortcut();
                if (options.shortcutId) {
                    this.model.set('id', options.shortcutId);
                }
                this.abtests = new opModelCls.ABTestCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误，请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content');
                if (attrs.abtest == -1) attrs.abtest = null;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    abtests: this.abtests.toJSON()
                }));
                $('.multiselect').multiselect();
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                ADQ.utils.getSingleUploader('uploadImage');
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                })
            }
        });
        var ShortcutDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/ShortcutDetail.html",
            initialize: function (shortcutId) {
                this.shortcutId = shortcutId;
            },
            render: function () {
                var view = new ShortcutDetailView(this.shortcutId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ThemeListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click .clone': 'cloneNew',
                'click #search': 'doSearch'
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.ThemeCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            cloneNew: function (e) {
                return _createOrClone(event, '/admin/preset/theme/',
                $(e.currentTarget).closest('tr').data('id'));  
            },
            doSearch: function () {
                var searched = {},
                    options = {},
                    now = moment().format('YYYY-MM-DD');
                searched.status = parseInt($('#searchStatus').val());
                searched.title = $('#searchTitle').val();
                if (searched.title) {
                    options.title = { $like: searched.title };
                }
                if (searched.status == 1) { // 过期
                    options.end_ts = { "$lt": now};
                } else if (searched.status == 2) { // 生效中
                    options.start_ts = { "$lte": now};
                    options.end_ts = { "$gt": now};
                } else if (searched.status == 3) {  // 待生效
                    options.start_ts = { "$gt": now};
                }
                ADQ.utils.saveSearched('theme', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/theme/', options),{
                    trigger: true
                })
            },
            renderWithData: function () {
               this.$el.html(this.template({
                   themes: this.collection.toJSON(),
                   searched: JSON.parse(localStorage.theme_searched || '{}')
               }));
               var that = this;
               ADQ.utils.renderTable('main-list', {
                   $orderby: that.options.$orderby || 'id',
                   sortCallback: function (field) {
                       that.options.$orderby = field;
                       that.options.$pate = 1;
                       var newUrl = ADQ.utils.composeQueryString('#preset/theme/', that.options);
                       app.navigate(newUrl, {
                           trigger: true
                       });
                   }
               });
               ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/theme/');
               return this;
           },
           load: function () {
               this.collection.fetch({
                   reset: true,
                   data: this.options,
                   error: function (c, r, o) {
                       ADQ.notify.notifyResp(r);
                       $('#content').append('<h4 class="text-muted">无数据</h4>');
                   },
               });
           }
        });
        var ThemeListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "preset/ThemeList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ThemeListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ThemeDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Theme();
                if (options.themeId) {
                    this.model.set('id', options.themeId);
                }
                this.abtests = new opModelCls.ABTestCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误,请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content')
                attrs.start_ts = moment(attrs.start_ts).unix();
                attrs.end_ts = moment(attrs.end_ts).unix();
                if (attrs.abtest == -1) attrs.abtest = null;
                var theme_color = {
                    global_theme_color: attrs.global_theme_color,
                    global_theme_text_color: attrs.global_theme_text_color,
                    title_bar_bg_color: attrs.title_bar_bg_color,
                    title_bar_text_color: attrs.title_bar_text_color,
                    global_text_blue_color: attrs.global_text_blue_color,
                    user_center_top_bg_color: attrs.user_center_top_bg_color,
                    my_profile_top_bg_color: attrs.my_profile_top_bg_color,
                    progress_bar_light_color: attrs.progress_bar_light_color,
                    revealed_count_down_text_color: attrs.revealed_count_down_text_color,
                    zero_fresh_count_down_text_color: attrs.zero_fresh_count_down_text_color,
                    hight_light_button_bg_color: attrs.hight_light_button_bg_color,
                    hight_light_button_text_color: attrs.hight_light_button_text_color,
                };
                var theme_icon = {
                    main_title_category_icon: attrs.main_title_category_icon,
                    main_title_search_icon: attrs.main_title_search_icon,
                    check_box_check_icon: attrs.check_box_check_icon,
                    check_box_uncheck_icon: attrs.check_box_uncheck_icon,
                    title_bar_back_icon: attrs.title_bar_back_icon,
                    title_bar_tips_icon: attrs.title_bar_tips_icon,
                    title_bar_share_icon: attrs.title_bar_share_icon
                };
                var main_tab = {
                    text_normal_color: attrs.text_normal_color,
                    text_select_color: attrs.text_select_color,
                    item_icon:{
                        main: {
                            normal: attrs['main-normal'],
                            press: attrs['main-press']
                        },
                        draw: {
                            normal: attrs['draw-normal'],
                            press: attrs['draw-press']
                        },
                        discover: {
                            normal: attrs['discover-normal'],
                            press: attrs['discover-press']
                        },
                        cart: {
                            normal: attrs['cart-normal'],
                            press: attrs['cart-press']
                        },
                        my: {
                            normal: attrs['my-normal'],
                            press: attrs['my-press']
                        }
                    }
                };
                attrs.content =JSON.stringify({
                    theme_color: theme_color,
                    theme_icon: theme_icon,
                    main_tab: main_tab
                });
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功!');
                        setTimeout(function () {
                            history.back();
                        },500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                try {
                    this.$el.html(this.template({
                        info: this.model.toJSON(),
                        abtests: this.abtests.toJSON(),
                    }));
                } catch (error) {
                    console.log(error.message);
                }
                var that = this;
                $('.multiselect').multiselect();
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                for(var i=1;i<18;i++){
                    ADQ.utils.getSingleUploader('uploadImg' + i);
                }
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                });
            }
        });
        var ThemeDetailPage = Backbone.View.extend({
            el: '#content_wrapper',
            template: "preset/ThemeDetail.html",
            initialize: function (themeId) {
                this.themeId = themeId;
            },
            render: function () {
                var view = new ThemeDetailView(this.themeId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var HomepageListView = Backbone.View.extend({
            tagName: 'div',
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new presetModelCls.HomepageCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            doSearch: function () {
                var searched = {},
                    options = {};
                searched.title = $('#searchTitle').val();
                if(searched.title) {
                    options.title = { $like: searched.title };
                }
                ADQ.utils.saveSearched('homepage', searched);
                app.navigate(ADQ.utils.composeQueryString('#preset/homepage/',options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    homepages: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.homepage_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#preset/homepage', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#preset/homepage/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    }
                });
            }

        });
        var HomepageListPage = Backbone.View.extend({
            el: '#content_wrapper',
            template: 'preset/HomepageList.html',
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new HomepageListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });
        var HomepageDetailView = Backbone.View.extend({
            tagName: 'div',
            className: 'panel-body pn',
            events: {
                'click #save': 'toSaveOrCreate',
            },
            initialize: function (options) {
                this.model = new presetModelCls.Homepage();
                this.abtests = new opModelCls.ABTestCollection();
                this.types = {'0': '无', '1': '小圆点', '2': '左边文字', '3': '右边文字', '4': '有背景色'};
                if (options.homepageId) {
                    this.model.set('id', options.homepageId);
                 }
                this.model.bind('change reset', this.renderWithData, this);
                this.abtests.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误,请检验');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content');
                if (attrs.abtest == -1) attrs.abtest = null;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        },  500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    abtests: this.abtests.toJSON(),
                    types: this.types
                }));
                $('.multiselect').multiselect();
                $('.image-popup').magnificPopup({
                    type: 'iamge',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') + 
                            '"target="_blank">查看原图</a>';
                        }
                    }
                });
                ADQ.utils.getSingleUploader('uploadImage');
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.abtests.fetch({
                    reset: true,
                    $size: -1
                });
            }
        });
        var HomepageDetailPage = Backbone.View.extend({
            el: '#content_wrapper',
            template: 'preset/HomepageDetail.html',
            initialize: function (homepageId) {
                this.homepageId = homepageId;
            },
            render: function () {
                var view = new HomepageDetailView(this.homepageId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        return {
            ShortcutPanel: ShortcutPanel,
            BannerPanel: BannerPanel,
            DiscoveryPanel: DiscoveryPanel,
            LoadingPanel: LoadingPanel,
            HomepagePanel: HomepagePanel,
            PannelWrapper: PannelWrapper,
            PresetListPage: PresetListPage,
            PresetDetailPage: PresetDetailPage,

            BannerListPage: BannerListPage,
            BannerDetailPage: BannerDetailPage,

            DiscoveryListPage: DiscoveryListPage,
            DiscoveryDetailPage: DiscoveryDetailPage,

            LoadingListPage: LoadingListPage,
            LoadingDetailPage: LoadingDetailPage,

            ShortcutListPage: ShortcutListPage,
            ShortcutDetailPage: ShortcutDetailPage,

            ThemeListPage: ThemeListPage,
            ThemeDetailPage: ThemeDetailPage,

            HomepageListPage: HomepageListPage,
            HomepageDetailPage: HomepageDetailPage
        }
    } ();

    var goodsViewCls = function () {
        var GoodsListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new goodsModelCls.GoodsCollection();
                this.sourceType = new goodsModelCls.SourceCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
                this.sourceType.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.idOrName = $('#searchIdOrName').val();
                searched.shipping_type = parseInt($('#searchShippingType').val());
                searched.source_type = parseInt($('#searchSourceType').val());
                var id = Number(searched.idOrName);
                if (isNaN(id)) {
                    options.name = {
                        '$like': searched.idOrName
                    };
                } else if (id) {
                    options.id = id;
                }
                if (searched.shipping_type != -1) {
                    options.shipping_type = searched.shipping_type;
                }
                if (searched.source_type != -1) {
                    options.source_type = searched.source_type;
                }
                ADQ.utils.saveSearched('goods', searched);
                app.navigate(ADQ.utils.composeQueryString('#goods/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    stock: this.collection.stock,
                    sourceCollection: this.sourceType,
                    searched: JSON.parse(localStorage.goods_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#goods/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#goods/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.sourceType.fetch({
                    reset: true,
                    $size: -1
                })
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var GoodsListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "goods/GoodsList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new GoodsListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var GoodsDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #goodsSave': 'toSaveOrCreate',
                'change select': 'calcCost',
                'blur #inputPrice': 'calcCost'
            },
            initialize: function (options) {
                this.model = new goodsModelCls.Goods();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.counter = 0;
                this.brands = new goodsModelCls.BrandCollection();
                this.sourceTypes = new goodsModelCls.SourceCollection();
                this.model.bind('change reset', this.renderWithData, this);
                this.brands.bind('reset', this.renderWithData, this);
                this.sourceTypes.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            calcCost: function(){
                var price = parseFloat($('#inputPrice').val()),
                    source_type = parseInt($('#inputSourceType').val()),
                    shipping_type = parseInt($('#inputShippingType').val()),
                    freight = 0,
                    tax = 0;
                if (shipping_type != 0) {
                    $('#inputTax').html('0%');
                    $('#inputFreight').html(0);
                    $('#inputCost').html(price);
                } else {
                    if (source_type == 1 || source_type == 6) {
                        $('#inputTax').html('0%');
                        freight = price < 99 ? 10 : 0;
                        $('#inputFreight').html(freight);
                        $('#inputCost').html(price + freight);
                    } else {
                        $('#inputTax').html('6%');
                        $('#inputFreight').html(10);
                        $('#inputCost').html((price * (1 + 0.06) + 10).toFixed(2));
                    }
                }
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                if (!ADQ.utils.simpleCheck('#goods-form')) {
                    ADQ.notify.error('错误', "输入错误，请检验");
                    return;
                }
                var data = ADQ.utils.getAllInput('#goods-form'),
                    category_path = _getCategoryPath(),
                    origin_id = this.model.get('category_id');
                if (!category_path) {
                    data.category_id = null;
                    data.category_path = [];
                }else if (origin_id == null || origin_id != category_path[category_path.length - 1]) {
                    data.category_id = category_path.length > 0 ? category_path[category_path.length - 1] : null;
                    data.category_path = category_path;
                }
                this.model.save(data, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderAfterLoad: function () {
                var param = this.model.get('id') ? { 'category_path': this.model.get('category_path') } : {};
                param.hide_goods = true;
                this.chooserView = new ChooserWidgetView(param);
                $('#goods-form').prepend(this.chooserView.render().el);
                this.chooserView.load();
                this.calcCost();
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    sourceTypes: this.sourceTypes.toJSON(),
                    brands: this.brands.toJSON()
                }));
                this.counter += 1;
                if (this.counter >= 3) {
                    this.renderAfterLoad();
                }
                return this;
            },
            load: function () {
                this.sourceTypes.fetch({
                    reset: true,
                    $size: -1
                });
                this.brands.fetch({
                    reset: true,
                    $size: -1
                });
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
            }
        });
        var GoodsDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "goods/GoodsDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new GoodsDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var ChooserWidgetView = Backbone.View.extend({
            tagName: "div",
            events: {
                'change .category-select': 'changeCategory',
                'change #inputGoods': 'changeGoods'
            },
            template: "goods/ChooserWidget.html",
            initialize: function (options) {
                this.options = options;
                this.category_path = options.category_path || [];
                this.hide_goods = options.hide_goods;
                this.tree = [];
                var that = this;
                _.each(this.category_path, function () {
                    that.tree.push(new goodsModelCls.CategoryCollection());
                });
                if (this.tree.length == 0) {
                    this.tree.push(new goodsModelCls.CategoryCollection());
                }
                _.each(this.tree, function (c) {
                    c.bind('change reset', that.renderWithData, that);
                });
                if (!this.hide_goods) {
                    this.goods_id = options.goods_id;
                    this.goodsList = new goodsModelCls.GoodsCollection();
                    this.goodsList.bind('change reset', this.renderWithData, this);
                }
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            changeGoods: function () {
                this.goods_id = $('#inputGoods').val();
            },
            reloadGoods: function () {
                var category_id = $('.category-select:last').val();
                this.goodsList.fetch({
                    reset: true,
                    data: { category_id: parseInt(category_id), $size: -1 },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            },
            changeCategory: function (e) {
                var parent_id = parseInt($(e.target).val()),
                    level = parseInt($(e.target).data('level')),
                    c = new goodsModelCls.CategoryCollection(),
                    that = this;
                this.category_path[level] = parent_id;
                this.category_path = this.category_path.slice(0, level + 1);
                this.goods_id = null;
                for (var i = level + 1; i < this.tree.length; ++i){
                    this.tree[i].off();
                }
                this.tree = this.tree.slice(0, level + 1);
                this.tree.push(c);
                c.bind('change reset', this.renderWithData, this);
                c.fetch({
                    data: { parent_id: parent_id, $size: -1},
                    reset: true,
                    success: function (c, r, o) {
                        if (c.length == 0 && !that.hide_goods) {
                            that.reloadGoods();
                        }
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    tree: this.tree,
                    goods_id: this.goods_id,
                    goodsModels: this.hide_goods ? [] : this.goodsList.models,
                    category: this.category_path
                }));
                $('.search-select').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                if (this.hide_goods) {
                    $('#goodsChooser').hide();
                }
                if (this.renderCallback) {
                    this.renderCallback();
                }
                return this;
            },
            load: function (callback) {
                var that = this;
                _.each(this.tree, function (c, index) {
                    var parent_id = index ? that.category_path[index - 1] : '$null';
                    c.fetch({
                        data: { parent_id: parent_id, $size: -1 },
                        reset: true,
                        error: function (c, r, o) {
                            ADQ.notify.notifyResp(r);
                        },
                    })
                });
                if (this.goodsList && this.category_path.length > 0) {
                    this.goodsList.fetch({
                        data: { category_id: this.category_path[this.category_path.length - 1] },
                        reset: true,
                        error: function (c, r, o) {
                            ADQ.notify.notifyResp(r);
                        },
                    })
                }
                if (callback) that.renderCallback=callback;
            }
        });
        var _getCategoryPath = function () {
            var path = [];
            $('.category-select').each(function () {
                var val = parseInt($(this).val());
                if (!isNaN(val)) {
                    path[$(this).data('level')] = val;
                } else {
                    return path;
                }
            })
            return path;
        };

        var CategoryListView = Backbone.View.extend({
            tagName: "div",
            events: {
                "click .delete-item": "deleteItem",
            },
            initialize: function (options) {;
                this.options = options;
                this.collection = new goodsModelCls.CategoryCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
                this.parent = new goodsModelCls.Category();
                if (this.options.parent_id != '$null') {
                    this.parent.set('id', this.options.parent_id);
                    this.parent.fetch({ reset: true });
                }
                this.parent.bind('reset', this.renderWithData);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            deleteItem: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    parent: this.parent.toJSON()
                }));
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var CategoryListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "goods/CategoryList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CategoryListView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });
        var CategoryDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': "save"
            },
            initialize: function (options) {
                this.model = new goodsModelCls.Category();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                if (this.model.get('id')) {
                    this.model.fetch({
                        reset: true
                    })
                } else {
                    this.renderWithData();
                }
            },
            save: function () {
                if (!ADQ.utils.simpleCheck()) {
                    ADQ.notify.failed('错误', '请检测输入...');
                    return;
                }
                var data = ADQ.utils.getAllInput(),
                    category_path = _getCategoryPath(),
                    origin_id = this.model.get('parent_id');
                if (origin_id == 0 || origin_id != category_path[category_path.length - 1]) {
                    data.parent_id = category_path[category_path.length - 1];
                }
                data.category_path = category_path;
                this.model.save(data, {
                    patch: true,
                    success: function (m, r, o) {
                        ADQ.notify.success();
                        setTimeout(function() {
                            history.back();
                        }, 500);
                    },
                    error: function (m, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                }));
                var param = this.model.get('id') ? { 'category_path': this.model.get('category_path') } : {};
                param.hide_goods = true;
                this.chooserView = new ChooserWidgetView(param);
                $('#category-form').prepend(this.chooserView.render().el);
                this.chooserView.load(function () {
                    $('#categoryChooser').html('父分类:');
                });
                ADQ.utils.getSingleUploader('uploadIcon');
                return this;
            }
        });
        var CategoryDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: 'goods/CategoryDetail.html',
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CategoryDetailView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });

        var BrandListView = Backbone.View.extend({
            tagName: "div",
            events: {
                "click .delete-item": "deleteItem"
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new goodsModelCls.BrandCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            deleteItem: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || '-updated_at',
                    sortCallback: function(field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#goods/brand/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#goods/brand/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var BrandListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "goods/BrandList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BrandListView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });
        var BrandDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': "save"
            },
            initialize: function (options) {
                this.model = new goodsModelCls.Brand();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                if (this.model.get('id')) {
                    this.model.fetch({
                        reset: true
                    })
                } else {
                    this.renderWithData();
                }
            },
            save: function () {
                if (!ADQ.utils.simpleCheck()) {
                    ADQ.notify.failed('错误', '请检测输入...');
                    return;
                }
                var data = ADQ.utils.getAllInput('#form');
                this.model.save(data, {
                    patch: true,
                    success: function (m, r, o) {
                        ADQ.notify.success();
                        setTimeout(function() {
                            history.back();
                        }, 500);
                    },
                    error: function (m, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                }));
                return this;
            }
        });
        var BrandDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: 'goods/BrandDetail.html',
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BrandDetailView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });

        var SourceListView = Backbone.View.extend({
            tagName: "div",
            events: {
                "click .delete-item": "deleteItem"
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new goodsModelCls.SourceCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            deleteItem: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || '-updated_at',
                    sortCallback: function(field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#goods/source/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#goods/source/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var SourceListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "goods/SourceList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new SourceListView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });
        var SourceDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': "save"
            },
            initialize: function (options) {
                this.model = new goodsModelCls.Source();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                if (this.model.get('id')) {
                    this.model.fetch({
                        reset: true
                    })
                } else {
                    this.renderWithData();
                }
            },
            save: function () {
                if (!ADQ.utils.simpleCheck()) {
                    ADQ.notify.failed('错误', '请检测输入...');
                    return;
                }
                var data = ADQ.utils.getAllInput('#form');
                this.model.save(data, {
                    patch: true,
                    success: function (m, r, o) {
                        ADQ.notify.success();
                        setTimeout(function() {
                            history.back();
                        }, 500);
                    },
                    error: function (m, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                }));
                return this;
            }
        });
        var SourceDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: 'goods/SourceDetail.html',
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new SourceDetailView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });

        return {
            GoodsListPage: GoodsListPage,
            GoodsDetailPage: GoodsDetailPage,
            ChooserWidgetView: ChooserWidgetView,

            CategoryListPage: CategoryListPage,
            CategoryDetailPage: CategoryDetailPage,

            BrandListPage: BrandListPage,
            BrandDetailPage: BrandDetailPage,

            SourceListPage: SourceListPage,
            SourceDetailPage: SourceDetailPage
        }
    } ();

    var opViewCls = function () {
        var TemplateListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.TemplateCollection();
                this.categorys = new opModelCls.CategoryCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
                this.categorys.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.idOrName = $('#searchIdOrName').val();
                searched.status = parseInt($('#searchStatus').val());
                searched.type = parseInt($('#searchType').val());
                searched.category = parseInt($('#searchCategory').val());
                searched.price_lower = parseInt($('#searchPriceLower').val());
                searched.price_upper = parseInt($('#searchPriceUpper').val());
                var id = Number(searched.idOrName);
                if (isNaN(id)) {
                    options.name = {
                        '$like': searched.idOrName
                    };
                } else if (id) {
                    options.id = id;
                }
                if (searched.type === 0) {
                    options.price = 0;
                } else if (searched.type != -1) {
                    options.unit = searched.type;
                }
                if (searched.status != -1) {
                    options.status = searched.status;
                }
                if (searched.category != -1) {
                    options.category_id = searched.category;
                }
                if (searched.price_lower || searched.price_upper) {
                    options.target_amount = {};
                    if (searched.price_lower) options.target_amount.$gte = searched.price_lower;
                    if (searched.price_upper) options.target_amount.$lte = searched.price_upper;
                }
                ADQ.utils.saveSearched('template', searched);
                app.navigate(ADQ.utils.composeQueryString('#template/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    categoryDct: this.categorys.idNameDct,
                    status: TEMPLATE_STATUS,
                    countrys: COUNTRY_CODE,
                    categorys: this.categorys.models,
                    searched: JSON.parse(localStorage.template_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('template-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#template/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#template/');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.categorys.fetch({
                    reset: true,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var TemplateListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/TemplateList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new TemplateListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var TemplateDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click a.template-save': "toSaveOrCreate",
                'click a.delete-image': "deleteImage",
                'change #inputPK': "changeMode",
                'blur #inputTargetAmount': "changeMode",
            },

            initialize: function (options) {
                this.templateID = options.templateID;
                this.goodsList = new goodsModelCls.GoodsCollection();
                this.categorys = new opModelCls.CategoryCollection();
                this.deletedImages = [];
                this.cachedImages = [];
                this.model = new opModelCls.Template();
                if (this.templateID != null) {
                    this.model.set('id', this.templateID);
                }
                this.model.bind('change', this.renderWithData, this);
                this.goodsList.bind('change reset', this.renderWithData, this);
                this.categorys.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.categorys.fetch({
                    reset: true,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
                this.goodsList.fetch({
                    reset: true,
                    data: {
                        "$size": -1,
                        "$orderby": "-id"
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
                if (this.templateID != null) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
            },
            changeMode: function () {
                if ($('#inputPK').val() > 0) {
                    var pk = parseInt($('#inputPK').val()),
                        target_amount = parseInt($('#inputTargetAmount').val()),
                        limit = target_amount / pk;
                    if (!Number.isInteger(limit)) {
                        ADQ.notify.warning('注意', '目标次数必须是pk人数的整数倍');
                        limit = Math.round(limit);
                    }
                    $('#inputBuyLimit').val(limit).prop('disabled', true);
                    $('#inputUnit').val(limit).prop('disabled', true);
                } else {
                    $('#inputBuyLimit').val(0).prop('disabled', false);
                    $('#inputUnit').val(1).prop('disabled', false);
                }
            },
            _getCurrentInputs: function () {
                var category_ids = $('#inputCategory').val() || [],
                    cids = [];
                _.each(category_ids, function (category_id) {
                    cids.push(parseInt(category_id, 10));
                });

                var data = {
                    'name': $('#inputName').val(),
                    'short_title': $('#inputShortName').val(),
                    'desc': $('#inputDesc').val(),
                    'images': this.getImages(),
                    'cover': $('#cover').attr('src') || '',
                    'price': parseInt($('#inputPrice').val()),
                    'goods_id': parseInt($('#inputGoodsId').val()),
                    'unit': parseInt($('#inputUnit').val()),
                    'category_ids': cids,
                    'country': $('#inputCountry').val(),
                    'target_amount': parseInt($('#inputTargetAmount').val()),
                    'status': parseInt($('#inputStatus').val()),
                    'graphics': this.getGraphics(),
                    'weight': parseInt($('#inputWeight').val()),
                    'buy_limit': parseInt($('#inputBuyLimit').val()),
                    'pk': parseInt($('#inputPK').val()),
                };
                return data;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                if (!$('#template-form').valid()) {
                    ADQ.notify.error('错误', "输入错误，请检验");
                    return;
                } else if ($('#inputGoodsId').val() == null) {
                    ADQ.notify.error('错误', '请选择商品');
                    return;
                } else if (parseInt($('#inputGoodsId').val()) < 0) {
                    ADQ.notify.error('错误', '请先添加商品再创建活动');
                    return;
                } else if ($('#inputShortName').val().length > 50) {
                    ADQ.notify.error('错误', '商品简称长度超过50个字符');
                    return;
                }
                var attrs = this._getCurrentInputs();
                if (attrs.unit != 0 && attrs.target_amount % attrs.unit != 0) {
                    ADQ.notify.error('错误', '目标数量必须是购买单位的整数倍');
                    return;
                }
                if (attrs.pk > 0 && !Number.isInteger(attrs.target_amount / attrs.pk)) {
                    ADQ.notify.error('错误', '目标数量必须是PK人数的整数倍');
                    return;
                }
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        if (response.status == 201) {
                            ADQ.notify.warning('警告', '保存成功，但商品库存不足，无法开始活动!');
                        } else {
                            ADQ.notify.notifyResp(response);
                        }
                    }
                });
                // if (this.deletedImages.length > 0)
                //     $.post('admin/image/delete/', {
                //         urls: this.deletedImages.join(',')
                //     }).done(function() {
                this.deletedImages = [];
                // });
                return false;
            },
            _getPics: function (divId) {
                var imgs = [];
                $('#' + divId + ' div img').each(function () {
                    var src = $(this).attr('src');
                    if (src) imgs.push(src);
                });
                $.merge(imgs, this.cachedImages);
                return imgs.join(',');
            },
            getImages: function () {
                return this._getPics('covers');
            },
            getGraphics: function () {
                return this._getPics('graphics');
            },
            addCovers: function () {
                this.model.set('images', this.getImages());
                this.cachedImages = [];
                $.magnificPopup.close();
            },
            addGraphics: function () {
                this.model.set('graphics', this.getGraphics());
                this.cachedImages = [];
                $.magnificPopup.close();
            },
            deleteImage: function (e) {
                e.preventDefault();
                var url = $(e.currentTarget).next('a').attr('href');
                $(e.currentTarget).parents('div.thumb').remove();
                this.deletedImages.push(url);
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    categorys: this.categorys.models,
                    goodsList: this.goodsList.models
                }));
                $('.sortable').sortable();
                $('.sortable').disableSelection();
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                $('.thumb').hover(function () {
                    $(this).children("a.close").toggle();
                });
                ADQ.utils.getValidator('#template-form');
                $('.search-select').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                if (this.model.get('images')) {
                    $('#covers').show();
                } else {
                    $('#covers').hide();
                }
                if (this.model.get('graphics')) {
                    $('#graphics').show();
                } else {
                    $('#graphics').hide();
                }
                var that = this;
                ADQ.utils.getSingleUploader('uploadCover', function (url) {
                    var cover = that.model.get('cover');
                    if (cover) that.deletedImages.push(that.model.get('cover'));
                    var k = that._getCurrentInputs();
                    k.cover = url;
                    that.model.set(k);
                });
                $('.btn-upload').magnificPopup({
                    items: {
                        src: '#uploadImagePanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    // showCloseBtn: false,
                    callbacks: {
                        beforeOpen: function () {
                            that.model.set(that._getCurrentInputs());
                            ADQ.utils.getUploader('pickfiles', 'fsUploadProgress', function (url) {
                                that.cachedImages.push(url);
                            });
                            $('#addCachedImgs').off('click').click(function () {
                                var magnificPopup = $.magnificPopup.instance,
                                    btnId = magnificPopup.st.el.attr('id');
                                if (btnId == 'uploadCovers')
                                    that.addCovers();
                                else
                                    that.addGraphics();
                            });
                        }
                    }
                });
                return this;
            },
        });
        var TemplateDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/TemplateDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new TemplateDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var FeedbackListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click #export': 'export',
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.FeedbackCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            _getSearchOption: function () {
                var searched = {},
                    options = {};
                searched.created_at_lower = $('#searchCreatedAtLower').val();
                searched.created_at_upper = $('#searchCreatedAtUpper').val();
                if (searched.created_at_lower || searched.created_at_upper) {
                    options.created_at = {};
                    if (searched.created_at_lower) options.created_at.$gte = searched.created_at_lower;
                    if (searched.created_at_upper) options.created_at.$lt = searched.created_at_upper;
                }
                ADQ.utils.saveSearched('feedback', searched);
                return options;
            },
            doSearch: function () {
                var options = this._getSearchOption();
                app.navigate(ADQ.utils.composeQueryString('#feedback/', options), {
                    trigger: true
                });
            },
            export: function () {
                ADQ.notify.warning('警告', '导出中，请等待...');
                var options = this._getSearchOption();
                ADQ.exportData(this.collection.url, options);
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    searched: JSON.parse(localStorage.feedback_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#feedback/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('[data-type="date"]').datetimepicker({
                    format: 'YYYY-MM-DD',
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#feedback/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var FeedbackListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/FeedbackList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new FeedbackListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var OrderListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch',
                'click #export': 'export',
                'click #autoShip': 'autoShip',
                'click .shortcut': 'changeSearchId',
                'click #switchSearchTime': 'changeSearchTime',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.OrderCollection();
                this.sources = new goodsModelCls.SourceCollection();
                this.brands = new goodsModelCls.BrandCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
                this.sources.bind('reset', this.renderWithData, this);
                this.brands.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            changeSearchId: function (e) {
                e.preventDefault();
                var $item = $(e.target),
                    key = $item.data('aria'),
                    tips = $item.html();
                $('#searchId').data('field', key).attr('placeholder', tips).val('');
                $('[data-toggle="dropdown"]').parent().removeClass('open');
                return false;
            },
            changeSearchTime: function () {
                var $item = $('#switchSearchTime');
                if ($item.html() == '领奖时间(点击切换)') {
                    $item.html('发货时间(点击切换)');
                    $('#searchSendTime').show();
                    $('#searchAwardTime').hide().find('input').each(function () { $(this).val(''); });
                } else {
                    $item.html('领奖时间(点击切换)');
                    $('#searchAwardTime').show();
                    $('#searchSendTime').hide().find('input').each(function () { $(this).val(''); });
                }
            },
            autoShip: function () {
                var ids = this.collection.pluck('id');
                if (ids.length == 0) return;
                ADQ.notify.warning('警告', '发货中，请等待...');
                $.post(this.collection.url, JSON.stringify({ order_ids: ids })).done(function (resp) {
                    var data = resp.data;
                    $.confirm({
                        title: '自动发货结果',
                        content: '本次发货成功'+data.succ+'条, 失败'+data.fail+'条',
                        confirmButton: '确认',
                        cancelButton: false,
                        icon: 'fa fa-info',
                        theme: 'bootstrap',
                        backgroundDismiss: false,
                        keyboardEnabled: true,
                        confirmButtonClass: 'btn-info',
                        confirm: function () {
                            window.location.reload();
                        },
                    });
                }).fail(function (data) {
                    ADQ.notify.notifyResp(data);
                });
            },
            _getSearchOption: function () {
                var options = ADQ.utils.getAllInput('#sidebar_right'),
                    searched = ADQ.utils.getAllInput('#sidebar_right');
                searched.id_field = $('#searchId').data('field');
                if (searched.award_time) searched.time_field = 'award_time';
                else if(searched.send_time) searched.time_field = 'send_time';
                ADQ.utils.saveSearched('order', searched);
                return options;
            },
            export: function () {
                if ($('#searchStatus').val() < 4) {
                    ADQ.notify.error('错误', '仅能导出中奖订单');
                    return;
                }
                ADQ.notify.warning('警告', '导出中，请等待...');
                var options = this._getSearchOption();
                ADQ.exportData(this.collection.url, options);
                return false;
            },
            doSearch: function () {
                var options = this._getSearchOption();
                app.navigate(ADQ.utils.composeQueryString('#order/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    sources: this.sources.toJSON(),
                    brands: this.brands.toJSON(),
                    searched: JSON.parse(localStorage.order_searched || '{}')
                }));
                var that = this;
                ADQ.utils.getFileUploader('/admin/order/', null, function (data) {
                    $.confirm({
                        title: '导入结果',
                        content: '本次导入成功'+data.data.succ+'条, 失败'+data.data.fail+'条',
                        confirmButton: '确认',
                        cancelButton: false,
                        icon: 'fa fa-info',
                        theme: 'bootstrap',
                        backgroundDismiss: false,
                        keyboardEnabled: true,
                        confirmButtonClass: 'btn-info',
                        confirm: function () {
                            window.location.reload();
                        },
                    });
                });
                ADQ.utils.renderTable('order-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#order/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#order/');
                $('.datetime-input').datetimepicker({
                    format: 'YYYY-MM-DD HH:mm:ss',
                });
                $('.date-input').datetimepicker({
                    format: 'YYYY-MM-DD',
                });
                return this;
            },
            load: function () {
                this.sources.fetch({
                    reset: true,
                    data: {
                        $size: -1
                    },
                });
                this.brands.fetch({
                    reset: true,
                    data: {
                        $size: -1
                    }
                })
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var OrderListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/OrderList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new OrderListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var OrderDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #orderSave': 'toSave',
                'click #refreshStatus': 'refreshStatus'
            },
            initialize: function (options) {
                this.model = new opModelCls.Order();
                this.model.set('id', options.orderID);
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            refreshStatus: function (e) {
                e.preventDefault();
                $.get('/admin/order/status/' + this.model.get('id')).then(function () {
                    window.location.reload();
                }).fail(function (data) {
                    ADQ.notify.notifyResp(data);
                    });
                return false;
            },
            toSave: function (e) {
                e.preventDefault();
                var extend = {
                    express: $('#inputExpress').val(),
                    express_num: $('#inputExpressNum').val(),
                    buy_price: parseFloat($('#inputBuyPrice').val()),
                    buy_from: $('#inputBuyFrom').val(),
                    remark: $('#inputRemark').val(),
                    internal_remark: $('#inputInternalRemark').val(),
                },
                    status = parseInt($('#inputStatus').val());
                if(this.model.get('status') >= 4){
                    extend.send_time = $('#inputSendTime').val() || moment().format('YYYY-MM-DD');
                }
                extend = JSON.stringify(extend);
                var attrs = {
                    'status': status,
                    'extend': extend,
                };
                if (this.model.get('ship_status') != $('#inputShipStatus').val()) {
                    attrs.ship_status = parseInt($('#inputShipStatus').val());
                }
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                var data = this.model.toJSON();
                var receipt_address = JSON.parse(data.receipt_address || '{}');
                var detail_address = JSON.parse(receipt_address.addr_code || '[]');
                var pre_address = '';
                for (var k = 0; k < detail_address.length; ++k) {
                    var item_name = detail_address[k].name;
                    pre_address += item_name;
                }
                receipt_address.address = pre_address + receipt_address.address;
                data.receipt_address = receipt_address;
                data.extend = JSON.parse(data.extend || '{}');
                data.status_dict = ORDER_STATUS;
                if (!this.card && data.status >= 5 && data.activity_name &&
                    data.activity_name.indexOf('充值卡') != -1) {
                    this.card = new opModelCls.ChargeCard();
                    this.card.bind('change reset', this.renderWithData, this);
                    this.card.set('id', data.id);
                    this.card.fetch({
                        reset: true
                    });
                }
                this.$el.html(this.template({
                    info: data,
                    card: (this.card ? this.card.get('card_info') : []) || []
                }));
                $('.multiselect').multiselect();
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true
                });
            }
        });
        var OrderDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/OrderDetail.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new OrderDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var RedEnvelopeListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click #export': 'export',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.RedEnvelopeCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            _getSearchOption: function () {
                var searched = ADQ.utils.getAllInput('#sidebar_right');
                ADQ.utils.saveSearched('redenvelope', searched);
                return searched;
            },
            export: function () {
                ADQ.notify.warning('警告', '导出中，请等待...');
                var options = this._getSearchOption();
                ADQ.exportData(this.collection.url, options);
                return false;
            },
            doSearch: function () {
                var options = this._getSearchOption();
                app.navigate(ADQ.utils.composeQueryString('#redenvelope/', options), {
                    trigger: true
                });
                ADQ.utils.saveSearched('redenvelope', options);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.redenvelope_searched || '{}')
                }));
                var that = this;
                ADQ.utils.getFileUploader('/admin/order/red_envelope/');
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#redenvelope/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#redenvelope/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var RedEnvelopeListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/RedEnvelopeList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new RedEnvelopeListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var ShowListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.ShowCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.userId = parseInt($('#searchUserId').val());
                searched.status = parseInt($('#searchStatus').val());
                searched.activity_name = $('#searchActivityName').val();
                searched.user_type = parseInt($('#searchUserType').val());
                searched.shipping_type = parseInt($('#searchShippingType').val());
                if (!isNaN(searched.userId)) {
                    options.user_id = searched.userId;
                }
                if (searched.status != -1) {
                    options.status = searched.status;
                }
                if (searched.activity_name) options.activity_name = searched.activity_name;
                if (searched.user_type != -1) {
                    options.is_virtual = searched.user_type;
                }
                // if (searched.shipping_type == 0) {
                //     options.shipping_type = 0;
                // } else if (searched.shipping_type == 1) {
                //     options.shipping_type = {"$gt": 0}
                // }
                ADQ.utils.saveSearched('show', searched);
                app.navigate(ADQ.utils.composeQueryString('#show/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    status_dct: SHOW_STATUS,
                    searched: JSON.parse(localStorage.show_searched || '{}')
                }));
                $('#statusFilter').val(this.options.status);
                var that = this;
                ADQ.utils.renderTable('show-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#show/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#show/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var ShowListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/ShowList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var luckyShowListView = new ShowListView(this.options);
                luckyShowListView.template = this.template;

                this.$el.empty();
                this.$el.append(luckyShowListView.render().el);
                luckyShowListView.load();

                return this;
            }
        });
        var ShowDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #showSave': 'toSave',
                'click .delete-image': 'deleteImage',
            },
            initialize: function (options) {
                this.model = new opModelCls.Show();
                this.deletedImages = [];
                if (options.showId) {
                    this.model.set('id', options.showId);
                } else {
                    this.model.set(options.params);
                    this.account = new statsModelCls.Account();
                    this.account.set('id', options.params.user_id);
                    delete options.params;
                    this.account.bind('change reset', this.renderWithData, this);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            deleteImage: function (e) {
                e.preventDefault();
                var url = $(e.currentTarget).next('a').attr('href');
                $(e.currentTarget).parents('div.thumb').remove();

                this.deletedImages.push(url);
                return false;
            },
            _getCurrentInputs: function () {
                var data = {};
                if (this.model.get('status') <= 2) {
                    data.content = $('#inputContent').val();
                    data.images = [];
                    $('.detail-image').each(function () {
                        data.images.push($(this).attr('src'));
                    });
                    data.images = data.images.join(',');
                }
                if (this.model.get('status') >= 2) {
                    data.status = parseInt($('#inputStatus').val());
                    data.verify_comment = $('#inputComment').val();
                    if (data.status == 4 || data.status == 16) {
                        data.verify_award = parseInt($('#inputVerifyAward').val()) || 0;
                    } else {
                        data.verify_comment = $('#inputComment').val();
                    }
                    if ($('#inputHighlight').is(':checked')) {
                        data.highlight = 1;
                    } else {
                        data.highlight = 0;
                    }
                }
                return data;
            },
            toSave: function (e) {
                e.preventDefault();
                var data = this._getCurrentInputs();
                if (data.status == 4 || data.status == 16) {
                    if (data.verify_award == 0) {
                        ADQ.notify.error('错误', '通过审核奖励不应为0');
                        return;
                    }
                    if (data.verify_award < 200 || data.verify_award > 3500) {
                        ADQ.notify.error('错误', '奖励积分应该在200-3500之间');
                        return;
                    }
                } else if (data.status == 8 && data.verify_comment == '') {
                    ADQ.notify.error('错误', '拒绝应说明原因');
                    return;
                }
                var postData = {
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                };
                if (data.status) {
                    // create new show
                    postData.patch = true;
                    postData.activity_id = this.activity_id;
                }
                this.model.save(data, postData);
                if (this.deletedImages.length > 0)
                    $.post('admin/image/delete/', {
                        urls: this.deletedImages.join(',')
                    }).done(function() {
                        this.deletedImages = [];
                    });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON(),
                    account: this.account ? this.account.toJSON() : {}
                }));
                $('.image-popup').magnificPopup({
                    type: 'image',
                    closeOnContentClick: true,
                    mainClass: 'mfp-img-mobile',
                    image: {
                        verticalFit: true,
                        titleSrc: function (item) {
                            return '<a href="' + item.el.attr('href') +
                                '" target="_blank">查看原图</a>';
                        }
                    }
                });
                $('#inputStatus').multiselect();
                var that = this;
                ADQ.utils.getSingleUploader('uploadImg', function (url) {
                    that.model.set(that._getCurrentInputs());
                    var images = (that.model.get('images') || '').split(',');
                    images.push(url);
                    that.model.set('images', images.join(','));
                }, true);
                ADQ.utils.getSingleUploader('uploadAvatar', function (url) {
                    $.post('/admin/virtual/account/' + that.model.get('user_id'),
                        JSON.stringify({ avatar_id: url })).fail(function (d) {
                        ADQ.notify.notifyResp(d);
                        }).then(function () {
                            that.account.set('avatar_id', url);
                    })
                });
                return this;
            },
            load: function () {
                if (this.model.get('id')) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.account.fetch({ reset: true });
                }
            }
        });
        var ShowDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/ShowDetail.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ShowDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var BigShowListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.TemplateCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.idOrName = $('#searchIdOrName').val();
                searched.price_lower = parseInt($('#searchPriceLower').val());
                searched.price_upper = parseInt($('#searchPriceUpper').val());
                var id = Number(searched.idOrName);
                if (isNaN(id)) {
                    options.name = {
                        '$like': searched.idOrName
                    };
                } else if (id) {
                    options.id = id;
                }
                if (searched.price_lower || searched.price_upper) {
                    options.target_amount = {};
                    if (searched.price_lower) options.target_amount.$gte = searched.price_lower;
                    if (searched.price_upper) options.target_amount.$lte = searched.price_upper;
                }
                ADQ.utils.saveSearched('bigshow', searched);
                app.navigate(ADQ.utils.composeQueryString('#bigshow/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    templates: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.bigshow_searched || '{}')
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#bigshow/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#bigshow/');
                return this;
            },
            load: function () {
                this.options.calc_show = 1;
                if (!this.options.target_amount) {
                    this.options.target_amount = JSON.stringify({ '$gte': 2000 });
                }
                this.options.current_term = JSON.stringify({ "$gt": 1 });
                this.options.status = 1;
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var BigShowListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/BigShowList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BigShowListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var BigShowDetailView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.info = options.params || {};
                this.info.id = options.template_id;
                delete options.params;
                this.collection = new opModelCls.ActivityCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    templates: this.collection.toJSON(),
                    info: this.info
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        })
                    }
                });
                $('#paginator').bootstrapPaginator({
                    currentPage: this.options.$page,
                    totalPages: Math.ceil(this.collection.total / 10) || 1,
                    size: 'small',
                    numberOfPages: 10,
                    alignment: 'center',
                    onPageClicked: function (e, originalEvent, type, page) {
                        e.stopImmediatePropagation();
                        that.options.$page = page;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        });
                    }
                });
                return this;
            },
            load: function () {
                this.options.calc_show = 1;
                this.options.status = 4;
                if (!this.options.$orderby) this.options.$orderby = "-term_number";
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var BigShowDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/BigShowDetail.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BigShowDetailView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var CategoryListView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #categorySave': 'toSaveOrCreate',
                'click a.onClickDelete': "deleteItem",
            },
            initialize: function (options) {
                this.collection = new opModelCls.CategoryCollection();
                this.deletedImages = [];
                this.cachedImages = [];
                this.collection.bind('add remove change reset', this.renderWithData, this);
            },
            deleteItem: function (e) {
                e.preventDefault();
                var parent = $(e.currentTarget).parents('div.with-border'),
                    url = parent.find("img.icon").attr('src'),
                    id = parseInt(parent.data('id')),
                    thisView = this;
                $(e.currentTarget).parents('div.with-border').remove();
                this.deletedImages.push(url);
                if (!isNaN(id) && id != -1) {
                    $.ajax({
                        url: '/admin/category/' + id,
                        type: 'delete',
                        success: function () {
                            thisView.collection.remove(new opModelCls.Category({
                                id: id
                            }));
                            ADQ.notify.success();
                        },
                        error: function (data) {
                            ADQ.notify.notifyResp(data);
                        }
                    });
                }
                return false;
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            getInputs: function () {
                var updatedItems = [];
                $('div.with-border').each(function (index) {
                    var item = { order: index },
                        id = parseInt($(this).data('id'), 10);
                    if (!isNaN(id) && id != -1) {
                        item.id = id;
                    }
                    item.icon = $(this).find('img').first().attr('src');
                    if (!item.icon) {
                        ADQ.notify.error('错误', '图片不存在');
                        return;
                    }
                    $(this).find('[data-field]').each(function () {
                        var v = $(this).val();
                        if ($(this).data('type') == 'timestamp') {
                            v = $(this).data('DateTimePicker').date().unix();
                        } else if ($(this).data('type') == 'int') {
                            v = parseInt(v);
                        }
                        item[$(this).data('field')] = v;
                    });
                    updatedItems.push(item);
                });
                _.each(this.cachedImages, function (img) {
                    updatedItems.push({
                        icon: img,
                        name: "",
                        tag: "",
                        order: 0
                    });
                });
                return updatedItems;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var isAllRight = ADQ.utils.simpleCheck();
                if (!isAllRight) {
                    ADQ.notify.error('错误', '输入错误，请检验');
                    return;
                }
                this.collection.set(this.getInputs());
                this.collection.save({
                    success: function () {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });
                if (this.deletedImages.length > 0)
                    $.post('admin/image/delete/', {
                        urls: this.deletedImages.join(',')
                    }).done(function () {
                        this.deletedImages = [];
                    });
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                }));
                $('.sortable').sortable();
                $('.sortable').disableSelection();
                var that = this;
                $('#uploadIcon').magnificPopup({
                    items: {
                        src: '#uploadImagePanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    // showCloseBtn: false,
                    callbacks: {
                        beforeOpen: function () {
                            that.collection.set(that.getInputs());
                            ADQ.utils.getUploader('pickfiles', 'fsUploadProgress', function (url) {
                                that.cachedImages.push(url);
                            });
                            $('#addCachedImgs').off('click').click(function () {
                                that.collection.set(that.getInputs());
                                that.cachedImages = [];
                                $.magnificPopup.close();
                            });
                        }
                    }
                });
                $('.replace-img').each(function () {
                    var $this = $(this);
                    ADQ.utils.getSingleUploader($this.attr('id'), function (url) {
                        that.deletedImages.push(url);
                    });
                });
                $(window).scrollTop(0);
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var CategoryListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/CategoryList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CategoryListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var VirtualListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.VirtualCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.nick_name = $('#searchNickName').val();
                searched.type = parseInt($('#searchType').val());
                searched.status = parseInt($('#searchStatus').val());
                searched.user_id = $('#searchUserId').val();
                var id = Number(searched.idOrName);
                if (searched.nick_name) {
                    options.nick_name = searched.nick_name;
                }
                if (searched.type != -1) {
                    options.deleted = searched.type;
                }
                if (searched.status != -1) {
                    options.avatar_id = searched.status ? "$!null" : "$null";
                }
                if (searched.user_id) options.user_id = searched.user_id;
                ADQ.utils.saveSearched('virtual', searched);
                app.navigate(ADQ.utils.composeQueryString('#virtual/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    searched: JSON.parse(localStorage.virtual_searched || '{}'),
                    unused_avatar_count: this.collection.unused_avatar_count
                }));
                var that = this;
                ADQ.utils.getFileUploader('/admin/virtual/');
                ADQ.utils.renderTable('virtual-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#virtual/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('#uploadAvatar').magnificPopup({
                    items: {
                        src: '#uploadImagePanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    // showCloseBtn: false,
                    callbacks: {
                        beforeOpen: function () {
                            var cachedImages = [];
                            ADQ.utils.getSimplerUploader('pickfiles', function (url) {
                                cachedImages.push(url);
                                $('#countTip').html('提示：已上传' + cachedImages.length + '个');
                            }, true);
                            ADQ.utils.setProcess({ max: 0, now: 0 });
                            $('#uploadprocess').html('');
                            $('#addCachedImgs').off('click').click(function () {
                                $.magnificPopup.close();
                                $.post('/admin/virtual/avatar/', JSON.stringify({ 'avatars': cachedImages })).fail(function (data) {
                                    ADQ.notify.notifyResp(data);
                                });
                            });
                        }
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#virtual/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var VirtualListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/VirtualList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new VirtualListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var VirtualDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #virtualSave': 'toSaveOrCreate'
            },
            initialize: function (options) {
                this.model = new opModelCls.Virtual();
                if (options.virtualId) {
                    this.model.set('id', options.virtualId);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                if (!$('#virtual-form').valid()) {
                    ADQ.notify.error('错误', "输入错误，请检验");
                    return;
                }
                var avatar_id = $('#avatar').attr('src') || "";
                if (avatar_id.indexOf('placeholder') >= 0) {
                    avatar_id = null;
                }
                var attrs = {
                    'nick_name': $('#inputNickname').val(),
                    'ip': $('#inputIp').val(),
                    'avatar_id': avatar_id,
                    'phone': $('#inputPhone').val()
                };
                var pattern = /^(\d|[1-9]\d|1\d\d|2([0-4]\d|5[0-5]))\.(\d|[1-9]\d|1\d\d|2([0-4]\d|5[0-5]))\.(\d|[1-9]\d|1\d\d|2([0-4]\d|5[0-5]))\.(\d|[1-9]\d|1\d\d|2([0-4]\d|5[0-5]))$/;
                if (!attrs.ip.match(pattern)) {
                    ADQ.notify.error('错误', 'ip地址格式错误');
                    return;
                }
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON()
                }));
                ADQ.utils.getValidator('#virtual-form');
                ADQ.utils.getSingleUploader('uploadAvatar', false, null, true);
                return this;
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
            }
        });
        var VirtualDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/VirtualDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new VirtualDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var CouponTemplateListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.onClickDelete': 'toDelete',
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.CouponTemplateCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.idOrName = $('#searchIdOrName').val();
                searched.type = parseInt($('#searchType').val(), 10);
                var id = Number(searched.idOrName);
                if (isNaN(id)) {
                    options.title = {
                        '$like': searched.idOrName
                    };
                } else if (id) {
                    options.id = id;
                }
                if (searched.type && searched.type != -1) {
                    options.coupon_type = searched.type;
                }
                ADQ.utils.saveSearched('couponTemplate', searched);
                app.navigate(ADQ.utils.composeQueryString('#coupon/template/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    types: COUPON_TYPE,
                    searched: JSON.parse(localStorage.couponTemplate_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('coupon-template-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#coupon/template/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#coupon/template/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var CouponTemplateListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/CouponTemplateList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CouponTemplateListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var CouponTemplateDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #couponTemplateSave': 'toSaveOrCreate'
            },
            initialize: function (options) {
                this.model = new opModelCls.CouponTemplate();
                this.allCategories = new opModelCls.CategoryCollection();
                if (options.couponTemplateId) {
                    this.model.set('id', options.couponTemplateId);
                }
                this.model.bind('change reset', this.renderWithData, this);
                this.allCategories.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                if (!ADQ.utils.simpleCheck("#coupon-template-form")) {
                    ADQ.notify.error('错误', "输入错误，请检验");
                    return;
                }
                var attrs = {
                    'title': $('#inputTitle').val(),
                    'desc': $("#inputDesc").val(),
                    'coupon_type': parseInt($('#inputCouponType').val()),
                    'price': parseFloat($('#inputPrice').val()),
                    'valid_ts': parseInt($('#inputValidTs').val(), 10),
                    'activity_tids': $('#inputActivities').val().replace(/\D/g, ',').replace(/,{2,}/g, ','),
                    'scope_all': parseInt($('#inputScopeAll').val()),
                    'cmd': $('#inputCmd').val(),
                    'remark': $('#inputRemark').val()
                };
                attrs.activity_categories = (ADQ.utils.getAllInput().activity_categories || []).join(',');
                if(attrs.coupon_type == 2){
                    attrs.condition_price = parseInt(
                        $('#inputConditionPrice').val());
                }
                attrs.valid_ts = attrs.valid_ts * 24 * 60 * 60;
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                var data = this.model.toJSON();
                data['allCategories'] = this.allCategories.toJSON();
                this.$el.html(this.template(data));
                $('.multiselect').multiselect();
                ADQ.utils.getValidator('#coupon-template-form');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
                this.allCategories.fetch({
                    reset: true
                });
            }
        });
        var CouponTemplateDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/CouponTemplateDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CouponTemplateDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var ABTestListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.delete-item': 'toDelete',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.ABTestCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#abtest/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#abtest/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var ABTestListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/ABTestList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ABTestListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ABTestDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
                'click .switch-key': 'switchKey',
                'click .shortcut': 'quickAdd'
            },
            initialize: function (options) {
                this.model = new opModelCls.ABTest();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            switchKey: function (e) {
                var $this = $(e.target);
                if ($this.data('key') == 'include') {
                    $this.data('key', 'exclude').html('排除渠道');
                } else {
                    $this.data('key', 'include').html('包含渠道');
                }
                return false;
            },
            quickAdd: function (e) {
                e.preventDefault();
                var $this = $(e.target),
                    aria = $this.data('aria'),
                    $pel = $this.closest('.input-group'),
                    $key = $('#inputKey'),
                    $el = $('#inputChannel');
                switch (aria) {
                    case 'allAndroid':
                        $key.data('key', 'exclude').html('排除渠道');
                        $el.val(NOT_ANDROID_CHN.join(','));
                        break;
                    case 'allIOS':
                        $key.data('key', 'include').html('包含渠道');
                        $el.val(IOS_CHN.join(','));
                        break;
                    case 'allQG':
                        $key.data('key', 'include').html('包含渠道');
                        $el.val(IOS_QG_CHN.join(','));
                        break;
                }
                $pel.find('[data-toggle="dropdown"]').parent().removeClass('open');
                return false;
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                var attrs = {
                    user_id: [$('#inputUserIdLower').val(), $('#inputUserIdUpper').val()],
                },
                    chn = $('#inputChannel').val();
                if (chn.length > 0) {
                    attrs.chn = {}
                    var key = $('#inputKey').data('key');
                    attrs.chn[key] = chn.split(',');
                }

                var saveData = {
                    content: JSON.stringify(attrs),
                    name: $('#inputName').val()
                }
                this.model.save(saveData, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON()
                }));
                return this;
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
            }
        });
        var ABTestDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/ABTestDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ABTestDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var NotificationListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click a.delete-item': 'toDelete',
                'click #search': 'doSearch',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new opModelCls.NotificationCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.content = $('#searchContent').val();
                if (searched.content) {
                    options.content = {$like: searched.content}
                }
                ADQ.utils.saveSearched('notification', searched);
                app.navigate(ADQ.utils.composeQueryString('#notification/', options), {
                    trigger: true
                });
            },
            toDelete: function (e) {
                _deleteItem(e, this.collection);
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.notification_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#notification/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#notification/');

                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var NotificationListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/NotificationList.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new NotificationListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var NotificationDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #save': 'toSaveOrCreate',
                'change #inputAlert': 'toggleAlert',
                'click .remove-filter': 'removeFilter',
                'click #addFilter': 'addFilter',
                'click .switch-key': 'switchKey',
                'click .shortcut': 'quickAdd'
            },
            initialize: function (options) {
                this.model = new opModelCls.Notification();
                if (options.id) {
                    this.model.set('id', options.id);
                }
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            toggleAlert: function () {
                if ($('#inputAlert').is(':checked')) {
                    $('#alertContent').show();
                } else {
                    $('#alertContent').hide();
                }
            },
            toSaveOrCreate: function (e) {
                e.preventDefault();
                if (!ADQ.utils.simpleCheck('#content-form')) {
                    ADQ.notify.error('错误', '输入错误，请检查');
                    return;
                }
                var attrs = ADQ.utils.getAllInput('#content-form'),
                    filter_list = [];
                if (!$('#inputAlert').is(':checked') && attrs.extend) {
                    delete attrs.extend.alert;
                }
                if (attrs.extend && attrs.extend.alert && attrs.extend.alert.type == "") {
                    delete attrs.extend.alert.type;
                }
                attrs.expire_ts = moment(attrs.expire_ts).unix();
                $('#filter-form .filter').each(function () {
                    var data = ADQ.utils.getAllInput(this),
                        key = $(this).find('.switch-key:first').data('key');
                    data['chn'] = {};
                    data['chn'][key] = $(this).find('.filter-value:first').val();
                    data['chn'][key] = data['chn'][key].split(',');
                    filter_list.push(data);
                });
                if (!attrs.extend) attrs.extend = {};
                if (filter_list.length > 0) {
                    attrs.extend.filter_list = filter_list;
                }
                attrs.extend = attrs.extend ? JSON.stringify(attrs.extend) : null;
                attrs.content = JSON.stringify(attrs.content);
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            removeFilter: function (e) {
                $(e.target).closest('.filter').remove();
                return false;
            },
            addFilter: function (e) {
                e.preventDefault();
                $('#filter-form').append($('#filterTemplate').html());
                return false;
            },
            switchKey: function (e) {
                var $this = $(e.target);
                if ($this.data('key') == 'include') {
                    $this.data('key', 'exclude').html('排除渠道');
                } else {
                    $this.data('key', 'include').html('包含渠道');
                }
                return false;
            },
            quickAdd: function (e) {
                e.preventDefault();
                var $this = $(e.target),
                    aria = $this.data('aria'),
                    $pel = $this.closest('.input-group'),
                    $key = $pel.find('.switch-key:first'),
                    $el = $pel.find('.filter-value:first');
                switch (aria) {
                    case 'allAndroid':
                        $key.data('key', 'exclude').html('排除渠道');
                        $el.val(NOT_ANDROID_CHN.join(','));
                        break;
                    case 'allIOS':
                        $key.data('key', 'include').html('包含渠道');
                        $el.val(IOS_CHN.join(','));
                        break;
                    case 'allQG':
                        $key.data('key', 'include').html('包含渠道');
                        $el.val(IOS_QG_CHN.join(','));
                        break;
                }
                $pel.find('[data-toggle="dropdown"]').parent().removeClass('open');
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    info: this.model.toJSON()
                }));
                ADQ.utils.getSingleUploader('uploadImage');
                $('#inputExpireTs').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                return this;
            },
            load: function () {
                if (this.model.id) {
                    this.model.fetch({
                        reset: true
                    });
                } else {
                    this.renderWithData();
                }
            }
        });
        var NotificationDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "op/NotificationDetail.html",

            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new NotificationDetailView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        return {
            TemplateListPage: TemplateListPage,
            TemplateDetailPage: TemplateDetailPage,

            OrderListPage: OrderListPage,
            OrderDetailPage: OrderDetailPage,
            RedEnvelopeListPage: RedEnvelopeListPage,

            ShowListPage: ShowListPage,
            ShowDetailPage: ShowDetailPage,
            BigShowListPage: BigShowListPage,
            BigShowDetailPage: BigShowDetailPage,

            CategoryListPage: CategoryListPage,

            VirtualListPage: VirtualListPage,
            VirtualDetailPage: VirtualDetailPage,

            CouponTemplateListPage: CouponTemplateListPage,
            CouponTemplateDetailPage: CouponTemplateDetailPage,

            ABTestListPage: ABTestListPage,
            ABTestDetailPage: ABTestDetailPage,
            FeedbackListPage: FeedbackListPage,

            NotificationListPage: NotificationListPage,
            NotificationDetailPage: NotificationDetailPage
        };
    } ();

    var statsViewCls = function () {
        var AccountDetailView = Backbone.View.extend({
            template: "stats/AccountDetail.html",
            initialize: function (options) {
                this.accountId = options.id;
                this.model = new statsModelCls.Account();
                if (this.accountId) this.model.set('id', this.accountId)
                this.model.bind('change', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            load: function (options) {
                if (this.accountId != null) {
                    this.model.fetch({
                        reset: true,
                        error: function (c, r, o) {
                            ADQ.notify.notifyResp(r);
                            $('#content').append('<h4 class="text-muted">无数据</h4>');
                        },
                        success: function (c, r, o) {
                            if (options.callback) {
                                options.callback();
                            }
                        }
                    });
                } else {
                    this.renderWithData();
                }
            },
            renderWithData: function () {
                this.$el.html(this.template(this.model.toJSON()));
                $(window).scrollTop(0);
                return this;
            },
        });
        var AccountCouponListView = Backbone.View.extend({
            tagName: "div",
            className: "p25 pt35",
            template: "stats/AccountCoupon.html",
            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.AccountCouponCollection(options);
                this.coupons = new opModelCls.CouponTemplateCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
                this.coupons.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    type: COUPON_TYPE,
                    coupons: this.coupons.models
                }));
                var that = this;
                ADQ.utils.renderTable('account-coupon-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        });
                    }
                });
                $('#addCoupon').magnificPopup({
                    items: {
                        src: '#addCouponPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    // showCloseBtn: false,
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitAdd').off('click').click(function () {
                                var options = {
                                    template_id: parseInt($("#inputCoupon").val()),
                                    user_id: that.options.user_id,
                                    count: parseInt($('#inputCount').val(), 10)
                                };
                                $.magnificPopup.close();
                                $.post('admin/coupon/add/', JSON.stringify(options)).fail(function (data) {
                                    ADQ.notify.notifyResp(data);
                                }).then(function (data) {
                                    ADQ.notify.success();
                                    that.collection.fetch({
                                        reset: true
                                    })
                                }
                                    );
                            });
                        },

                    }
                });
                $('#inputCoupon').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 200,
                });
                $('#paginator').bootstrapPaginator({
                    currentPage: this.options.$page,
                    totalPages: Math.ceil(this.collection.total / 5) || 1,
                    size: 'small',
                    numberOfPages: 10,
                    alignment: 'center',
                    onPageClicked: function (e, originalEvent, type, page) {
                        e.stopImmediatePropagation();
                        that.options.$page = page;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        });
                    }
                });
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                });
                this.coupons.fetch({
                    reset: true,
                    data: {
                        $size: -1
                    }
                });
            }
        });
        var AccountTransactionView = Backbone.View.extend({
            tagName: "div",
            className: "p25 pt35",
            template: "stats/AccountTransaction.html",
            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.AccountTransactionCollection(options);
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                }));
                var that = this;
                ADQ.utils.renderTable('account-transaction-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        });
                    }
                });
                $('#trans-paginator').bootstrapPaginator({
                    currentPage: this.options.$page,
                    totalPages: Math.ceil(this.collection.total / 5) || 1,
                    size: 'small',
                    numberOfPages: 10,
                    alignment: 'center',
                    onPageClicked: function (e, originalEvent, type, page) {
                        e.stopImmediatePropagation();
                        that.options.$page = page;
                        that.collection.fetch({
                            reset: true,
                            data: that.options
                        });
                    }
                });
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                });
            }
        });
        var AccountDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/AccountPage.html",
            events: {
                'click #search': 'doSearch',
            },
            initialize: function (options) {
                this.options = options;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.id = parseInt($('#searchId').val());
                if (!isNaN(searched.id)) {
                    options.id = searched.id;
                    ADQ.utils.saveSearched('stats_account', searched);
                    app.navigate('#stats/account/?id=' + searched.id, {
                        trigger: true
                    });
                }
            },
            render: function () {
                this.$el.html(this.template({
                    searched: JSON.parse(localStorage.stats_account_searched || '{}')
                }));
                var section = this.$el.find('#content');
                if (this.options.id != null) {
                    var detailView = new AccountDetailView(this.options),
                        couponList = new AccountCouponListView({
                            'user_id': this.options.id,
                            'status': 1,
                            '$page': 1,
                            '$size': 5,
                        }),
                        transactionList = new AccountTransactionView({
                            'user_id': this.options.id,
                            '$page': 1,
                            '$size': 5,
                            '$orderby': '-created_at'
                        })

                    $(section).append(detailView.render().el);
                    detailView.load({
                        callback: function () {
                            $(section).append(couponList.render().el);
                            couponList.load();
                            $(section).append(transactionList.render().el);
                            transactionList.load();
                        }
                    });
                } else {
                    $(section).append('<h4 class="text-muted">请从右侧进行搜索...</h4>');
                }

                return this;
            }
        });
        var ActivityListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'change #searchStatus': 'toggleFilter',
                'click #exportData': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.ActivityCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.template_id = $('#searchTemplateId').val();
                searched.winner_id = parseInt($("#searchWinnerId").val());
                searched.created_at_lower = $("#searchCreatedAtLower").val();
                searched.created_at_upper = $('#searchCreatedAtUpper').val();
                searched.type = parseInt($('#searchType').val());
                searched.status = parseInt($('#searchStatus').val());
                searched.winner_type = parseInt($('#searchWinnerType').val());
                searched.announced_at_lower = $('#searchAnnouncedAtLower').val();
                searched.announced_at_upper = $('#searchAnnouncedAtUpper').val();

                var template_id = Number(searched.template_id);
                if (!isNaN(template_id) && template_id) {
                    options.template_id = template_id;
                } else if (searched.template_id) {
                    options.name = { "$like": searched.template_id };
                }
                if (!isNaN(searched.winner_id)) {
                    options.winner_id = searched.winner_id;
                }
                if (searched.type === 0) {
                    options.price = 0;
                } else if (searched.type != -1) {
                    options.unit = searched.type;
                }
                if (searched.status != -1) {
                    options.status = searched.status;
                }
                if (searched.winner_type != -1 && options.winner_id == undefined &&
                    options.status != 1 && options.status != 2) {
                    options.winner_type = searched.winner_type;
                }
                if (searched.created_at_lower || searched.created_at_upper) {
                    options.created_at = {};
                    if (searched.created_at_lower) options.created_at.$gte = searched.created_at_lower;
                    if (searched.created_at_upper) options.created_at.$lt = searched.created_at_upper;
                }
                if (searched.announced_at_lower || searched.announced_at_upper) {
                    options.announced_at = {};
                    if (searched.announced_at_lower) options.announced_at.$gte = searched.announced_at_lower;
                    if (searched.announced_at_upper) options.announced_at.$lt = searched.announced_at_upper;
                }
                ADQ.utils.saveSearched('stats_activity', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/activity/', options), {
                    trigger: true
                });
            },
            exportData: function (e) {
                e.preventDefault();
                if (this.collection.total == 0) {
                    return;
                }
                if (this.collection.total > 1000) {
                    ADQ.notify.warning('警告', '数据量较大，请耐心等待');
                }
                ADQ.exportData(this.collection.url, this.options);
                return false;
            },
            toggleFilter: function (e) {
                var val;
                if (e) {
                    val = $(e.target).val();
                } else {
                    val = parseInt($('#searchStatus').val());
                }
                if (val == 4) {
                    $('.announced-filter').show();
                } else {
                    $('.announced-filter').hide();
                }
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    status: ACTIVITY_STATUS,
                    searched: JSON.parse(localStorage.stats_activity_searched || '{}'),
                    overview: this.collection.overview,
                }));
                var that = this;
                ADQ.utils.renderTable('activity-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/activity/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('[data-type=date]').datetimepicker({
                    defaultDate: false,
                    format: 'YYYY-MM-DD'
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/activity/');
                this.toggleFilter();
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var ActivityListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/ActivitiesList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ActivityListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var OrderListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click #exportData': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.OrderCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            exportData: function (e) {
                e.preventDefault();
                if (this.collection.total == 0) {
                    return;
                }
                if (this.collection.total > 1000) {
                    ADQ.notify.warning('警告', '数据量较大，请耐心等待');
                }
                ADQ.exportData(this.collection.url, this.options);
                return false;
            },
            doSearch: function () {
                var options = {},
                    searched = {},
                    reg = /^[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}$/;

                searched.activity_id = $('#searchActivityId').val();
                searched.buyer = parseInt($("#searchBuyer").val());
                searched.created_at_lower = $("#searchCreatedAtLower").val();
                searched.created_at_upper = $('#searchCreatedAtUpper').val();
                searched.type = parseInt($('#searchType').val());
                if (searched.activity_id) {
                    if (searched.activity_id.match(reg))
                        options.activity_id = searched.activity_id;
                    else
                        options.activity_name = searched.activity_id;
                }
                if (!isNaN(searched.buyer)) {
                    options.buyer = searched.buyer;
                }
                if (searched.created_at_lower || searched.created_at_upper) {
                    options.created_at = {};
                    if (searched.created_at_lower) options.created_at.$gte = searched.created_at_lower;
                    if (searched.created_at_upper) options.created_at.$lt = searched.created_at_upper;
                }
                if (searched.type != -1) {
                    options.activity_type = searched.type;
                }
                ADQ.utils.saveSearched('stats_order', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/order/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    searched: JSON.parse(localStorage.stats_order_searched || '{}'),
                    overview: this.collection.overview,
                }));
                var that = this;
                ADQ.utils.renderTable('order-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/order/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('[data-type=date]').datetimepicker({
                    defaultDate: false,
                    format: 'YYYY-MM-DD'
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/order/');

                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                });
            }
        });
        var OrderListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/OrderList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new OrderListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var CouponListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click #exportData': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.CouponCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            exportData: function (e) {
                e.preventDefault();
                if (this.collection.total == 0) {
                    return;
                }
                if (this.collection.total > 1000) {
                    ADQ.notify.warning('警告', '数据量较大，请耐心等待');
                }
                ADQ.exportData(this.collection.url, this.options);
                return false;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.idOrName = $('#searchIdOrName').val();
                searched.user_id = parseInt($("#searchUserId").val());
                searched.created_at_lower = $("#searchCreatedAtLower").val();
                searched.created_at_upper = $('#searchCreatedAtUpper').val();
                searched.status = parseInt($('#searchStatus').val());
                searched.type = parseInt($('#searchType').val());

                if (searched.idOrName) {
                    var id = parseInt(searched.idOrName, 10);
                    if ($isNaN(id)) options.id = id;
                    else options.title = searched.idOrName;
                }
                if (!isNaN(searched.user_id)) {
                    options.user_id = searched.user_id;
                }
                if (searched.created_at_lower || searched.created_at_upper) {
                    options.start_ts = {};
                    if (searched.created_at_lower) options.start_ts.$gte = moment(searched.created_at_lower, 'YYYY-MM-DD').unix();
                    if (searched.created_at_upper) options.start_ts.$lt = moment(searched.created_at_upper, 'YYYY-MM-DD').unix();
                }
                if (searched.status != -1) {
                    options.status = searched.status;
                }
                if (searched.type != -1) {
                    options.coupon_type = searched.type;
                }
                ADQ.utils.saveSearched('stats_coupon', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/coupon/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    status: COUPON_STATUS,
                    type: COUPON_TYPE,
                    searched: JSON.parse(localStorage.stats_coupon_searched || '{}'),
                    overview: this.collection.overview,
                }));
                var that = this;
                ADQ.utils.renderTable('coupon-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/coupon/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('[data-type=date]').datetimepicker({
                    defaultDate: false,
                    format: 'YYYY-MM-DD'
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/coupon/');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var CouponListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/CouponList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new CouponListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var PayListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click #exportData': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.PayCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            exportData: function (e) {
                e.preventDefault();
                if (this.collection.total == 0) {
                    return;
                }
                if (this.collection.total > 1000) {
                    ADQ.notify.warning('警告', '数据量较大，请耐心等待');
                }
                ADQ.exportData(this.collection.url, this.options);
                return false;
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.id = $('#searchId').val();
                searched.user_id = parseInt($("#searchUserId").val());
                searched.created_at_lower = $("#searchCreatedAtLower").val();
                searched.created_at_upper = $('#searchCreatedAtUpper').val();
                searched.type = parseInt($('#searchType').val());
                searched.pay_type = parseInt($('#searchPayType').val());
                searched.user_type = parseInt($('#searchUserType').val());

                if (!isNaN(searched.user_id)) {
                    options.user_id = searched.user_id;
                }
                if (searched.id) {
                    options.id = searched.id;
                }
                if (searched.created_at_lower || searched.created_at_upper) {
                    options.created_at = {};
                    if (searched.created_at_lower) options.created_at.$gte = searched.created_at_lower;
                    if (searched.created_at_upper) options.created_at.$lt = searched.created_at_upper;
                }
                if (searched.type != -1) {
                    options.activity_id = searched.type ? '$!null' : '$null';
                }
                if (searched.pay_type != -1) {
                    options.pay_type = searched.pay_type;
                }
                if (searched.user_type != -1) {
                    options.user_type = searched.user_type;
                }
                ADQ.utils.saveSearched('stats_pay', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/pay/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    searched: JSON.parse(localStorage.stats_pay_searched || '{}'),
                    overview: this.collection.overview,
                }));
                var that = this;
                ADQ.utils.renderTable('pay-list', {
                    $orderby: that.options.$orderby || '-created_at',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/pay/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('[data-type=date]').datetimepicker({
                    defaultDate: false,
                    format: 'YYYY-MM-DD'
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/pay/');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var PayListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/PayList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new PayListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var UninstallListView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
                'click #exportData': 'exportData',
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new statsModelCls.UninstallCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            exportData: function (e) {
                e.preventDefault();
                if (this.collection.total == 0) {
                    return;
                }
                if (this.collection.total > 1000) {
                    ADQ.notify.warning('警告', '数据量较大，请耐心等待');
                }
                ADQ.exportData(this.collection.url, this.options);
                return false;
            },
            doSearch: function () {
                var options = {},
                    searched = {};

                searched.remove_at_lower = $("#searchRemoveAtLower").val();
                searched.remove_at_upper = $('#searchRemoveAtUpper').val();
                if (searched.remove_at_lower || searched.remove_at_upper) {
                    options.remove_at = {};
                    if (searched.remove_at_lower) options.remove_at.$gte = searched.remove_at_lower;
                    if (searched.remove_at_upper) options.remove_at.$lt = searched.remove_at_upper;
                }
                ADQ.utils.saveSearched('stats_uninstall', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/uninstall/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    overview: this.collection.overview,
                    searched: JSON.parse(localStorage.stats_uninstall_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/uninstall/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('.date-input').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                if (this.collection.overview.questionare) {
                    var options = ADQ.utils.getHighChartPieOptions(),
                        series = options.series[0].data;
                    _.each(this.collection.overview.questionare.dist, function (v, k) {
                        if (v > 0) series.push({
                            name: "选项" + k,
                            y: v
                        });
                    });
                    $('#reasonDist').highcharts(options);
                }
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/uninstall/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var UninstallListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "stats/UninstallList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new UninstallListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        return {
            AccountDetailView: AccountDetailView,
            AccountCouponListView: AccountCouponListView,
            AccountTransactionView: AccountTransactionView,
            AccountDetailPage: AccountDetailPage,
            ActivityListPage: ActivityListPage,
            OrderListPage: OrderListPage,
            CouponListPage: CouponListPage,
            PayListPage: PayListPage,
            UninstallListPage: UninstallListPage
        };
    } ();

    var vipsViewCls = function () {
        var MissedVipsListView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
                'change #selectAll': 'selectAll',
                'change .check-row': 'checkRow',
                'click #export': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new vipsModelCls.MissedVipsCollection();
                this.coupons = new opModelCls.CouponTemplateCollection();
                this.checkedUids = [];
                this.checkedIds = [];
                this.collection.bind('change remove reset', this.renderWithData, this);
                this.coupons.bind('reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            exportData: function () {
                ADQ.notify.warning('警告', '导出中，请等待');
                ADQ.exportData(this.collection.url, this._getSearchOption());
            },
            selectAll: function (e) {
                var checked = $(e.target).is(':checked');
                $('.check-row').prop('checked', checked);
                if (!checked) {
                    this.checkedUids = [];
                    this.checkedIds = [];
                }
                else {
                    this.checkedUids = this.collection.pluck('uid');
                    this.checkedIds = this.collection.pluck('id');
                }
                $('#selectTips').html('已选中' + this.checkedIds.length + '个');
            },
            checkRow: function (e) {
                var tr = $(e.target).closest('tr'),
                    uid = tr.data('uid'),
                    id = tr.data('id');
                if ($(e.target).is(':checked')) {
                    this.checkedUids.push(uid);
                    this.checkedIds.push(id);
                } else {
                    this.checkedUids = _.without(this.checkedUids, uid);
                    this.checkedIds = _.without(this.checkedIds, id);
                }
                $('#selectTips').html('已选中' + this.checkedIds.length + '个');
            },
            _getSearchOption: function () {
                var options = {},
                    searched = {};
                searched.user_type = parseInt($('#searchUserType').val());
                searched.created_at = $('#searchCreatedAt').val();
                searched.lost_days = $('#searchLostDays').val();
                searched.status = parseInt($('#searchStatus').val());
                searched.coupon_level = parseInt($('#searchCouponLevel').val());
                searched.type = parseInt($('#searchType').val());
                _.each(['status', 'type', 'user_type', 'coupon_level'], function (k) {
                    if (searched[k] != -1) options[k] = searched[k];
                })
                if (searched.created_at) {
                    options.created_at = searched.created_at;
                }
                if (searched.lost_days) {
                    options.lost_days = parseInt(searched.lost_days);
                }
                ADQ.utils.saveSearched('stats_missed_vips', searched);
                return options;
            },
            doSearch: function () {
                var options = this._getSearchOption();
                options.$page = 1;
                options.$size = 300;
                app.navigate(ADQ.utils.composeQueryString('#stats/vips/missed/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.stats_missed_vips_searched || '{}'),
                    overview: this.collection.overview,
                    coupons: this.coupons.toJSON()
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/vips/missed/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('#searchCreatedAt').datetimepicker({
                    defaultDate: ADQ.utils.yesterday('YYYY-MM-DD'),
                    format: 'YYYY-MM-DD'
                });
                $('#inputStatus').multiselect();
                $('#sendCoupon').magnificPopup({
                    items: {
                        src: '#addCouponPanel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    disableOn: function () {
                        return that.checkedUids.length > 0;
                    },
                    callbacks: {
                        beforeOpen: function () {
                            var coupons = {};
                            $('#addCoupon').off('click').click(function () {
                                var template_id = parseInt($('#inputCoupon').val()),
                                    count = parseInt($('#inputCount').val()),
                                    coupon = that.coupons.get(template_id);
                                if (coupons[template_id] == undefined) coupons[template_id] = 0;
                                coupons[template_id] += count;
                                $('#chosenCoupon').append('<tr><td>' + coupon.get('desc') + '</td><td>' + count + '</td></tr>');
                            });
                            $('#submitAddCoupon').off('click').click(function () {
                                $.magnificPopup.close();
                                $.post('admin/coupon/add/', JSON.stringify({
                                    uids: that.checkedUids,
                                    coupons: coupons
                                })).fail(function (data) {
                                    ADQ.notify.notifyResp(data);
                                }).then(function (data) {
                                    ADQ.notify.success();
                                    $.post('/admin/stats/vips/missed/', JSON.stringify({ ids: that.checkedIds, status: 4 })).then(function () {
                                        that.collection.fetch({
                                            reset: true,
                                            data: that.options
                                        })
                                    })
                                }
                                    );
                            });
                        },

                    }
                });
                $('#updateStatus').magnificPopup({
                    items: {
                        src: '#updateStatusPannel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    disableOn: function () {
                        return that.checkedUids.length > 0;
                    },
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitUpdateStatus').off('click').click(function () {
                                $.magnificPopup.close();
                                var status = $('#inputStatus').val(),
                                    final = 0;
                                _.each(status, function (s) {
                                    final |= s;
                                })
                                $.post(that.collection.url, JSON.stringify({
                                    ids: that.checkedIds,
                                    status: final
                                })).fail(function (data) {
                                    ADQ.notify.notifyResp(data);
                                }).then(function (data) {
                                    ADQ.notify.success();
                                    that.collection.fetch({
                                        reset: true,
                                        data: that.options
                                    })
                                    that.checkedIds = [];
                                    that.checkedUids = [];
                                });
                            });
                        },

                    }
                });
                $('#inputCoupon').multiselect({
                    enableFiltering: true,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: 250,
                })
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/vips/missed/');
                return this;
            },
            load: function () {
                this.coupons.fetch({
                    reset: true,
                    data: {
                        $size: -1,
                        title: JSON.stringify({ '$like': "心跳" })
                    }
                })
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var MissedVipsListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "vips/MissedVips.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new MissedVipsListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var BackVipsListView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
                'click #export': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new vipsModelCls.BackVipsCollection();
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            exportData: function () {
                ADQ.notify.warning('警告', '导出中，请等待');
                ADQ.exportData(this.collection.url, this.options);
            },
            _getSearchOption: function(){

            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.calc_at_lower = $('#searchCalcAtLower').val();
                searched.calc_at_upper = $('#searchCalcAtUpper').val();
                searched.call_at_lower = $('#searchCallAtLower').val();
                searched.call_at_upper = $('#searchCallAtUpper').val();
                if (searched.calc_at_lower || searched.calc_at_upper) {
                    options.calc_at = {};
                    if (searched.calc_at_lower) options.calc_at.$gte = searched.calc_at_lower;
                    if (searched.calc_at_upper) options.calc_at.$lt = searched.calc_at_upper;
                }
                if (searched.call_at_lower || searched.call_at_upper) {
                    options.call_at = {};
                    if (searched.call_at_lower) options.call_at.$gte = searched.call_at_lower;
                    if (searched.call_at_upper) options.call_at.$lt = searched.call_at_upper;
                }
                ADQ.utils.saveSearched('stats_back_vips', searched);
                app.navigate(ADQ.utils.composeQueryString('#stats/vips/back/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.stats_back_vips_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/vips/back/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('.date-box').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                ADQ.utils.getPaginator(that.options, this.collection.total, '#stats/vips/back/');
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var BackVipsListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "vips/BackVips.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new BackVipsListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var ActiveVipsListView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
                'change #selectAll': 'selectAll',
                'change .check-row': 'checkRow',
                'click #export': 'exportData',
            },

            initialize: function (options) {
                this.options = options;
                this.collection = new vipsModelCls.ActiveVipsCollection();
                this.checkedUids = [];
                this.collection.bind('change remove reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            exportData: function () {
                ADQ.notify.warning('警告', '导出中，请等待');
                ADQ.exportData(this.collection.url, this._getSearchOption());
            },
            selectAll: function (e) {
                var checked = $(e.target).is(':checked');
                $('.check-row').prop('checked', checked);
                if (!checked) {
                    this.checkedUids = [];
                }
                else {
                    this.checkedUids = this.collection.pluck('uid');
                }
                $('#selectTips').html('已选中' + this.checkedIds.length + '个');
            },
            checkRow: function (e) {
                var tr = $(e.target).closest('tr'),
                    uid = tr.data('uid');
                if ($(e.target).is(':checked')) {
                    this.checkedUids.push(uid);
                } else {
                    this.checkedUids = _.without(this.checkedUids, uid);
                }
                $('#selectTips').html('已选中' + this.checkedUids.length + '个');
            },
            _getSearchOption: function () {
                var options = ADQ.utils.getAllInput('#sidebar_right'),
                    searched = ADQ.utils.getAllInput('#sidebar_right');
                searched.visit_status =parseInt($('#searchVisitStatus').val());
                searched.add_status = parseInt($('#searchAddStatus').val());
                if (searched.visit_status != -1 || searched.add_status != -1) {
                    options.status = 0;
                    if (searched.visit_status != -1) options.status |= searched.visit_status;
                    if (searched.add_status != -1) options.status |= searched.add_status;
                }
                options.$size = -1;
                ADQ.utils.saveSearched('stats_active_vips', searched);
                return options;
            },
            doSearch: function () {
                var options = this._getSearchOption();
                app.navigate(ADQ.utils.composeQueryString('#stats/vips/active/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.stats_active_vips_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#stats/vips/active/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                $('.date-input').datetimepicker({
                    format: 'YYYY-MM-DD'
                });
                $('#inputStatus').multiselect();
                $('#updateStatus').magnificPopup({
                    items: {
                        src: '#updateStatusPannel',
                        type: 'inline'
                    },
                    midClick: true,
                    closeOnBgClick: false,
                    disableOn: function () {
                        return that.checkedUids.length > 0;
                    },
                    callbacks: {
                        beforeOpen: function () {
                            $('#submitUpdateStatus').off('click').click(function () {
                                $.magnificPopup.close();
                                var status = $('#inputStatus').val(),
                                    final = 0;
                                _.each(status, function (s) {
                                    final |= s;
                                })
                                $.post(that.collection.url, JSON.stringify({
                                    ids: that.checkedUids,
                                    status: final
                                })).fail(function (data) {
                                    ADQ.notify.notifyResp(data);
                                }).then(function (data) {
                                    ADQ.notify.success();
                                    that.collection.fetch({
                                        reset: true,
                                        data: that.options
                                    })
                                    that.checkedUids = [];
                                }
                                    );
                            });
                        },

                    }
                });
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var ActiveVipsListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "vips/ActiveVips.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new ActiveVipsListView(this.options);
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        return {
            MissedVipsListPage: MissedVipsListPage,
            BackVipsListPage: BackVipsListPage,
            ActiveVipsListPage: ActiveVipsListPage
        };
    } ();

    var reportViewCls = function () {
        var _loadDatePicker = function(options) {
            $('#dateFilter').daterangepicker({
                autoApply: true,
                alwaysShowCalendars: true,
                locale: {
                    format: 'YYYY-MM-DD',
                    separator: ' ~ '
                },
                startDate: ADQ.utils.fromDate(options.dateRange[0], "YYYY-MM-DD"),
                endDate: ADQ.utils.fromDate(options.dateRange[1], "YYYY-MM-DD"),
                opens: "center",
                ranges: {
                    'today': [moment(), moment()],
                    'yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                    'last 7 days': [moment().subtract(7, 'days'), moment().subtract(1, 'days')],
                    'last 30 days': [moment().subtract(30, 'days'), moment().subtract(1, 'days')],
                    'last 90 days': [moment().subtract(90, 'days'), moment().subtract(1, 'days')],
                },
                minDate: '2016-08-13',
                maxDate: moment(),
            }, function(start, end, label) {
                if (options.callback) options.callback(start, end, label);
            });
        };
        var _getDateRange = function () {
            var value = $('#dateFilter').val(),
                t = value.split('~');
            for (var i = 0; i < t.length; ++i){
                t[i] = t[i].trim();
            }
            return t;
        };
        var Overview = Backbone.View.extend({
            tagName: "div",
            initialize: function (options) {
                this.options = options;
                this.user = new reportModelCls.UserOverview();
                this.activity = new reportModelCls.ActivityOverview();
                this.cost = new reportModelCls.CostOverview();

                this.user.bind('change reset', this.renderWithData, this);
                this.activity.bind('change reset', this.renderWithData, this);
                this.cost.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    user: this.user.toJSON(),
                    activity: this.activity.toJSON(),
                    cost: this.cost.toJSON(),
                }));
                var that = this;
                return this;
            },
            load: function () {
                this.user.fetch({
                    reset: true,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
                this.cost.fetch({
                    reset: true,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
                this.activity.fetch({
                    reset: true,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            },
        });
        var OverviewPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Overview.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new Overview(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var DailyReportView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.DailyReport();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.model.list,
                    options: this.options
                }));
                _loadDatePicker(this.options);
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var DailyReportPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/DailyReport.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new DailyReportView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var ShippingView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.ShippingReport();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.model.list,
                    info: this.model.info,
                    options: this.options
                }));
                _loadDatePicker(this.options);
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var ShippingPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Shipping.html",
            render: function () {
                var yesterday = ADQ.utils.yesterday('YYYY-MM-DD'),
                    dateRange = [yesterday, yesterday],
                    view = new ShippingView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var ProfitView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.DailyReport();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.model.list,
                    options: this.options
                }));
                _loadDatePicker(this.options);
                var x = _.pluck(this.model.list, '_id'),
                    profit = _.pluck(this.model.list, 'real_profit'),
                    profitRate = _.pluck(this.model.list, 'real_profit_rate');
                $('#chart').highcharts({
                    chart: {
                        zoomType: 'xy'
                    },
                    title: {
                        text: '利润走势曲线'
                    },
                    xAxis: [{
                        categories: x,
                        crosshair: true
                    }],
                    yAxis: [{   //利润值
                        labels: {
                            style: {
                                color: 'blue',
                            }
                        },
                        title: {
                            text: '金额',
                            style: {
                                color: 'blue'
                            }
                        },
                    }, {    //比例
                            title: {
                                text: '利润率',
                            },

                        opposite: true
                    }],
                    tooltip: {
                        shared: true
                    },
                    series: [{
                        name: '金额',
                        type: 'spline',
                        data: profit,
                        tooltip: {
                            pointFormat: '{series.name}: <b>{point.y: .2f}</b>'
                        }
                    }, {
                            name: '利润率',
                            type: 'spline',
                            data: profitRate,
                            yAxis: 1,
                            tooltip: {
                                pointFormat: '<br/>{series.name}: <b>{point.y: .2f}</b>'
                            },
                    }]
                });
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var ProfitPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Profit.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new ProfitView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var RechargeView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.RechargeReport();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.options.userType = parseInt($('#userType').val());
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    item: this.model.toJSON(),
                    options: this.options
                }));
                _loadDatePicker(this.options);
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                        user_type: this.options.userType
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var RechargePage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Recharge.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new RechargeView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var TacticsView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.TacticsReport();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                var rechargeLower = parseInt($('#rechargeLower').val()) || 0,
                    rechargeUpper = parseInt($('#rechargeUpper').val()) || 0;
                if (rechargeLower || rechargeUpper) {
                    this.options.rechargeRange = [rechargeLower];
                    if (rechargeUpper) {
                        this.options.push(rechargeUpper);
                    }
                }
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.model.list,
                    total: this.model.total,
                    options: this.options
                }));
                _loadDatePicker(this.options);
                var countOptions = ADQ.utils.getHighChartPieOptions(),
                    amountOptions = ADQ.utils.getHighChartPieOptions(),
                    countSeries = countOptions.series[0].data,
                    amountSeries = amountOptions.series[0].data;
                countOptions.title.text = '人数占比';
                amountOptions.title.text = '金额占比';
                _.each(this.model.list, function (item) {
                    countSeries.push({
                        name: item.id,
                        y: item.count
                    });
                    amountSeries.push({
                        name: item.id,
                        y: item.amount
                    })
                });
                $('#countPie').highcharts(countOptions);
                $('#amountPie').highcharts(amountOptions);

                return this;
            },
            load: function () {
                var data = {
                    date_range: this.options.dateRange.join(','),
                };
                if (this.options.rechargeRange) {
                    data.recharge_range = this.options.rechargeRange.join(',')
                }
                this.model.fetch({
                    reset: true,
                    data: data,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var TacticsPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Tactics.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new TacticsView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var ResourceView = Backbone.View.extend({
            events: {
                'click #search': 'doSearch',
                'shown.bs.tab a.chart-tab': "onSelectTab"
            },
            initialize: function (options) {
                this.options = options;
                this.modelDct = {
                    'coin': new reportModelCls.CoinReport(),
                    'coupon': new reportModelCls.CouponReport(),
                    'credit': new reportModelCls.CreditReport()
                }
                var that = this;
                _.each(this.modelDct, function (v, k){
                    v.bind('change reset', that.renderWithData, that);
                });
            },
            onSelectTab: function (e) {
                e.preventDefault();
                var ref = $(e.target).attr('href');
                $(ref).highcharts().reflow();
                return this;
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.options.resourceType = $('#resourceType').val();
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                var model = this.modelDct[this.options.resourceType || 'coin'];
                this.$el.html(this.template({
                    item: model.toJSON(),
                    options: this.options
                }));
                _loadDatePicker(this.options);
                //走势曲线，产生与消耗 || 留存 || 消费玩家
                var ccc = ADQ.utils.getHighChartLineOptions(),
                    bc = ADQ.utils.getHighChartLineOptions(),
                    cuc = ADQ.utils.getHighChartLineOptions();
                _.each([ccc, ccc, bc, cuc], function (t) {
                    t.series.push({name:'', data: []});
                })
                ccc.series[0].name = '产生';
                ccc.series[1].name = '消耗';
                bc.series[0].name = '余额';
                cuc.series[0].name = '消耗用户数';
                ccc.xAxis
                _.each(model.list, function (item) {
                    ccc.xAxis.categories.push(item._id);
                    bc.xAxis.categories.push(item._id);
                    cuc.xAxis.categories.push(item._id);
                    ccc.series[0].data.push(item.gen_amount);
                    ccc.series[1].data.push(item.cost_amount);
                    bc.series[0].data.push(item.balance);
                    cuc.series[0].data.push(item.cost_user);
                });
                $('#create_cost').highcharts(ccc);
                $('#balance').highcharts(bc);
                $('#cost_user').highcharts(cuc);

                //产生与消耗渠道的饼图
                var createPie = ADQ.utils.getHighChartPieOptions(),
                    costPie = ADQ.utils.getHighChartPieOptions(),
                    that = this;
                _.each(model.gen_dist, function (item) {
                    createPie.series[0].data.push({
                        name: item.type,
                        y: item.amount
                    });
                });
                _.each(model.cost_dist, function (item) {
                    costPie.series[0].data.push({
                        name: item.type,
                        y: item.amount
                    });
                });
                $('#create_channel').highcharts(createPie);
                $('#cost_channel').highcharts(costPie);
                return this;
            },
            load: function () {
                var model = this.modelDct[this.options.resourceType || 'coin'];
                model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var ResourcePage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Resource.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new ResourceView({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        var Top100View = Backbone.View.extend({
            events: {
                'click #search': 'doSearch'
            },
            initialize: function (options) {
                this.options = options;
                this.model = new reportModelCls.Top100List();
                this.model.bind('change reset', this.renderWithData, this);
            },
            doSearch: function () {
                this.options.dateRange = _getDateRange();
                this.load();
            },
            render: function () {
                this.$el.html("");
                $(window).scrollTop(0);
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.model.list,
                    options: this.options
                }));
                _loadDatePicker(this.options);
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: this.options.$orderby || 'rank',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        var desc = false;
                        if (field[0] == '-') {
                            desc = true;
                            field = field.substr(1);
                        }
                        that.model.list =  _.sortBy(that.model.list, function (o) {
                            if (desc) return 0 - o[field];
                            return o[field];
                        });
                        that.renderWithData();
                    }
                });
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true,
                    data: {
                        date_range: this.options.dateRange.join(','),
                    },
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    }
                })
            }
        });
        var Top100Page = Backbone.View.extend({
            el: "#content_wrapper",
            template: "report/Top100.html",
            render: function () {
                var today = moment().format('YYYY-MM-DD'),
                    dateRange = [today, today],
                    view = new Top100View({
                        dateRange: dateRange
                    });
                view.template = this.template;
                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();
                return this;
            }
        });

        return {
            OverviewPage: OverviewPage,
            DailyReportPage: DailyReportPage,
            ProfitPage: ProfitPage,
            RechargePage: RechargePage,
            TacticsPage: TacticsPage,
            ResourcePage: ResourcePage,
            ShippingPage: ShippingPage,
            Top100Page: Top100Page
        };
    } ();

    var consoleViewCls = function () {
        var UserListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click a.onClickDelete': 'toDelete',
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new consoleModelCls.UserCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            toDelete: function (e) {
                var userId = $(e.currentTarget).closest('tr').data('id'),
                    thisView = this;
                $.ajax({
                    url: '/admin/user/' + userId,
                    type: 'delete',
                    success: function () {
                        thisView.collection.remove(new opModelCls.Template({
                            id: userId
                        }));
                        ADQ.notify.success();
                    },
                    error: function (data) {
                        ADQ.notify.notifyResp(data);
                    }
                });
            },
            doSearch: function () {
                var options = {},
                    searched = {};
                searched.email = $('#searchEmail').val();
                searched.role = parseInt($('#searchRole').val());
                if (searched.role != -1) {
                    options.role = searched.role;
                }
                if (searched.email) {
                    options.email = searched.email;
                }
                ADQ.utils.saveSearched('console_user', searched);
                app.navigate(ADQ.utils.composeQueryString('#console/user/', options), {
                    trigger: true
                });
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    roleDict: USER_ROLE,
                    searched: JSON.parse(localStorage.console_user_searched || '{}'),
                    info: USER_INFO.info,
                }));
                var that = this;
                ADQ.utils.getPaginator(that.options, this.collection.total, '#console/user/');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var UserListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "console/UserList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new UserListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var UserDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #userSave': 'toSave'
            },
            initialize: function (options) {
                this.model = new consoleModelCls.User();
                this.model.set('id', options.userId);
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            toSave: function (e) {
                e.preventDefault();
                var attrs = {
                    'nickname': $('#inputNickname').val(),
                    'role': parseInt($('#inputRole').val()),
                };
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                var data = this.model.toJSON();
                data.ori_role = USER_INFO.info.role;
                this.$el.html(this.template(data));
                $('#inputRole').multiselect();
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true
                });
            }
        });
        var UserDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "console/UserDetail.html",
            initialize: function (userId) {
                this.userId = userId;
            },
            render: function () {
                var view = new UserDetailView(this.userId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var PermListView = Backbone.View.extend({
            tagName: "div",
            initialize: function (options) {
                this.options = options;
                this.collection = new consoleModelCls.PermissionCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    models: this.collection.models,
                    roleDict: USER_ROLE,
                }));
                var that = this;
                ADQ.utils.getPaginator(that.options, this.collection.total, '#console/perm/');
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                        $('#content').append('<h4 class="text-muted">无数据</h4>');
                    },
                });
            }
        });
        var PermListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "console/PermissionList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new PermListView(this.options);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });
        var PermDetailView = Backbone.View.extend({
            tagName: "div",
            className: "panel-body pn",
            events: {
                'click #permSave': 'toSave'
            },
            initialize: function (options) {
                this.model = new consoleModelCls.Permission();
                this.model.set('id', options.permId);
                this.model.bind('change reset', this.renderWithData, this);
            },
            render: function () {
                this.$el.html("");
                return this;
            },
            toSave: function (e) {
                e.preventDefault();
                var attrs = {
                    'min_role': parseInt($('#inputMinRole').val()),
                };
                this.model.save(attrs, {
                    patch: true,
                    success: function (model, response) {
                        ADQ.notify.success('提示', '保存成功！');
                        setTimeout(function () {
                            history.back();
                        }, 500);
                    },
                    error: function (model, response) {
                        ADQ.notify.notifyResp(response);
                    }
                });

                return false;
            },
            renderWithData: function () {
                var data = this.model.toJSON();
                this.$el.html(this.template(data));
                $('#inputMinRole').multiselect();
                $(window).scrollTop(0);
                return this;
            },
            load: function () {
                this.model.fetch({
                    reset: true
                });
            }
        });
        var PermDetailPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "console/PermissionDetail.html",
            initialize: function (permId) {
                this.permId = permId;
            },
            render: function () {
                var view = new PermDetailView(this.permId);
                view.template = this.template;

                this.$el.empty();
                this.$el.append(view.render().el);
                view.load();

                return this;
            }
        });

        var RecordListView = Backbone.View.extend({
            tagName: "div",
            events: {
                'click #search': 'doSearch',
                'click .show-info': 'showInfo'
            },
            initialize: function (options) {
                this.options = options;
                this.collection = new consoleModelCls.RecordCollection();
                this.collection.bind('change reset remove', this.renderWithData, this);
            },
            render: function () {
                this.$el.html('');
                $(window).scrollTop(0);
                return this;
            },
            doSearch: function () {
                var options = ADQ.utils.getAllInput('#sidebar_right');
                ADQ.utils.saveSearched('record', options);
                app.navigate(ADQ.utils.composeQueryString('#console/record/', options), {
                    trigger: true
                });
            },
            showInfo: function (e) {
                e.preventDefault();
                var content = $(e.target).data('content'),
                    rows = content.split(', '),
                    $gen_html = $('<ul></ul>');
                _.each(rows, function (row) {
                    if (row.length > 100) {
                        var rs = row.split(','),
                        row = rs.join('<br/>')
                    }
                    $gen_html.append($('<li></li>').append(row));
                });
                $.dialog({
                    'title': '内容详情',
                    'content': $gen_html.html(),
                    'backgroundDismiss': true,
                    'theme': 'bootstrap',
                })
                return false;
            },
            renderWithData: function () {
                this.$el.html(this.template({
                    items: this.collection.toJSON(),
                    searched: JSON.parse(localStorage.record_searched || '{}'),
                }));
                var that = this;
                ADQ.utils.renderTable('main-list', {
                    $orderby: that.options.$orderby || 'id',
                    sortCallback: function (field) {
                        that.options.$orderby = field;
                        that.options.$page = 1;
                        var newUrl = ADQ.utils.composeQueryString('#console/record/', that.options);
                        app.navigate(newUrl, {
                            trigger: true
                        });
                    }
                });
                ADQ.utils.getPaginator(this.options, this.collection.total, '#console/record/');
                $('.date-input').datetimepicker({
                    format: 'YYYY-MM-DD HH:mm:ss',
                });
                return this;
            },
            load: function () {
                this.collection.fetch({
                    reset: true,
                    data: this.options,
                    error: function (c, r, o) {
                        ADQ.notify.notifyResp(r);
                    },
                });
            }
        });
        var RecordListPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "console/RecordList.html",
            initialize: function (options) {
                this.options = options;
            },
            render: function () {
                var view = new RecordListView(this.options);
                view.template = this.template;
                this.$el.empty().append(view.render().el);
                view.load();
                return this;
            }
        });


        return {
            UserListPage: UserListPage,
            UserDetailPage: UserDetailPage,
            PermListPage: PermListPage,
            PermDetailPage: PermDetailPage,
            RecordListPage: RecordListPage
        };
    } ();

    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "luckyTemplateList",
            "template/(?*queryString)": "luckyTemplateList",
            "template/:id/": "luckyTemplateDetail",
            "feedback/(?*queryString)": "luckyFeedbackList",
            "order/(?*queryString)": "luckyOrderList",
            "order/:id/(?*queryString)": "luckyOrderDetail",
            "redenvelope/(?*queryString)": "luckyRedEnvelopeList",
            "show/(?*queryString)": "luckyShowList",
            "show/:id/(?*queryString)": "luckyShowDetail",
            "bigshow/(?*queryString)": "luckyBigShowList",
            "bigshow/:id/(?*queryString)": "luckyBigShowDetail",
            "category/": "luckyCategoryList",
            "virtual/(?*queryString)": "luckyVirtualList",
            "virtual/:id/": "luckyVirtualDetail",
            "coupon/template/(?*queryString)": "luckyCouponTemplateList",
            "coupon/template/:id/": "luckyCouponTemplateDetail",
            "abtest/(?*queryString)": "luckyABTestList",
            "abtest/:id/": "luckyABTestDetail",
            "notification/(?*queryString)": "luckyNotificationList",
            "notification/:id/": "luckyNotificationDetail",

            "preset/banner/(?*queryString)": "presetBannerList",
            "preset/banner/:id/": "presetBannerDetail",
            "preset/discovery/(?*queryString)": "presetDiscoveryList",
            "preset/discovery/:id/": "presetDiscoveryDetail",
            "preset/loading/(?*queryString)": "presetLoadingList",
            "preset/loading/:id/": "presetLoadingDetail",
            "preset/shortcut/(?*queryString)": "presetShortcutList",
            "preset/shortcut/:id/": "presetShortcutDetail",
            "preset/theme/(?*queryString)": "presetThemeList",
            "preset/theme/:id/": "presetThemeDetail",
            "preset/homepage/(?*queryString)": "presetHomepageList",
            "preset/homepage/:id/": "presetHomepageDetail",
            "preset/(?*queryString)": "presetList",
            "preset/:id/": "presetDetail",

            "stats/account/(?*queryString)": "statsAccountDetail",
            "stats/activity/(?*queryString)": "statsActivityList",
            "stats/order/(?*queryString)": "statsOrderList",
            "stats/coupon/(?*queryString)": "statsCouponList",
            "stats/pay/(?*queryString)": "statsPayList",
            "stats/uninstall/(?*queryString)": "statsUninstallList",

            "stats/vips/missed/(?*queryString)": "statsMissedVipsList",
            "stats/vips/back/(?*queryString)": "statsBackVipsList",
            "stats/vips/active/(?queryString)": "statsActiveVipsList",

            "stats/report/daily/(?queryString)": "statsDailyReport",
            "stats/report/overview/": "statsReportOverview",
            "stats/report/profit/(?queryString)": "statsProfitReport",
            "stats/report/recharge/(?queryString)": "statsRechargeReport",
            "stats/report/resource/(?queryString)": "statsResourceReport",
            "stats/report/tactics/(?queryString)": "statsTacticsReport",
            "stats/report/shipping/(?queryString)": "statsShippingReport",
            "stats/report/top100/(?queryString)": "statsTop100List",

            "goods/source/(?*queryString)": "goodsSourceList",
            "goods/source/:id/": "goodsSourceDetail",
            "goods/brand/(?*queryString)": "goodsBrandList",
            "goods/brand/:id/": "goodsBrandDetail",
            "goods/category/(?*queryString)": "goodsCategoryList",
            "goods/category/:id/": "goodsCategoryDetail",
            "goods/(?*queryString)": "goodsList",
            "goods/:id/": "goodsDetail",

            "console/user/(?*queryString)": "consoleUserList",
            "console/user/:id/": "consoleUserDetail",
            "console/perm/(?*queryString)": "consolePermList",
            "console/perm/:id/": "consolePermDetail",
            "console/record/(?*queryString)": "consoleRecordList",
        },
        before: function () {
            var key = $('#sidebar_right').data('key') || ADQ.utils.getCurrentKey(),
                align = localStorage.getItem(key + '_align') || 'c';
            ADQ.utils.setrs(align);
        },
        after: function () {
            $('body').on('keypress', '#sidebar_right', function (e) {
                e.stopImmediatePropagation();
                if (e.which == 13) $('#search').click();
            });
        },
        prepareSearch: function (key, reflush) {
            if (reflush) {
                switch (key) {
                    case "template":
                        ADQ.utils.saveSearched(key, {
                            status: 1,
                            type: -1
                        });
                        break;
                    case "order":
                        ADQ.utils.saveSearched(key, {
                            status: 5
                        });
                        break;
                    case "show":
                        ADQ.utils.saveSearched(key, {
                            status: 2
                        });
                        break;
                    case "stats_activity":
                    case "stats_order":
                    case "stats_pay":
                    case "stats_coupon":
                        ADQ.utils.saveSearched(key, {
                            created_at_lower: moment().format('YYYY-MM-DD'),
                            created_at_upper: moment().add(1, 'days').format('YYYY-MM-DD')
                        });
                        break;
                    default:
                        ADQ.utils.saveSearched(key, {});
                        break;
                }
            }
        },
        luckyTemplateList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('template', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.TemplateListPage(params);
            page.render();
        },
        luckyFeedbackList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-created_at';
            }
            var page = new opViewCls.FeedbackListPage(params);
            page.render();
        },
        luckyOrderList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('order', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) params.$orderby = 'updated_at';
            var page = new opViewCls.OrderListPage(params);
            page.render();
        },
        luckyRedEnvelopeList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) params.$orderby = '-updated_at';
            var page = new opViewCls.RedEnvelopeListPage(params);
            page.render();
        },
        luckyShowList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('show', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.ShowListPage(params);
            page.render();
        },
        luckyBigShowList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.BigShowListPage(params);
            page.render();
        },
        luckyCategoryList: function () {
            var page = new opViewCls.CategoryListPage();
            page.render();
        },
        luckyVirtualList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.VirtualListPage(params);
            page.render();
        },
        luckyCouponTemplateList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('couponTempalte', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.CouponTemplateListPage(params);
            page.render();
        },
        luckyABTestList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = 'id';
            }
            var page = new opViewCls.ABTestListPage(params);
            page.render();
        },
        luckyNotificationList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new opViewCls.NotificationListPage(params);
            page.render();
        },
        luckyTemplateDetail: function (templateID) {
            var luckyTemplateDetailPage = null;
            if (templateID == "add") {
                luckyTemplateDetailPage = new opViewCls.TemplateDetailPage({});
            } else {
                luckyTemplateDetailPage = new opViewCls.TemplateDetailPage({
                    templateID: templateID
                });
            }
            luckyTemplateDetailPage.render();
        },
        luckyOrderDetail: function (orderID) {
            var page = null;
            page = new opViewCls.OrderDetailPage({
                orderID: orderID
            });
            page.render();
        },
        luckyShowDetail: function (showId, qs) {
            var page = null;
            if (showId == 'add') {
                var params = ADQ.utils.parseQueryString(qs);
                page = new opViewCls.ShowDetailPage({
                    params: params
                });
            } else {
                page = new opViewCls.ShowDetailPage({
                    showId: showId
                });
            }
            page.render();
        },
        luckyBigShowDetail: function (id, qs) {
            var page = null,
                params = ADQ.utils.parseQueryString(qs);
            page = new opViewCls.BigShowDetailPage({
                template_id: id,
                $page: 1,
                $size: 10,
                params: params
            });
            page.render();
        },
        luckyVirtualDetail: function (virtualId) {
            var page = null;
            if (virtualId == "add") {
                page = new opViewCls.VirtualDetailPage({});
            } else {
                page = new opViewCls.VirtualDetailPage({
                    virtualId: virtualId
                });
            }
            page.render();
        },
        luckyCouponTemplateDetail: function (couponTemplateId) {
            var page = null;
            if (couponTemplateId == "add") {
                page = new opViewCls.CouponTemplateDetailPage({});
            } else {
                page = new opViewCls.CouponTemplateDetailPage({
                    couponTemplateId: couponTemplateId
                });
            }
            page.render();
        },
        luckyABTestDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new opViewCls.ABTestDetailPage({});
            } else {
                page = new opViewCls.ABTestDetailPage({
                    id: id
                });
            }
            page.render()
        },
        luckyNotificationDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new opViewCls.NotificationDetailPage({});
            } else {
                page = new opViewCls.NotificationDetailPage({
                    id: id
                });
            }
            page.render()
        },
        presetList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.PresetListPage(params);
            page.render();
        },
        presetBannerList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.BannerListPage(params);
            page.render();
        },
        presetDiscoveryList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.DiscoveryListPage(params);
            page.render();
        },
        presetLoadingList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.LoadingListPage(params);
            page.render();
        },
        presetShortcutList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.ShortcutListPage(params);
            page.render();
        },
        presetThemeList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.ThemeListPage(params);
            page.render();
        },
        presetHomepageList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(parmas.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            var page = new presetViewCls.HomepageListPage(params);
            page.render();
        },
        presetDetail: function (presetId) {
            var page = null;
            if (presetId == "add") {
                page = new presetViewCls.PresetDetailPage({});
            } else {
                page = new presetViewCls.PresetDetailPage({
                    id: presetId
                });
            }
            page.render();
        },
        presetBannerDetail: function (bannerId) {
            var page = null;
            if (bannerId == 'add') {
                page = new presetViewCls.BannerDetailPage({});
            } else {
                page = new presetViewCls.BannerDetailPage({
                    bannerId: bannerId
                });
            }
            page.render();
        },
        presetDiscoveryDetail: function (discoveryId) {
            var page = null;
            if (discoveryId == 'add') {
                page = new presetViewCls.DiscoveryDetailPage({});
            } else {
                page = new presetViewCls.DiscoveryDetailPage({
                    discoveryId: discoveryId
                });
            }
            page.render();
        },
        presetLoadingDetail: function (loadingId) {
            var page = null;
            if (loadingId == 'add') {
                page = new presetViewCls.LoadingDetailPage({});
            } else {
                page = new presetViewCls.LoadingDetailPage({
                    loadingId: loadingId
                });
            }
            page.render();
        },
        presetShortcutDetail: function (shortcutId) {
            var page = null;
            if (shortcutId == 'add') {
                page = new presetViewCls.ShortcutDetailPage({});
            } else {
                page = new presetViewCls.ShortcutDetailPage({
                    shortcutId: shortcutId
                });
            }
            page.render();
        },
        presetThemeDetail: function (themeId) {
            var page = null;
            if (themeId == 'add') {
                page = new presetViewCls.ThemeDetailPage({});
            } else {
                page = new presetViewCls.ThemeDetailPage({
                    themeId: themeId
                });
            }
            page.render();
        },
        presetHomepageDetail: function (homepageId) {
            var page = null;
            if (homepageId == 'add') {
                page = new presetViewCls.HomepageDetailPage({});
            } else {
                page = new presetViewCls.HomepageDetailPage({
                    homepageId: homepageId
                });
            }
            page.render();
        },
        statsAccountDetail: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new statsViewCls.AccountDetailPage(params);
            page.render();
        },
        statsActivityList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('stats_activity', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = 20;
            if (!params.$orderby) {
                params.$orderby = '-created_at';
            }
            var page = new statsViewCls.ActivityListPage(params);
            page.render();
        },
        statsOrderList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('stats_order', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = 10;
            if (!params.$orderby) {
                params.$orderby = '-created_at';
            }
            var page = new statsViewCls.OrderListPage(params);
            page.render();
        },
        statsCouponList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('stats_coupon', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-start_ts';
            }
            var page = new statsViewCls.CouponListPage(params);
            page.render();
        },
        statsPayList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('stats_pay', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-created_at';
            }
            var page = new statsViewCls.PayListPage(params);
            page.render();
        },
        statsUninstallList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            if (!params.$orderby) {
                params.$orderby = '-remove_at';
            }
            var page = new statsViewCls.UninstallListPage(params);
            page.render();
        },
        statsMissedVipsList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = 300;
            if (!params.created_at) params.created_at = ADQ.utils.now('YYYY-MM-DD');
            if (!params.$orderby) {
                params.$orderby = 'id';
            }
            var page = new vipsViewCls.MissedVipsListPage(params);
            page.render();
        },
        statsBackVipsList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            if (!params.calc_at) params.calc_at = ADQ.utils.now('YYYY-MM-DD');
            var page = new vipsViewCls.BackVipsListPage(params);
            page.render();
        },
        statsActiveVipsList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            if (!params.created_at) params.created_at = ADQ.utils.now('YYYY-MM-DD');
            var page = new vipsViewCls.ActiveVipsListPage(params);
            page.render();
        },
        statsDailyReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.DailyReportPage(params);
            page.render();
        },
        statsReportOverview: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.OverviewPage(params);
            page.render();
        },
        statsProfitReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.ProfitPage(params);
            page.render();
        },
        statsRechargeReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.RechargePage(params);
            page.render();
        },
        statsResourceReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.ResourcePage(params);
            page.render();
        },
        statsTacticsReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.TacticsPage(params);
            page.render();
        },
        statsShippingReport: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.ShippingPage(params);
            page.render();
        },
        statsTop100List: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            var page = new reportViewCls.Top100Page(params);
            page.render();
        },
        consoleUserList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            this.prepareSearch('console_user', params._reflush);
            delete params._reflush;
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = PAGE_SIZE;
            var page = new consoleViewCls.UserListPage(params);
            page.render();
        },
        consoleUserDetail: function (userId) {
            var page = null;
            page = new consoleViewCls.UserDetailPage({
                userId: userId
            });
            page.render();
        },
        consolePermList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = PAGE_SIZE;
            var page = new consoleViewCls.PermListPage(params);
            page.render();
        },
        consolePermDetail: function (permId) {
            var page = null;
            if (permId == 'add') {
                page = new consoleViewCls.PermDetailPage({});
            } else {
                page = new consoleViewCls.PermDetailPage({
                    permId: permId
                });
            }
            page.render();
        },
        consoleRecordList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page) : 1;
            params.$size = PAGE_SIZE;
            var page = new consoleViewCls.RecordListPage(params);
            page.render();
        },
        goodsList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new goodsViewCls.GoodsListPage(params);
            page.render();
        },
        goodsDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new goodsViewCls.GoodsDetailPage({});
            } else {
                page = new goodsViewCls.GoodsDetailPage({
                    id: id
                });
            }
            page.render();
        },
        goodsSourceList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new goodsViewCls.SourceListPage(params);
            page.render();
        },
        goodsSourceDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new goodsViewCls.SourceDetailPage({});
            } else {
                page = new goodsViewCls.SourceDetailPage({
                    id: id
                });
            }
            page.render();
        },
        goodsBrandList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = PAGE_SIZE;
            if (!params.$orderby) {
                params.$orderby = '-updated_at';
            }
            var page = new goodsViewCls.BrandListPage(params);
            page.render();
        },
        goodsBrandDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new goodsViewCls.BrandDetailPage({});
            } else {
                page = new goodsViewCls.BrandDetailPage({
                    id: id
                });
            }
            page.render();
        },
        goodsCategoryList: function (queryString) {
            var params = ADQ.utils.parseQueryString(queryString);
            params.$page = params.$page ? parseInt(params.$page, 10) : 1;
            params.$size = -1;
            if (!params.$orderby) params.$orderby = '-updated_at';
            if (!params.parent_id) params.parent_id = '$null';

            var page = new goodsViewCls.CategoryListPage(params);
            page.render();
        },
        goodsCategoryDetail: function (id) {
            var page = null;
            if (id == "add") {
                page = new goodsViewCls.CategoryDetailPage({});
            } else {
                page = new goodsViewCls.CategoryDetailPage({
                    id: id
                });
            }
            page.render();
        },
    });

    return {
        init: function () {
            ADQ.fullscreen();
            ADQ.utils.loadTemplate([opViewCls, statsViewCls, reportViewCls, consoleViewCls, presetViewCls, goodsViewCls, vipsViewCls], function () {
                app = new AppRouter();
                Backbone.history.start();
            });
        }
    };

} (jQuery, _);
