-- MySQL dump 10.13  Distrib 5.5.47, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: admin
-- ------------------------------------------------------
-- Server version	5.5.47-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `permission`
--

DROP TABLE IF EXISTS `permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `permission` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `url` varchar(255) NOT NULL,
  `permission` smallint(6) DEFAULT '0',
  `min_role` smallint(6) DEFAULT '1',
  `desc` varchar(64) DEFAULT '',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `index_url_permission` (`url`,`permission`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `record`
--

DROP TABLE IF EXISTS `record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `nickname` varchar(64) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` smallint(6) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `index_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_token`
--

DROP TABLE IF EXISTS `user_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_token` (
  `user_id` bigint(20) unsigned NOT NULL,
  `token` varchar(64) NOT NULL,
  `deleted` smallint(2) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`user_id`,`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-09-22  6:51:26

INSERT INTO `permission` values (
    null, '/admin/user/login/', 2, 1, '用户登录', now(), now()),(
    null, '/admin/user/logout/', 2, 1, '用户注销', now(), now()),(
    null, '/admin/user/', 1, 1, '用户管理', now(), now()),(
    null, '/admin/user/', 2, 2, '用户管理', now(), now()),(
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
    null, '/admin/stats/missed_vips/', 2, 3, '流失用户状态管理', now(), now()), (
    null, '/admin/account/',1, 3, '用户账户信息', now(), now()),(
    null, '/admin/activity/', 1, 3, '活动信息', now(), now()),(
    null, '/admin/coupon/', 1, 3, '红包信息', now(), now()),(
    null, '/admin/report/', 1, 3, '报表信息', now(), now());
