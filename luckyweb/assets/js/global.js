'use strict';

var originalSync = Backbone.sync;
Backbone.sync = function(method, model, options) {

    options.beforeSend = function(xhr) {
        xhr.setRequestHeader('X-AUTH-USER', ADQ.utils.getCookie('lucky_user_id'));
        xhr.setRequestHeader('X-AUTH-TOKEN', ADQ.utils.getCookie('lucky_user_token'));
    };

    if (method === 'patch') options.type = 'PUT';
    if (method === 'delete') options.type = 'DELETE';
    return originalSync(method, model, options);
};

Backbone.Collection.prototype.save = function (options) {
    Backbone.sync("create", this, options);
};

Backbone.Router.prototype.before = function () {};
Backbone.Router.prototype.after = function () {};

Backbone.Router.prototype.route = function (route, name, callback) {
  if (!_.isRegExp(route)) route = this._routeToRegExp(route);
  if (_.isFunction(name)) {
    callback = name;
    name = '';
  }
  if (!callback) callback = this[name];

  var router = this;

  Backbone.history.route(route, function(fragment) {
    var args = router._extractParameters(route, fragment);

    router.before.apply(router, arguments);
    callback && callback.apply(router, args);
    router.after.apply(router, arguments);

    router.trigger.apply(router, ['route:' + name].concat(args));
    router.trigger('route', name, args);
    Backbone.history.trigger('route', router, name, args);
  });
  return this;
};


$.ajaxSetup({
    cache: false
});
$.ajaxPrefilter(function(options) {
    if (!options.beforeSend) {
        options.beforeSend = function(xhr) {
            xhr.setRequestHeader('X-AUTH-USER', ADQ.utils.getCookie('lucky_user_id'));
            xhr.setRequestHeader('X-AUTH-TOKEN', ADQ.utils.getCookie('lucky_user_token'));
        };
    }
});

window.USER_INFO = {

};

window.PAGE_SIZE = 15;

window.PRICE_UNITS = {
    0: 'RMB',
    1: 'USD'
};

window.ORDER_STATUS = {
    // "0": '已下单，待支付',
    // "1": '已支付，待确认',
    "2": '已支付, 待开奖',
    // "3": '未中奖',
    "4": '已中奖，待领奖',
    "5": '已领奖，待发货',
    "6": '已发货，待收货',
    "7": '已收货',
    "11": '已提交，处理中',
    "12": '已处理，待确认',
    "13": '已确认',
    "8": '已晒单',
};

window.RED_ORDER_STATUS = {
    "5": '已领奖，待发货',
    "6": '已发货，待收货',
    "7": '已收货',
}

window.SHOW_STATUS = {
    "1": "待晒单",
    "2": "待审核",
    "4": "已通过",
    "8": "未通过",
    "16": "预审核",
};

window.ERROR_CODE = {
    2: '参数错误',
    3: '需要HTTPS',
    4: '数据错误',
    5: '数据库错误',
    6: '缓存错误',
    101: '用户不存在',
    102: '密码错误',
    103: '验证码错误',
    104: '账户重复',
    105: 'TOKEN过期',
    106: '用户未激活',
    107: '权限不足',
    201: '商品库存不足',
};

window.TEMPLATE_STATUS = {
    "0": '待开始',
    "1": '进行中',
    "2": '已暂停'
};

window.ACTIVITY_STATUS = {
    0: '准备开始',
    1: '进行中',
    2: '待开奖',
    4: '已开奖',
    8: '已过期',
    16: '已暂停',
};

window.COUNTRY_CODE = {
    'cn': '中国',
    'vn': '越南',
    'id': '印尼'
};

window.DEVICE_TYPE = {
    '1': 'Android',
    '2': 'iOS',
    '4': 'wap',
    // '8': 'web',
    '16': 'iOS Pro',
    '32': 'iOS HD',
    '64': 'QG iOS',
    '128': 'QG PRO',
    '256': 'QG HD',
};

window.IOS_CHN = ['ios_pro', 'ios_hd', 'ios']
window.IOS_QG_CHN = ['qg_pro', 'qg_hd', 'qg_ios']
window.NOT_ANDROID_CHN = ['ios_pro', 'ios_hd', 'ios', 'qg_pro', 'qg_hd', 'qg_ios']

window.COUPON_TYPE = {
    '1': '直减',
    '2': '满减',
};

window.COUPON_STATUS = {
    '1': '未使用',
    '2': '已使用',
    '4': '已过期',
};

window.USER_TYPE = {
    '1': '新用户',
    '2': '次日用户',
    '3': '周用户',
    '4': '老用户',
};

window.PAY_TYPE = {
    0: '预付卡',
    1: 'NGANLUONG',
    2: '支付宝',
    3: '微信',
    4: '银联支付',
    5: '京东支付',
    6: '百度钱包',
    7: '爱贝支付',
    8: '支付宝WAP',
    9: 'wii pay',
    10: '友信',
    11: '爱贝WAP',
    12: '即刻支付WAP',
    13: 'swift'
};

window.USER_ROLE = {
    0: "未激活/黑名单用户",
    1: "一般用户",
    2: "运营人员",
    3: "高级运营",
    4: "运营主管",
    5: "开发者",
};

window.TRANSACTION_TYPE = {
    1: "充值",
    2: "系统奖励",
    4: "余额购买",
    8: "退款"
}

window.TRANSACTION_STATUS = {
    0: "进行中",
    1: "已完成",
    2: "失败"
}

window.CALLBACK_STATUS = {
    0: "未召回",
    1: "已电话",
    2: "已短信",
    4: "已发红包",
    8: "已召回"
}

window.SHIPPING_TYPE = {
    0: "普通商品",
    1: "手机号",
    2: "Q币",
    3: "夺宝币",
    4: "Email",
    5: "Gojek",
    6: "电费",
}

window.SHIP_STATUS = {
    0: "正常",
    1: "自动充值中",
    2: "自动充值失败",
    3: "自动发货中",
    4: "自动发货失败",
    5: "自动发货成功",
    98: '异常订单',
    99: "非法订单"
}

window.NOTIFY_STATUS = {
    0: "未发布",
    1: "已发布"
}

window.RED_ENVELOPE_STATUS = {
    0: "待兑换",
    1: "兑换失败",
    2: "兑换成功"
}

window.RESOURCE_DICT = {
    'coupon': '红包',
    'template': '活动模板',
    'awarded_order': '订单'
}

window.ACTION_DICT = {
    1: '创建',
    2: '更新',
    3: '删除'
}

window.MISSED_TYPE = {
    0: '大客户',
    1: '新增'
}

window.CALLBACK_STATUS = {
    0: '未召回',
    1: '已电话',
    2: '已短信',
    4: '已发红包',
    8: '已召回',
}

window.VIP_TYPE = {
    0: '周榜',
    1: '半月榜',
    2: '月榜'
}

window.SOURCE_TYPE = {
    2: '直付供应商',
    3: '自主发货',
    4: '其他',
    5: '月结供应商'
}

window.SERVER_REGION = {
    1: {
        code: 'tw',
        areaName: '台湾',
        server: "http://tw.lucky-gou.com",
        currency: "twd"
    },
    2: {
        code: 'en',
        areaName: "America",
        server: "http://us.lucky-gou.com",
        currency: "usd",
    },
    3: {
        code: 'eu',
        areaName: "Euro",
        server: "http://lucky-gou.com",
        currency: "eur"
    }
}

window.ADQ = function($, _, Backbone) {
    var notify = function() {
        var Stacks = {
            stack_top_right: {
                "dir1": "down",
                "dir2": "left",
                "push": "top",
                "spacing1": 10,
                "spacing2": 10
            },
            stack_top_left: {
                "dir1": "down",
                "dir2": "right",
                "push": "top",
                "spacing1": 10,
                "spacing2": 10
            },
            stack_bottom_left: {
                "dir1": "right",
                "dir2": "up",
                "push": "top",
                "spacing1": 10,
                "spacing2": 10
            },
            stack_bottom_right: {
                "dir1": "left",
                "dir2": "up",
                "push": "top",
                "spacing1": 10,
                "spacing2": 10
            },
            stack_bar_top: {
                "dir1": "down",
                "dir2": "right",
                "push": "top",
                "spacing1": 0,
                "spacing2": 0
            },
            stack_bar_bottom: {
                "dir1": "up",
                "dir2": "right",
                "spacing1": 0,
                "spacing2": 0
            },
            stack_context: {
                "dir1": "down",
                "dir2": "left",
                "context": $("#stack-context")
            }
        };

        function findWidth(noteStack) {
            if (noteStack == "stack_bar_top") {
                return "100%";
            }
            if (noteStack == "stack_bar_bottom") {
                return "70%";
            } else {
                return "290px";
            }
        }

        var createNotify = function(title, text, noteStyle, noteStack) {
            return new PNotify({
                title: title,
                text: text,
                addclass: noteStack,
                type: noteStyle,
                stack: Stacks[noteStack],
                width: findWidth(noteStack),
                delay: 1400
            });
        };

        var notifyResp = function(data) {
            var message = "服务器错误！";
            data = data.responseJSON;
            if (data != null) {
                message = data.msg || ERROR_CODE[data.status] || message;
            }
            return createNotify("警告", "操作失败！" + message, "warning", "stack_bottom_right");
        };

        return {
            success: function(title, text) {
                return createNotify(title || "提示", text || "操作成功！", 'success', 'stack_bottom_right');
            },
            warning: function(title, text) {
                return createNotify(title || "错误", text || "操作失败！", 'warning', 'stack_bottom_right');
            },
            error: function(title, text) {
                return createNotify(title || "警告", text || "出现错误", 'danger', 'stack_bottom_right');
            },
            notifyResp: notifyResp
        };
    }();

    var fullscreen = function() {
        // Fullscreen Functionality
        var screenCheck = $.fullscreen.isNativelySupported();

        // Attach handler to navbar fullscreen button
        $('.request-fullscreen').click(function() {
            // Check for fullscreen browser support
            if (screenCheck) {
                if ($.fullscreen.isFullScreen()) {
                    $.fullscreen.exit();
                } else {
                    $('html').fullscreen({
                        overflow: 'visible'
                    });
                }
            } else {
                alert('Your browser does not support fullscreen mode.')
            }
        });
    };

    var utils = {
        DATETIME_FORMAT: "YYYY/MM/DD HH:mm:ss",
        numberWithCommas: function(x) {
            var parts = x.toString().split(".");
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            return parts.join(".");
        },
        now: function(format) {
            if (format) {
                return moment().format(format);
            }
            return moment();
        },
        yesterday: function(format) {
            if (format) {
                return moment().add(-1, 'days').format(format);
            }
            return moment().add(-1, 'days');
        },
        toDate: function(unix_timestamp, format) {
            var unix_timestamp = parseInt(unix_timestamp, 10);
            format = format || this.DATETIME_FORMAT;
            return moment(unix_timestamp).format(format);
        },
        fromDate: function(dtstring, format) {
            format = format || this.DATETIME_FORMAT;
            return moment(dtstring, format);
        },
        nearest10N: function(num) {
            var n10N = 10,
                multi = 10;
            while (num - n10N > 0) {
                n10N = n10N + multi;
                if (n10N / multi == 10) {
                    multi = multi * 10;
                }
            }
            return n10N;
        },
        getDeviceTypeStr: function(num){
            num = parseInt(num);
            var dt = [];
            _.each(DEVICE_TYPE, function(value, key){
                if(num & parseInt(key)){
                    dt.push(value);
                }
            });
            return dt.join(',');
        },
        isIOS: function (t) {
            if (t & (2 | 16 | 32 | 64 | 128 | 256)) {
                return true;
            }
            return false;
        },
        calcDeviceType: function(deviceTypes){
            var deviceType = 0;
            if(deviceTypes){
                _.each(deviceTypes, function(t){
                    deviceType |= parseInt(t);
                });
            }
            return deviceType;
        },
        generateUUID: function() {
            var d = new Date().getTime();
            if(window.performance && typeof window.performance.now === "function"){
                d += performance.now(); //use high-precision timer if available
            }
            var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = (d + Math.random()*16)%16 | 0;
                d = Math.floor(d/16);
                return (c=='x' ? r : (r&0x3|0x8)).toString(16);
            });
            return uuid;
        },
        getFileExtension: function(filename) {
                var tempArr = filename.split(".");
                var ext;
                if (tempArr.length === 1 || (tempArr[0] === "" && tempArr.length === 2)) {
                    ext = "";
                } else {
                    ext = tempArr.pop().toLowerCase(); //get the extension and make it lower-case
                }
                return ext;
        },
        _getUploaderParams: function (btnId, forAvatar) {
            var uptoken_url = '/admin/uptoken/',
                domain = window.QINIU_DOMAIN || 'http://7xod1l.com1.z0.glb.clouddn.com/';
            if (forAvatar) {
                uptoken_url = window.UPTOKEN_URL || uptoken_url;
                domain = window.AVATAR_DOMAIN || domain;
            }
            var params = {
                runtimes: 'html5,flash,html4',
                browse_button: btnId,
                container: 'container',
                drop_element: 'container',
                max_file_size: '10mb',
                flash_swf_url: 'vendor/plugins/plupload/js/Moxie.swf', //引入flash,相对路径
                max_retries: 3, //上传失败最大重试次数
                dragdrop: true,
                chunk_size: '4mb',
                domain: domain,
                get_new_uptoken: false,
                uptoken_url: uptoken_url,
                filters: {
                    mime_types: [ //只允许上传图片文件
                        {
                            title: "图片文件",
                            extensions: "jpg,gif,png,bmp,jpeg"
                        },
                    ],
                    prevent_duplicates: true //不允许队列中存在重复文件
                },
                auto_start: true,
                headers: {
                    'X-AUTH-USER': ADQ.utils.getCookie('lucky_user_id'),
                    'X-AUTH-TOKEN': ADQ.utils.getCookie('lucky_user_token')
                },
            };
            if (!forAvatar) {
                params.unique_names = true;
            } else {
                params.unique_names = false;
                params.save_key = false;
                params.init = {};
                params.init.Key = function (up, file) {
                    var key = "avatars/",
                        ext = ADQ.utils.getFileExtension(file.name),
                        name = ext ? file.id + '.' + ext : file.id;
                    // do something with key here
                    return key + name;
                };
            }
            return params;
        },
        getUploader: function (btnId, uiId, uploadedCallback, forAvatar) {
            var params = ADQ.utils._getUploaderParams(btnId, forAvatar);
            $.extend(true, params, {
                init: {
                    'FilesAdded': function (up, files) {
                        $('#processTable').show();
                        $('#success').hide();
                        plupload.each(files, function (file) {
                            var progress = new FileProgress(file, uiId);
                            progress.setStatus("等待...");
                            progress.bindUploadCancel(up);
                        });
                    },
                    'BeforeUpload': function (up, file) {
                        var progress = new FileProgress(file, uiId);
                        var chunk_size = plupload.parseSize(this.getOption('chunk_size'));
                        if (up.runtime === 'html5' && chunk_size) {
                            progress.setChunkProgess(chunk_size);
                        }
                    },
                    'UploadProgress': function (up, file) {
                        var progress = new FileProgress(file, uiId);
                        var chunk_size = plupload.parseSize(this.getOption('chunk_size'));
                        progress.setProgress(file.percent + "%", file.speed, chunk_size);
                    },
                    'UploadComplete': function () {
                        $('#success').show();
                    },
                    'FileUploaded': function (up, file, info) {
                        var progress = new FileProgress(file, uiId);
                        progress.setComplete(up, info);
                        var res = $.parseJSON(info);
                        var url;
                        if (res.url) {
                            url = res.url;
                        } else {
                            var domain = up.getOption('domain');
                            url = domain + encodeURI(res.key);
                        }
                        uploadedCallback(url);
                    },
                    'Error': function (up, err, errTip) {
                        $('#processTable').show();
                        var progress = new FileProgress(err.file, uiId);
                        progress.setError();
                        progress.setStatus(errTip);
                    }
                }
            });
            var uploader = Qiniu.uploader(params);
            return uploader;
        },
        setProcess: function (values, barId) {
            if (values.max != null) $('#' + barId).attr('aria-valuemax', values.max);
            if (values.now != null) $('#' + barId).css('width', values.now + '%').attr('aria-valuenow', values.now);
        },
        getProcess: function (barId) {
            return { max: $('#' + barId).attr('aria-valuenow'), now: $('#' + barId).attr('aria-valuemax') };
        },
        getSimplerUploader: function (btnId, uploadedCallback, forAvatar) {
            var params = ADQ.utils._getUploaderParams(btnId, forAvatar);
            $.extend(true, params, {
                init: {
                    'FilesAdded': function (up, files) {
                        ADQ.utils.setProcess({ max: files.length, now: 0 }, 'uploadprocess');
                        $('#uploadprocess').html('processing...');
                    },
                    'UploadComplete': function () {
                        ADQ.utils.setProcess({ max: 100, now: 100 }, 'uploadprocess');
                        $('#uploadprocess').html('上传完毕');
                    },
                    'FileUploaded': function (up, file, info) {
                        var c = $('#uploadprocess').attr('aria-valuenow');
                        ADQ.utils.setProcess({ now: c + 1 });
                        var res = $.parseJSON(info);
                        var url;
                        if (res.url) {
                            url = res.url;
                        } else {
                            var domain = up.getOption('domain');
                            url = domain + encodeURI(res.key);
                        }
                        uploadedCallback(url);
                    },
                    'Error': function (up, err, errTip) {
                        $('#processTable').show();
                        var progress = new FileProgress(err.file, uiId);
                        progress.setError();
                        progress.setStatus(errTip);
                    }
                }
            });
            var uploader = Qiniu.uploader(params);
            return uploader;
        },
        getSingleUploader: function (btnId, uploadedCallback, silent, forAvatar) {
            var params = ADQ.utils._getUploaderParams(btnId, forAvatar),
                originImg = null;
            $.extend(true, params, {
                init: {
                    'FilesAdded': function (up, files) {
                        if (!silent) {
                            var img = $('#' + btnId).data('img');
                            originImg = $('#' + img).attr('src');
                            $('#' + img).attr("src", "vendor/plugins/qiniu/loading.gif");
                        }
                    },
                    'FileUploaded': function (up, file, info) {
                        var res = $.parseJSON(info),
                            img = $('#' + btnId).data('img'),
                            url = '';
                        if (res.url) {
                            url = res.url;
                        } else {
                            var domain = up.getOption('domain');
                            url = domain + encodeURI(res.key);
                            $('#' + img).attr("src", url);
                            $('#' + img).parent('a.image-popup').attr('href', url);
                        }
                        if (uploadedCallback) uploadedCallback(url);
                    },
                    'Error': function (up, err, errTip) {
                        if (!silent) {
                            var img = $('#' + btnId).data('img');
                            $('#' + img).attr("src", originImg);
                        }
                        notify.error("上传错误", errTip);
                    }
                }
            });
            var uploader = Qiniu.uploader(params);
            return uploader;
        },
        getValidator: function(selector) {
            var v = $(selector).validate({
                errorClass: "state-error",
                validClass: "state-success",
                errorElement: "em",
                highlight: function(element, errorClass, validClass) {
                    $(element).addClass(errorClass).removeClass(validClass);
                },
                unhighlight: function(element, errorClass, validClass) {
                    $(element).addClass(validClass).removeClass(errorClass);
                },
                errorPlacement: function(error, element) {
                    if (element.is(":radio") || element.is(":checkbox")) {
                        element.closest('.option-group').after(error);
                    } else if (element.is("select")) {
                        error.insertAfter(element.parent('div'));
                        return;
                    } else {
                        error.insertAfter(element.parent());
                    }
                }
            });
            return v;
        },
        validElement: function (elem) {
            var $this = $(elem),
                val = ADQ.utils.getInput(elem),
                isRight = true;
            if ($this.is('[required]') && (val === '' || val == undefined)) {
                isRight = false;
            } else if ($this.data("field") == "command" || $this.data("field") == "cmd" ||
                $(this).data('type') === 'command') {
                if (!val.match(/\d+#.*/)) {
                    isRight = false;
                }
            } else if ($this.attr("min") || $this.attr("max")) {
                val = parseInt(val);
                var min = parseInt($this.attr("min")),
                    max = parseInt($this.attr("max"));
                if (min && val < min) isRight = false;
                if (max && val > max) isRight = false;
            } else if ($this.attr("maxlength") || $this.attr("minlength")) {
                var maxlength = $this.attr('maxlength'),
                    minlength = $this.attr('minlength');
                if (maxlength && val.length > maxlength) isRight = false;
                if (minlength && val.length < minlength) isRight = false;
            }
            return isRight;
        },
        simpleCheck: function(selector) {
            var inputAllRight = true;
            if (!selector) selector = 'body';
            $(selector).find('[required]').not('.placeholder').each(function() {
                if (!ADQ.utils.validElement(this)) {
                    inputAllRight = false;
                    $(this).removeClass("state-success").addClass("state-error");
                }
            });
            return inputAllRight;
        },
        renderTable: function(tableId, options) {
            var orderby = options.$orderby,
                desc = false;
            if (orderby && orderby[0] == '-') {
                desc = true;
                orderby = orderby.substr(1);
            }
            var selectorPrefix = '#' + tableId + ' ';
            $(selectorPrefix + 'span.fa').remove();
            $(selectorPrefix + 'th.sortable').append(' <span class="fa fa-sort deactive"></span>');
            var iconClass = desc ? "fa-sort-desc" : "fa-sort-asc";
            $(selectorPrefix + 'th[data-field=' + orderby + '] span').removeClass('fa-sort deactive').addClass(iconClass);
            $(selectorPrefix + 'th.sortable').click(function() {
                var field = $(this).data('field');
                var desc = $(this).children('span').hasClass('fa-sort-asc');
                if (desc) field = '-' + field;
                if (options.sortCallback) {
                    options.sortCallback(field);
                }
            });
        },
        getPaginator: function(options, total, url_prefix) {
            var pageSize = options.$size || PAGE_SIZE,
                currentPage = options.$page || 1,
                start = (currentPage - 1) * pageSize + 1,
                end = start + pageSize - 1,
                totalPages = Math.ceil(total / pageSize) || 1;
            if(end > total) end = total;
            $('#page-tips').text("第" + start + "到第" + end + "项, 共" + total + "项");
            $('#paginator').bootstrapPaginator({
                currentPage: currentPage,
                totalPages: totalPages,
                numberOfPages: 10,
                alignment: 'center',
                itemTexts: function(type, page, current) {
                    switch (type) {
                        case "first":
                            return "首页";
                        case "prev":
                            return "前一页";
                        case "next":
                            return "后一页";
                        case "last":
                            return "尾页";
                        case "page":
                            return page;
                    }
                },
                onPageClicked: function(e,originalEvent,type,page){
                    options.$page = page;
                    location.href = ADQ.utils.composeQueryString(url_prefix, options);
                },
            });
            $('#paginator').append('<input id="pageNumber" type="text" class="pull-right" size="2">');
            $('#pageNumber').val(currentPage);
            $('#pageNumber').off().on('keypress', function (e) {
                if (e.which == 13) {
                    e.stopImmediatePropagation();
                    var page = parseInt($('#pageNumber').val());
                    if (!isNaN(page) && page <= totalPages) {
                        options.$page = page;
                        location.href = ADQ.utils.composeQueryString(url_prefix, options);
                    }
                }
            })
        },
        loadTemplate: function(clses, callback) {
            var deferreds = [];
            _.each(clses, function(cls, index) {
                _.each(cls, function(view) {
                    if (view.prototype.template) {
                        deferreds.push($.get('templates/' + view.prototype.template, function(data) {
                            view.prototype.template = _.template(data);
                        }));
                    }
                });
            });
            $.when.apply(null, deferreds).done(callback);
        },
        parseQueryString: function(queryString) {
            var params = {};
            if (queryString) {
                _.each(
                    _.map(decodeURI(queryString).split(/&/g), function(el, i) {
                        var aux = el.split('='),
                            o = {};
                        if (aux.length >= 1) {
                            var val = null;
                            if (aux.length == 2)
                                val = aux[1];
                            o[aux[0]] = val;
                        }
                        return o;
                    }),
                    function(o) {
                        _.extend(params, o);
                    }
                );
            }
            return params;
        },
        composeQueryString: function(base, queryDict) {
            if ($.isEmptyObject(queryDict)) return base;
            base += '?';
            _.each(queryDict, function(value, key) {
                if (value === true) {
                    value = 1;
                } else if (value === false) {
                    value = 0;
                }
                if (value != undefined) {
                    if (typeof(value) == 'object') {
                        base += key + '=' + JSON.stringify(value) + '&';
                    } else {
                        base += key + '=' + value + '&';
                    }
                } else {
                    base += key + '&';
                }
            });
            base = base.slice(0, -1);
            return base;
        },
        saveSearched: function (key, searched) {
            var k = key + '_' + 'searched';
            localStorage[k] = JSON.stringify(searched);
        },
        clearSearched: function(key) {
            if (key) {
                delete localStorage[key + '_' + 'searched'];
            } else {
                // NOTE: TAKE CARE
                localStorage.clear();
            }
        },
        snapPage: function(key) {
            var k = key + '_' + 'style',
                style = {};
            if ($('body').hasClass('sb-r-o')) {
                style.sbr = 'sb-r-o';
            } else {
                style.sbr = 'sb-r-c';
            }
            localStorage[k] = JSON.stringify(style);
        },
        setls: function(status) {
            return $('body').removeClass('sb-l-c sb-l-o sb-l-m').addClass('sb-l-' + status);
        },
        setrs: function(status) {
            return $('body').removeClass('sb-r-o sb-r-c').addClass('sb-r-' + status);
        },
        addCookie: function(name, value, expires) {
            var d = new Date();
            d.setTime(d.getTime() + (expires * 24 * 60 * 60 * 1000));
            var expiresStr = d.toGMTString();
            document.cookie = name + "=" + value + ";expires=" + expiresStr;
        },
        getCookie: function(name) {
            var cookieName = name + "=";
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var c = cookies[i];
                while (c.charAt(0) == ' ') c = c.substring(1);
                if (c.indexOf(cookieName) != -1) return c.substring(cookieName.length, c.length);
            }
            return "";
        },
        deleteCookie: function(name) {
            // 默认为当前的host
            var domain = arguments[1] ? arguments[1] : window.location.host;
            // 默认为当前的URL
            var path = arguments[2] ? arguments[2] : "/";
            //document.cookie = name + "=;domain=" + domain + ";path=" + path + ";expires=Thu, 01 Jan 1970 00:00:00 GMT";
            document.cookie = name + "=;path=" + path + ";expires=Thu, 01 Jan 1970 00:00:00 GMT";
        },
        checkUserToken: function(callback) {
            $.get('/admin/user/' + ADQ.utils.getCookie('lucky_user_id') + '/').done(function(resp) {
                $('#user-full-name').text(resp.data.nickname);
                var role = resp.data.role;
                USER_INFO.info = resp.data;
                if(role <= 2){
                    $('#statsMenu').hide();
                }
                if(role <= 1){
                    $('#consoleMenu').hide();
                }
                // $.get('/admin/permission/?min_role:{"$lte":' + role + '}').done(function(r){
                //     _.each(r.data.list, function(v){
                //         if ((v.url in PERM_DICT && v.permission > PERM_DICT[v.url]) || !(v.url in PERM_DICT)){
                //             PERM_DICT[v.url] = v.permission;
                //         }
                //     });
                    callback();
                // }).fail(function(r){
                //     notify.notifyResp(r);
                // });
            }).fail(function(data) {
                notify.notifyResp(data);
                window.location.href = '/user.html';
            });
        },
        getHighChartPieOptions: function(){
            return {
                chart: {
                    plotBackgroundColor: null,
                    plotBorderWidth: null,
                    plotShadow: false,
                    type: 'pie'
                },
                tooltip: {
                    pointFormat: '{point.name}: <b>{point.percentage: .2f}%</b>'
                },
                title: {
                    text: null,
                },
                plotOptions: {
                    pie: {
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: true,
                            format: '<b>{point.name}</b>: {point.y}',
                        }
                    }
                },
                series: [{
                    name: '占比',
                    colorByPoint: true,
                    data: []
                }]
            };
        },
        getHighChartColumnOptions: function(stack){
            var option = {
                chart: {
                    type: 'column'
                },
                xAxis: {
                    categories: [],
                    crosshair: true,
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: '数值'
                    }
                },
                title: {
                    text: null,
                },
                tooltip:{
                    pointFormat: '{point.name}: <b>{point.y}</b>'
                },
                series: []
            };
            if(stack){
                option.plotOptions = {
                column: {
                    stacking: 'normal',
                    dataLabels: {
                        enabled: true,
                        color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                        }
                    }
                };
            }
            return option;
        },
        getHighChartLineOptions: function(){
            return {
                chart: {
                    type: 'line'
                },
                xAxis: {
                    categories: []
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: '值'
                    }
                },
                title: {
                    text: null,
                },
                tooltip:{
                    pointFormat: '{point.name}: <b>{point.y}</b>'
                },
                series: []
            };
        },
        getCurrentKey: function () {
            var hash = location.hash.split('/');
            if (hash[hash.length -1] == '' || hash[hash.length - 1][0] == "?") {
                hash = hash.slice(0, hash.length - 1);
            }
            return hash.join('/');
        },
        getFileUploader: function (url, btn) {
            var uploader = new plupload.Uploader({
                runtimes : 'html5,flash,silverlight,html4',
                browse_button: btn || 'importExcel',
                container: document.getElementById('container'),
                url: url,
                dragdrop: false,
                // chunk_size: "1mb",
                filters: {
                    mime_types: [
                        {
                            title: "Excel Files",
                            extensions: "xls,xlsx"
                        },
                    ],
                    max_file_size: "4mb",
                    prevent_duplicates: false //不允许队列中存在重复文件
                },
                file_data_name: "excel_data",
                flash_swf_url : '/plupload/js/Moxie.swf',
                multi_selection: false,
                headers:{
                    'X-AUTH-USER': ADQ.utils.getCookie('lucky_user_id'),
                    'X-AUTH-TOKEN': ADQ.utils.getCookie('lucky_user_token')
                },
                init: {
                    FilesAdded: function(up, files) {
                        up.start();
                    },
                    UploadProgress: function(up, file) {
                        ADQ.notify.warning("警告", "上传中，请耐心等待...");
                    },
                    'FileUploaded': function() {
                        ADQ.notify.success("通知", "上传成功！");
                        setTimeout(function() {
                            location.reload();
                        }, 500);
                    },
                    'Error': function(up, err, errTip) {
                        ADQ.notify.error("上传失败", errTip);
                        console.log(err);
                    }
                    }
            });
            uploader.init();
        },
        getInput: function (elem) {
            var $this = $(elem),
                value = null;
            if ($this.data('value')) {
                value = $this.data('value')
            }else if ($this.is('img')) {
                value = $this.attr('src')
            } else if ($this.is(':checkbox')) {
                value = $this.is(':checked');
            } else {
                var val = $this.val(),
                    type = $this.data('type');
                if (type == 'int') {
                    value = parseInt(val);
                    if (isNaN(value)) value = '';
                } else if (type == 'float') {
                    value = parseFloat(val);
                    if (isNaN(value)) value = '';
                } else {
                    value = val;
                }
            }
            return value;
        },
        getAllInput: function (selector) {
            var inputs = {};
            if (selector == undefined) selector = "body";
            $(selector).find('[data-field]').each(function () {
                var $this = $(this),
                    key = $this.data('field'),
                    value = ADQ.utils.getInput(this),
                    keyArray = key.split('.'),
                    useless = $this.data('useless'),
                    t = inputs;
                if (useless != undefined && value == useless) return;
                if ($this.hasClass('placeholder')) return;
                var parent = inputs;
                for (var i = 0; i < keyArray.length - 1; ++i){
                    var key = keyArray[i];
                    if (parent[key] == undefined) {
                        parent[key] = {};
                    }
                    parent = parent[key];
                }
                parent[keyArray[keyArray.length - 1]] = value;
            });
            return inputs;
        },
        humanizeContent: function (resource, content) {
            content = JSON.parse(content || '{}');
            var result = '';
            if (content && content.extend) {
                $.extend(content, content.extend);
            }
            _.each(content, function (v, k) {
                if (v == null || v == '') return;
                if (k == 'id' || k == 'created_at' || k == 'updated_at' || k == 'extend') return;
                if (k == 'status') {
                    if (resource == 'awarded_order') result += ('订单状态 -> ' + ORDER_STATUS[v] + ', ');
                    else if (resource == 'template') result += ('状态 -> ' + TEMPLATE_STATUS[v] + ', ');
                } else if (k == 'ship_status') {
                    result += ('发货状态 -> ' + SHIP_STATUS[v] + ', ');
                } else {
                    result += (k + ' -> ' + v + ', ');
                }
            })
            result = result.slice(0, -2);
            return result;
        }

    };

    var exportData = function(base, options){
        options.$size = -1;
        delete options.$page;
        delete options.$orderby;
        options.$export = true;
        $.get(utils.composeQueryString(base, options)).done(function(resp){
            window.location=resp.data.url;
        }).fail(function(resp){
            notify.error();
        });
    };
    Backbone.emulateHTTP = true;

    _.template.utils = utils;

    return {
        notify: notify,
        fullscreen: fullscreen,
        utils: utils,
        exportData: exportData,
    };

}(jQuery, _, Backbone);
