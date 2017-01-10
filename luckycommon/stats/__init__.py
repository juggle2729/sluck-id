# -*- coding: utf-8 -*-
from pymongo import MongoClient
from django.conf import settings

MG = MongoClient(settings.MONGO_ADDR).lucky
HP = MongoClient(settings.MONGO_ADDR).helper
