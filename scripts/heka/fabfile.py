# -*- coding: utf-8 -*-
import os
import json
import re
import uuid
import getpass
from os import path, listdir
from distutils.util import strtobool

from fabric.context_managers import lcd, cd
from fabric.contrib import console, files
from fabric.operations import local, put, sudo, run
from fabric.state import env
from fabric.colors import green
from fabric.api import task, parallel

CUR_DIR = path.dirname(path.abspath(__file__))
DEB = path.join(CUR_DIR, 'heka_0.10.0_amd64.deb')
CONFIG_FILE = 'lucky.toml'
CONFIG_PATH = path.join(CUR_DIR, CONFIG_FILE)
USER = 'terran'
#TARGETS = ['120.27.162.212', '121.41.86.172', '121.40.49.87', '121.199.0.80']
TARGETS = ['127.0.0.1']
SETTINGS = {}
KEY_FILE = ''

@task
def init():
    global SETTINGS
    env.warn_only = True
    env.colorize_errors = True
    env.need_confirm = True
    for t in TARGETS:
        env.hosts.append('%s@%s' % (USER, t))


@task
def reconfig():
    if not SETTINGS:
        init()
    if not confirm('update config file'):
        return
    put(CONFIG_PATH, '/tmp/')
    sudo('mv /tmp/%s /etc/heka/lucky.toml' % CONFIG_FILE)
    sudo('pkill -f hekad')
    run('nohup sudo hekad -config /etc/heka/lucky.toml >> /tmp/hekad.log 2>&1 &', pty=False)


@task
def update():
    if not SETTINGS:
        init()
    if not confirm('update deb file'):
        return
    put(DEB, '/tmp/')
    sudo('apt-get install screen')
    with cd('/tmp/'):
        sudo('pkill -f hekad')
        sudo('dpkg -i heka_0.10.0_amd64.deb')
    run('nohup sudo hekad -config /etc/heka/lucky.toml >> /tmp/hekad.log 2>&1 &', pty=False)

def confirm(tips):
    if env.need_confirm:
        if not console.confirm('Are you sure to %s' % tips, default=True):
            return False
    return True
