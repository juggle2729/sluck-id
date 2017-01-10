# -*- coding:utf-8 -*-
import json
import logging
import importlib

from luckycommon.level.handler import has_level_coupon
from luckycommon.preset.handler import view_discovery

from luckycommon.credit.model.check import CHECK_TYPE
from luckycommon.credit.db import credit as credit_db

from luckycommon.model.show import SHOW_STATUS, AnnounceShow

from luckycommon.cache import redis_cache
from luckycommon.utils.limit import check_abtest 
from luckycommon.utils.types import Enum
from luckycommon.utils.tz import now_ts

from django.conf import settings


_LOGGER = logging.getLogger('lucky')


class BaseTips(object):
    """
    小红点抽象类
    """
    def query(self, user_id):
        raise NotImplementedError('BaseTips is an Abstract Class')

    def update(self, user_id): 
        raise NotImplementedError('BaseTips is an Abstract Class')

    def add(self, user_id):
        """
        增加一个tip
        """
        raise NotImplementedError('BaseTips is an Abstract Class')

    def remove(self, user_id):
        """
        移除一个tip
        """
        raise NotImplementedError('BaseTips is an Abstract Class')

    def set(self, user_id, count):
        """
        设置tips个数
        """
        raise NotImplementedError('BaseTips is an Abstract Class')

    def clear(self, user_id):
        """
        清空tips 
        """
        raise NotImplementedError('BaseTips is an Abstract Class')


class AwardTips(BaseTips): 
    """
    中奖提醒小红点
    """
    def query(self, user_id):
        count = redis_cache.get_user_pending(user_id, 'award') or 0
        return {'award': int(count)}

    def add(self, user_id):
        redis_cache.add_user_pending(user_id, 'award')

    def remove(self, user_id):
        redis_cache.remove_user_pending(user_id, 'award')


class ShowTips(BaseTips): 
    """
    晒单提醒小红点
    """
    def query(self, user_id):
        fail_shows = AnnounceShow.query.filter(AnnounceShow.user_id == user_id)\
                                 .filter(AnnounceShow.status == SHOW_STATUS.VERIFY_FAIL)\
                                 .all()
        available_shows = AnnounceShow.query.filter(AnnounceShow.user_id == user_id)\
                                      .filter(AnnounceShow.status == SHOW_STATUS.WAIT_SHOW)\
                                      .all()
        return {
            'available_show': len(available_shows),
            'verify_fail': len(fail_shows)
        }


class PartnerRewardTips(BaseTips): 
    """
    好友返利提醒小红点
    """
    def query(self, user_id):
        count = redis_cache.get_user_pending(user_id, 'partner_reward') or 0
        return {'partner_reward': int(count)}

    def set(self, user_id, count):
        redis_cache.set_user_pending(user_id, 'partner_reward', 1)

    def clear(self, user_id):
        redis_cache.clear_user_pending(user_id, 'partner_reward')


class DailySignTips(BaseTips):
    """
    每日签到提醒小红点
    """
    def query(self, user_id):
        today_checks = credit_db.get_today_checks(user_id)
        for check_item in today_checks:
            if check_item.check_type == CHECK_TYPE.DAILY_SIGN:
                return {'daily_sign': 0}
        return {'daily_sign': 1}


class LevelUpCouponTips(BaseTips):
    def query(self, user_id):
        result = has_level_coupon(user_id)
        if result:
            return {'level_up_coupon': 1}
        else:
            return {'level_up_coupon': 0}


# 用于映射快捷方式的小红点key
CMD_TIPS_MAP = {
    '11#%s/user/my_daily_attendance': 'daily_sign',
    '11#%s/user/my_rebate#%s/rebate_qa?show=1' % (settings.WEB_APP_ROOT_URL, settings.WEB_APP_ROOT_URL): 'partner_reward',
    '11#%s/discovery/new_year_coupon' % settings.WEB_APP_ROOT_URL: 'recharge_campaign',
    '11#%s/discovery/new_year_coupon2' % settings.WEB_APP_ROOT_URL: 'recharge_campaign',
    '11#%s/discovery/recharge' % settings.WEB_APP_ROOT_URL: 'new_recharge_campaign',
    '11#%s/discovery/new_year_share_coupon' % settings.WEB_APP_ROOT_URL: 'daily_buy_campaign',
    '11#%s/discovery/wealthy_god' % settings.WEB_APP_ROOT_URL: 'god_campaign',
    '11#%s/user/newbie_task' % settings.WEB_APP_ROOT_URL: 'fresh_mission',
}


# 所有存在待完成事项提醒的并会存在于发现中的活动，都需要在下面配置, 对应的模块需要实现query_tips方法
CMD_MODULES = {
    '11#%s/discovery/new_year_coupon' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.recharge_campaign'),
    '11#%s/discovery/new_year_coupon2' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.recharge_campaign'),
    '11#%s/discovery/recharge' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.new_recharge_campaign'),
    '11#%s/discovery/new_year_share_coupon' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.daily_buy_campaign'),
    '11#%s/discovery/wealthy_god' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.campaign.god_campaign'),
    '11#%s/user/newbie_task' % settings.WEB_APP_ROOT_URL:
        importlib.import_module('luckycommon.mission.fresh_mission'),
}


# 所有可能出现在快捷入口的功能，都要在下面配置
CAMPAIGN_CONF = [
    #('recharge_campaign', '11#%s/discovery/new_year_coupon' % settings.WEB_APP_ROOT_URL,
    #    importlib.import_module('luckycommon.campaign.recharge_campaign')),
    #('recharge_campaign', '11#%s/discovery/new_year_coupon2' % settings.WEB_APP_ROOT_URL,
    #    importlib.import_module('luckycommon.campaign.recharge_campaign')),
    #('new_recharge_campaign', '11#%s/discovery/recharge' % settings.WEB_APP_ROOT_URL,
    #    importlib.import_module('luckycommon.campaign.new_recharge_campaign')),
    #('daily_buy_campaign', '11#%s/discovery/new_year_share_coupon' % settings.WEB_APP_ROOT_URL,
    #    importlib.import_module('luckycommon.campaign.daily_buy_campaign')),
    #('god_campaign', '11#%s/discovery/wealthy_god' % settings.WEB_APP_ROOT_URL,
    #    importlib.import_module('luckycommon.campaign.god_campaign')),
    ('fresh_mission', '11#%s/user/newbie_task' % settings.WEB_APP_ROOT_URL,
        importlib.import_module('luckycommon.mission.fresh_mission')),
]


class CommandTips(BaseTips):
    """
    命令小红点，对应待完成事项
    """

    def query(self, user_id):
        command_dict = {}
        for item in CAMPAIGN_CONF:
            # check new tips
            tip_name, cmd, relation_module = item
            add_count = self.query_by_cmd(user_id, cmd)
            if add_count > 0:
                command_dict.update({tip_name: add_count})
        return command_dict

    def query_by_cmd(self, user_id, cmd, auto_ack=False):
        count = 0
        relation_module = CMD_MODULES.get(cmd)
        if relation_module:
            query_tips = getattr(relation_module, 'query_tips')
            if query_tips:
                count = query_tips(user_id)
        if not redis_cache.check_discovery_item_notified(user_id, cmd):
            count += 1
            if auto_ack:
                redis_cache.notify_discovery_item(user_id, cmd)
        return count


class DiscoveryTips(BaseTips):
    """
    发现入口小红点
    """
    def __init__(self, command_dict):
        self.command_dict = command_dict

    def query(self, user_id, cvc, chn):
        discovery_count = 0
        discovery_list = view_discovery(cvc, chn, user_id)
        if not discovery_list:
            return {}
        for discovery in discovery_list:
            cmd = discovery['cmd']
            discovery_count += CommandTips().query_by_cmd(user_id, cmd)
        return {'discovery': discovery_count}


def query_all(user_id, cvc, chn):
    tips = redis_cache.get_user_tips(user_id)
    if not tips:
        tips = {}
        tips.update(AwardTips().query(user_id))
        tips.update(ShowTips().query(user_id))
        tips.update(PartnerRewardTips().query(user_id))
        tips.update(DailySignTips().query(user_id))
        tips.update(LevelUpCouponTips().query(user_id))
        command_tips = CommandTips().query(user_id)
        tips.update(command_tips)
        tips.update(DiscoveryTips(command_tips).query(user_id, cvc, chn))
        redis_cache.set_user_tips(user_id, tips)
    return tips
