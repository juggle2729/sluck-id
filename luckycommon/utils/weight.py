'''This algorithm is for weighted sample without replacement.
http://stackoverflow.com/questions/2140787/select-random-k-ele\
ments-from-a-list-whose-elements-have-weights/2149533#2149533'''

import random


class Node:
    __slots__ = ['w', 'v', 'tw']

    def __init__(self, w, v, tw):
        self.w, self.v, self.tw = w, v, tw


def rws_heap(items):
    h = [None]
    for item in items:
        h.append(Node(item['weight'], item, item['weight']))
    for i in range(len(h) - 1, 1, -1):
        h[i >> 1].tw += h[i].tw
    return h


def rws_heap_pop(h):
    gas = h[1].tw * random.random()
    i = 1

    while gas > h[i].w:
        gas -= h[i].w
        i <<= 1
        if gas > h[i].tw:
            gas -= h[i].tw
            i += 1
    w = h[i].w
    v = h[i].v
    # set weight to 0, make sure not chosen again
    # so the original weight of the node can't be 0,
    # or we will have duplicated values.
    h[i].w = 0
    while i:
        h[i].tw -= w
        i >>= 1
    return v


def weight_sample(items, n):
    heap = rws_heap(items)
    for i in range(n):
        yield rws_heap_pop(heap)
