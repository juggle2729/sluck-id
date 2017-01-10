import json
import sys
from bs4 import BeautifulSoup
from datetime import date

import os
import requests

# add up one level dir into sys path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'luckyplatform.settings'

from luckycommon.lottery.internal_handler import save_lottery

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
}

_PROVIDERS = {
    'baidu': {
        'url': 'http://baidu.lecai.com/lottery/ajax_latestdrawn.php?lottery_type=200',
        'reference': 'http://baidu.lecai.com/lottery/draw/sorts/cqssc.php',
    },
    '163': {
        'url': 'http://caipiao.163.com/award/daily_refresh.html?gameEn=ssc&selectDate=1&date=',
        'reference': 'http://baidu.lecai.com/lottery/draw/sorts/cqssc.php',
    },
    'taiwanlottery': {
        'url': 'http://www.taiwanlottery.com.tw/Lotto/BINGOBINGO/drawing.aspx',
        'reference': 'http://www.taiwanlottery.com.tw/Lotto/BINGOBINGO/drawing.aspx',
    },
}


def get_lottery(provider):
    today = date.today().strftime('%Y%m%d')
    if provider == 'baidu':
        url = _PROVIDERS[provider]['url']
        response = requests.get(url, headers=_HEADERS)
        data = json.loads(response.text)
        phase = data['data'][0]['phase']
        number = ''.join(data['data'][0]['result']['result'][0]['data'])
        reference = _PROVIDERS[provider]['reference'] + '?date=' + today
        save_lottery(phase, number, reference)
    if provider == '163':
        url = _PROVIDERS[provider]['url'] + today
        response = requests.get(url, headers=_HEADERS)
        soup = BeautifulSoup(response.content, "lxml")
        tds = soup.find_all('td', {'class': 'start'})
        for td in tds:
            if td.get('data-win-number'):
                phase = today + td.get_text()
                number = td.get('data-win-number').replace(' ', '')
                reference = _PROVIDERS[provider]['reference'] + '?date=' + today
                save_lottery(phase, number, reference)
    if provider == 'taiwanlottery':
        url = _PROVIDERS[provider]['url']
        reference = _PROVIDERS[provider]['reference']
        response = requests.get(url, headers=_HEADERS)
        soup = BeautifulSoup(response.content, "lxml")
        tds = soup.find_all('td', {'class': 'thB'})
        for td in tds:
            table = td.table
            if table:
                for tr in table.find_all('tr'):
                    text = tr.get_text()
                    data_list = text.split(' ')
                    if len(data_list) == 22:
                        phase = data_list[0][:-2]
                        number = data_list[0][-2:] + data_list[-2] + data_list[-1][0:2]
                        save_lottery(phase, number, reference)


if __name__ == '__main__':
    get_lottery('taiwanlottery')
