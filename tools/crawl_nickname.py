import time
import urllib2
import requests
from lxml import etree

#base_url = 'https://www.reddit.com/?count=100&after=t3_4y32kk'
base_url = 'https://www.reddit.com/new/'
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
}

fp = open('./crawled_nickname', 'a')

nickname_set = set()

#r = urllib2.urlopen(base_url)
def crawl_page(page_url):
    r = requests.get(page_url, headers=_HEADERS)
    html_page = r.content
    html_tree = etree.HTML(html_page)
    authors = html_tree.xpath('//a[contains(@class, "author")]')
    for author in authors:
        nickname_set.add(author.text)
        fp.write('%s\n' % author.text)

    next_url = html_tree.xpath('//span[@class="nextprev"]')[0].xpath('//a[@rel="nofollow next"]/@href')[0]
    print nickname_set
    print len(nickname_set)
    fp.flush()
    time.sleep(1)
    crawl_page(next_url)


if __name__ == "__main__":
    crawl_page(base_url)
    print nickname_set
    fp.close()
