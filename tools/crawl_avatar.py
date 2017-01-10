import json
import re
import sys
import uuid
from pprint import pprint
from time import sleep

import urllib
from bs4 import BeautifulSoup
from datetime import date

import os
import requests

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
}

host = 'http://www.xosothantai.com/'
start_url = 'http://www.xosothantai.com/index.php'
response = requests.get(start_url, headers=_HEADERS)
html_soup = BeautifulSoup(response.content, "lxml")
d = html_soup.find_all('div', {'class': 'membersOnline'})[0]
d_soup = BeautifulSoup(str(d), "lxml")
lis = d_soup.find_all('li')
profile_url_list = []
for li in lis:
    li_soup = BeautifulSoup(str(li), "lxml")
    a = li_soup.find_all('a')[0]
    profile_url = host + a['href']
    profile_url_list.append(profile_url)

# print profile_url_list

avatar_list = []
for profile_url in profile_url_list:
    sleep(0.5)
    profile_response = requests.get(profile_url, headers=_HEADERS)
    profile_soup = BeautifulSoup(profile_response.content, "lxml")
    avatars = profile_soup.find_all('div', {'class': 'avatarScaler'})
    friends = profile_soup.find_all('a', {'class': 'avatar'})
    if len(avatars) == 0:
        continue
    avatar_soup = BeautifulSoup(str(avatars[0]), "lxml")
    avatar_img = avatar_soup.find('img')
    if avatar_img:
        avatar_url = avatar_img['src']
        if 'default' not in avatar_url:
            avatar_list.append(avatar_url)
    for friend in friends:
        friend_soup = BeautifulSoup(str(friend), "lxml")
        span = friend_soup.find('span')
        if span:
            style = span.get('style')
            if style and 'default' not in style:
                url = host + re.findall(r'\'(.*)\'', style)[0]
                url = url.replace('/s/', '/l/')
                avatar_list.append(url)

print avatar_list


for avatar_link in avatar_list:
    sleep(0.5)
    name = str(uuid.uuid4()) + '.jpeg'
    r = urllib.urlopen(avatar_link)
    obj = r.read()
    ft = open('./avatars/' + name, 'wb')
    ft.write(obj)
