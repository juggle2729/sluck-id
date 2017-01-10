import threading, time, httplib, random


urls = [
	"/api/v1/activitys?status=6&page=",
]
MAX_PAGE = 10
SERVER_NAME = "www.1yuan-gou.com"
TEST_COUNT = 10


class RequestThread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.test_count = 0
        self.thread_name = thread_name

    def run(self):
        i = 0
        while i < TEST_COUNT:
            self.test_performace()
            i += 1
        #self.test_other_things()

    def test_performace(self):
        conn = httplib.HTTPConnection(SERVER_NAME)
        for i in range(0, random.randint(0, 100)):
            url = urls[random.randint(0, len(urls) - 1)];
            url += str(random.randint(0, MAX_PAGE))
            print self.thread_name, url
            try:
                conn.request("GET", url)
                rsps = conn.getresponse()
                if rsps.status == 200:
                    data = rsps.read()
                self.test_count += 1
            except:
                continue
        conn.close()
		
start_time = time.time()
threads = []
thread_count = 10

i = 0
while i < thread_count:
    t = RequestThread("thread" + str(i))
    threads.append(t)
    t.start()
    i += 1

# cmd
word = ""
while True:
    word = raw_input("cmd:")
    if word == "s":
        time_span = time.time() - start_time
        all_count = 0
        for t in threads:
            all_count += t.test_count
        print "%s Request/Second" % str(all_count / time_span)
    elif word == "e":
        TEST_COUNT = 0
        for t in threads:
            t.join(0)
        break
