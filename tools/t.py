import time
import random

range_list=range(1,80000)
l1=range_list
exists_nums=range(200,7000)
random.shuffle(exists_nums)
print '%f' % time.time()
#exists_nums=[str(x) for x in exists_nums]
exists_nums = set(exists_nums)
exists_nums = set(exists_nums)
print '%f' % time.time()
range_list=[x for x in range_list if str(x) not in exists_nums]
#range_list=[x for x in range_list if x not in exists_nums]
print '%f' % time.time()
