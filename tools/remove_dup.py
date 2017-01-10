# -*- coding: utf-8 -*-
import codecs

fd = codecs.open("./user.t", "r", "utf-8")

ip_set = set()
user_list = []

for line in fd:
    line = line.strip()
    print line
    if len(line.split('\t')) != 3:
        continue
    nick_name, ip, avatar = line.split('\t')
    if ip in ip_set:
        continue
    ip_set.add(ip)
    user_list.append({
        'nick_name': nick_name,
        'ip': ip,
        'avatar': '' if avatar=='160.jpeg' else avatar
    })


print 'got %d user' % len(user_list)

ft = codecs.open("./user_latest", "w", 'utf-8')
for user in user_list:
    nick_name = user['nick_name']
    ip = user['ip']
    avatar = user['avatar']
    ft.write('%s\t%s\t%s\n' % (nick_name, ip, avatar))
