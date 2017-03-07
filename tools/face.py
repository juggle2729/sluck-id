import urllib
import uuid
from time import sleep

from bs4 import BeautifulSoup

_dir = '/Users/mm/tmp/'

# save facebook friends page div to facebook.html
s = open(_dir + 'facebook.html')
s = s.read()
html_soup = BeautifulSoup(s, 'lxml')

# find all avatar urls
# avatars = []
# l = html_soup.find_all('img')
# for i in l:
#     avatars.append(i['src'])
#
# for avatar_link in avatars:
#     sleep(0.5)
#     name = str(uuid.uuid4()) + '.jpeg'
#     try:
#         r = urllib.urlopen(avatar_link)
#         obj = r.read()
#         ft = open('./avatars/' + name, 'wb')
#         ft.write(obj)
#         ft.close()
#     except Exception:
#         continue

# find all nicknames

nicknames = []
divs = html_soup.find_all('div', {'class': 'fsl'})
nickname_file = open('./nicknames.txt', 'w')
for div in divs:
    a = div.find_all('a')[0]
    try:
        nickname_file.write(a.text + u'\n')
    except Exception:
        print type(a.text), a.text
        continue
nickname_file.close()
