CREATE DATABASE IF NOT EXISTS `admin`;

USE admin;

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nickname` VARCHAR(64) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `role` SMALLINT NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00',
    PRIMARY KEY (`id`),
    UNIQUE KEY `index_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `permission` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `url` VARCHAR(255) NOT NULL,
    `permission` SMALLINT DEFAULT 0,
    `min_role`   SMALLINT DEFAULT 1,
    `desc`       VARCHAR(64) DEFAULT '',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00',
    PRIMARY KEY (`id`),
    UNIQUE KEY `index_url_permission` (`url`, `permission`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `permission` values (
    null, '/admin/user/login/', 2, 1, '用户登录', now(), now()),(
    null, '/admin/user/logout/', 2, 1, '用户注销', now(), now()),(
    null, '/admin/user/', 1, 1, '用户管理', now(), now()),(
    null, '/admin/user/', 2, 2, '用户管理', now(), now()),(
    null, '/admin/record/',1, 2, '操作记录', now(), now()),(
    null, '/admin/permission/', 1, 1, '权限管理', now(), now()),(
    null, '/admin/permission/', 2, 4, '权限管理', now(), now()),(
    null, '/admin/activity/template/', 1, 1, '活动模板管理', now(), now()),(
    null, '/admin/activity/template/', 2, 2, '活动模板管理', now(), now()),(
    null, '/admin/order/', 1, 1, '订单管理', now(), now()),(
    null, '/admin/order/', 2, 2, '订单管理', now(), now()),(
    null, '/admin/goods/', 1, 1, '商品管理', now(), now()),(
    null, '/admin/goods/', 2, 2, '商品管理', now(), now()),(
    null, '/admin/uptoken/', 1, 2, "上传七牛图片", now(), now()),(
    null, '/admin/image/delete/', 2, 2, '删除七牛图片', now(), now()),(
    null, '/admin/preset/', 1, 1, '预置数据管理', now(), now()),(
    null, '/admin/preset/', 2, 2, '预置数据管理', now(), now()),(
    null, '/admin/show/', 1, 1, '晒单管理', now(), now()),(
    null, '/admin/show/', 2, 2, '晒单管理', now(), now()),(
    null, '/admin/category/', 1, 1, '分类管理', now(), now()),(
    null, '/admin/category/', 2, 2, '分类管理', now(), now()),(
    null, '/admin/virtual/', 1, 1, '虚拟账户管理', now(), now()),(
    null, '/admin/virtual/', 2, 2, '虚拟账户管理', now(), now()),(
    null, '/admin/notification/', 1, 1, '系统通知管理', now(), now()),(
    null, '/admin/notification/', 2, 2, '系统通知管理', now(), now()),(
    null, '/admin/coupon/template/', 1, 1, '红包模板管理', now(), now()),(
    null, '/admin/coupon/', 2, 2, '红包管理', now(), now()),(
    null, '/admin/abtest/', 1, 2, '灰度策略管理', now(), now()),(
    null, '/admin/abtest/', 2, 2, '灰度策略管理', now(), now()),(
    null, '/admin/feedback/', 1, 2, '用户反馈管理', now(), now()),(
    null, '/admin/stats/', 1, 3, '统计信息', now(), now()),(
    null, '/admin/stats/limit/', 2, 4, '限额管理', now(), now()),(
    null, '/admin/vips/', 2, 3, 'vip用户管理', now(), now()), (
    null, '/admin/account/',1, 3, '用户账户信息', now(), now()),(
    null, '/admin/activity/', 1, 3, '活动信息', now(), now()),(
    null, '/admin/coupon/', 1, 3, '红包信息', now(), now()),(
    null, '/admin/report/', 1, 3, '报表信息', now(), now());


CREATE TABLE IF NOT EXISTS `user_token` (
    `user_id` BIGINT(20) UNSIGNED NOT NULL,
    `token` VARCHAR(64) NOT NULL,
    `deleted` SMALLINT(2) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00',
     PRIMARY KEY (`user_id`,`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `record` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `resource` varchar(64) NOT NULL,
  `resource_id` bigint(20) unsigned DEFAULT NULL,
  `action` tinyint(4) NOT NULL,
  `content` text,
  `operator` bigint(20) unsigned NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `index_res` (`resource`,`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;