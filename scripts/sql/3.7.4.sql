-- 新建homepage_lib表
CREATE TABLE `homepage_lib` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cmd` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `remark` text COLLATE utf8mb4_unicode_ci,
  `abtest` int(10) unsigned DEFAULT NULL,
  `type` tinyint(2) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `dot` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- 新建theme_lib表 
CREATE TABLE `theme_lib` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `title` text COLLATE utf8mb4_unicode_ci,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `abtest` int(10) unsigned DEFAULT NULL,
  `start_ts` bigint(20) unsigned DEFAULT NULL,
  `end_ts` bigint(20) unsigned DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `remark` text COLLATE utf8mb4_unicode_ci,
  `active` tinyint(2) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- coupon_tempalte增加字段
alter table coupon_template add column activity_tids text default null;
alter table coupon_template add column activity_categories text default null;
ALTER TABLE coupon_template add COLUMN scope_all tinyint(2) DEFAULT 0;
alter table coupon_template add column cmd TEXT default null;
alter table coupon_template add column remark TEXT default null;

-- 更新remark和cmd
update coupon_template set scope_all=1 where 
    id in (104, 193, 194, 222, 223, 224, 254, 259, 260)
    or id between 228 and  245
    or id between 62  and 86
    or id between 144 and  149
    or id between 246 and  252
    or id between 261 and  287; 

update coupon_template set remark="全场商品可使用", cmd="0#" where scope_all=1;

update coupon_template set remark="仅限实物类商品使用", cmd="0#" where scope_all=0;