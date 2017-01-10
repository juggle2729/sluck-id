import os

f_list = []
for r,d,f in os.walk('./20160121/avatars'):
    f_list.append(f) 

f_list=f_list[0]
fd = open('./20160121/avatar_list', 'w')
for f in f_list:
    item = 'http://7xov75.com2.z0.glb.qiniucdn.com/avatars/%s\n' % f
    print item
    fd.write(item)

fd.close()
