from bs4 import BeautifulSoup

s = open('facebook.html')
s = s.read()
m = BeautifulSoup(s)
l= m.find_all('img')
to = open('furl.txt','w')
for i in l:
    to.write(i['src'])
    to.write('\n')
to.close()

