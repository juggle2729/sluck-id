'use strict';

var UserConsole = function($) {
    var app = null;

    var viewCls = function(){
        var UserSignInPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "user/SignIn.html",
            events: {
                'submit #form-signin': "signin"
            },

            signin: function(e) {
                e.preventDefault();
                var formObj = $('#form-signin'),
                    submitBtn = $('button.btn-primary');
                submitBtn.attr('disabled', 'disabled');
                $.ajax({
                    url: formObj.attr("action"),
                    type: 'POST',
                    headers: {'Access-Control-Allow-Origin': '*'},
                    data: JSON.stringify({
                        'email': formObj.find("#email").val(),
                        'password': formObj.find("#password").val()
                    }),
                }).done(function(data){
                    ADQ.utils.addCookie('lucky_user_id', data.data.id, 7);
                    ADQ.utils.addCookie('lucky_user_token', data.data.token, 7);
                    if(window.location.href != document.referrer && document.referrer) {
                        window.location.href = document.referrer;
                    } else {
                        window.location.href = '/';
                    }
                }).fail(function(data){
                    ADQ.notify.notifyResp(data);
                    submitBtn.removeAttr('disabled');
                });
            },
            render: function() {
                this.$el.html(this.template());
                return this;
            }
        });

        var UserSignUpPage = Backbone.View.extend({
            el: "#content_wrapper",
            template: "user/SignUp.html",
            events: {
                'submit #form-signup': "signup"
            },

            signup: function(e) {
                e.preventDefault();
                var formObj = $('#form-signup'),
                    submitBtn = $('button.btn-primary');
                submitBtn.attr('disabled', 'disabled');
                $.ajax({
                    url: formObj.attr("action"),
                    type: 'POST',
                    data: JSON.stringify({
                        nickname: formObj.find("#nickname").val(),
                        email: formObj.find("#email").val(),
                        password: formObj.find("#password").val()
                    }),
                }).done(function(data){
                    alert('注册成功，请联系管理人员激活账号！');
                    window.location.href = 'user.html#signin/';
                }).fail(function(data){
                    ADQ.notify.error('注册', '注册失败: ' + ERROR_CODE[data.responseJSON.status] || '服务器错误');
                    submitBtn.removeAttr('disabled');
                });
            },
            render: function() {
                this.$el.html(this.template());
                return this;
            }
        });

        return {
            UserSignInPage: UserSignInPage,
            UserSignUpPage: UserSignUpPage
        };
    }();

    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "userSignIn",
            "signin/": "userSignIn",
            "signup/": "userSignUp"
        },

        userSignIn: function() {
            var userSignInPage = new viewCls.UserSignInPage();
            userSignInPage.render();
        },
        userSignUp: function() {
            var userSignUpPage = new viewCls.UserSignUpPage();
            userSignUpPage.render();
        }
    });

    return {
        init: function() {
            ADQ.fullscreen();
            ADQ.utils.loadTemplate([viewCls], function() {
                app = new AppRouter();
                Backbone.history.start();
            });
        }
    };

}(jQuery);
