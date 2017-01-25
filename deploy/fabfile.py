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
PROJECT_ROOT = path.dirname(CUR_DIR)
SETTINGS = {}
# DIR name should endswith '/'
REMOTE_PROJECT_DIR = '/home/ubuntu/af-env/'
REMOTE_PROJECT_NAME = {'luckyservice-id': 'luckyservice'}
REMOTE_VIRENV = '/home/ubuntu/af-env/'
REMOTE_USER = 'ubuntu'
LOG_PATH = '/var/log/lucky/'


@task
def dep(name='aliyun'):
    """choose env name, for example: aliyun
    """
    global SETTINGS
    setting_file = path.join(CUR_DIR, '%s/deploy.json' % name)
    with open(setting_file) as f:
        SETTINGS = json.load(f)

    env.warn_only = True
    env.colorize_errors = True
    env.key_filename = path.expanduser(
        SETTINGS['default'].get('key_filename', ''))
    env.need_confirm = SETTINGS['default'].get('need_confirm', True)
    if not env.key_filename and 'password' in SETTINGS['default']:
        env.password = SETTINGS['default']['password']


@task
def pro(name='luckyservice-id'):
    """choose project name, for example: luckyservice
    """
    if not SETTINGS:
        # load default env
        dep()
    login_names = SETTINGS.get('default', {})
    user = login_names.get(getpass.getuser()) if login_names.get(getpass.getuser()) else login_names.get('user')
    env.project_name = name
    for host in SETTINGS['env'][name]:
        env.hosts.append(user + '@' + host)


@task
def envinstall(is_restart=True):
    if not confirm('install dependency'):
        return
    dependencies = SETTINGS['dependency'].get(env.project_name, [])
    for dependency in dependencies:
        if isinstance(dependency, dict):
            for k, v in dependency.iteritems():
                sudo('%s %s' % (k, ' '.join(v)))
        elif isinstance(dependency, basestring):
            sudo(dependency)

    if 'pip install virtualenv' in dependencies:
        sudo('chown -R %s /home/%s/.cache/pip' % (REMOTE_USER, REMOTE_USER))
        if not files.exists('%sbin/python' % REMOTE_VIRENV):
            sudo('virtualenv --no-site-packages %s' % REMOTE_VIRENV)
            sudo('chown -R %s %s' % (REMOTE_USER, REMOTE_VIRENV))
        put('%s/requirement.txt' % CUR_DIR, '/tmp/requirement.txt')
        sudo('source %s/bin/activate && pip install -r /tmp/requirement.txt' % (
            REMOTE_VIRENV,))
        run('rm /tmp/requirement.txt')

    sudo('mkdir -p %s' % LOG_PATH)
    sudo('chown -R %s %s' % (REMOTE_USER, LOG_PATH))


@task
def deploy(is_restart=True):
    if 'confirm' not in env and not confirm('deploy'):
        return

    is_restart = bool(strtobool(str(is_restart)))
    temp_folder = '/tmp/' + str(uuid.uuid4())
    r_temp_folder = '/tmp/' + str(uuid.uuid4())
    local('mkdir %s' % temp_folder)
    project_path = find_path(env.project_name)
    local('cp -r %s %s' % (project_path, temp_folder))

    package_dir = path.join(temp_folder, env.project_name)
    with lcd(package_dir):
        special_env_dct = SETTINGS['env'].get(env.project_name, {}).get(env.host)
        for binfile, commands in special_env_dct.iteritems():
            for command in commands:
                if binfile == 'bash' or binfile == 'shell':
                    local(command)
        if 'debug' in special_env_dct and env.debug == '1':
            for command in special_env_dct['debug']:
                local(command)

    with lcd(temp_folder):
        local('tar cf {0}.tar.gz --exclude "*.pyc" --exclude="*.deb" --exclude=".git" {0}'.format(env.project_name))
        run("mkdir -p %s" % r_temp_folder)
        put('%s.tar.gz' % package_dir, r_temp_folder)

    with cd(r_temp_folder):
        run("tar xf %s.tar.gz" % env.project_name)
        pj = REMOTE_PROJECT_NAME.get(env.project_name, env.project_name)
        sudo('rm -r %s/%s-backup' % (REMOTE_PROJECT_DIR, pj))
        sudo("mv {0}/{1} {0}/{1}-backup".format(
            REMOTE_PROJECT_DIR, pj))
        if env.project_name != pj:
            sudo("mv %s %s" % (env.project_name, pj))
        sudo("mv %s %s" % (pj, REMOTE_PROJECT_DIR))
        sudo('chown -R %s %s' % (REMOTE_USER, REMOTE_PROJECT_DIR))
    sudo('rm -r %s' % r_temp_folder)
    local('rm -rf %s' % temp_folder)
    # restart(env.project_name, is_restart)
    if env.project_name == 'luckyservice-id':
        sudo("killall uwsgi")
    print green('deploy %s@%s done' % (env.project_name, env.host))


@task
def restore():
    sudo('rm -r %s/%s' % (REMOTE_PROJECT_DIR, env.project_name))
    sudo('mv {0}/{1}-backup {0}/{1}'.format(
        REMOTE_PROJECT_DIR, env.project_name))
    restart(env.project_name)
    print green('restore done')


def confirm(task_name):
    if env.need_confirm:
        if not console.confirm(
                        'Are you sure you want to %s' % task_name, default=True):
            return False
    return True


def find_path(project_name):
    current_dir = PROJECT_ROOT
    while current_dir != '/':
        for f in listdir(current_dir):
            if f == project_name and path.isdir(path.join(current_dir, f)):
                return path.join(current_dir, f)
        current_dir = path.dirname(current_dir)
    raise Exception('source folder not found!')


def restart(project_name, is_restart=True):
    scripts_dir = "%s/%s/scripts" % (REMOTE_PROJECT_DIR, project_name)
    if files.exists(scripts_dir, use_sudo=True):
        with cd(scripts_dir):
            if not is_restart:
                sudo('bash reconfig.sh')
            else:
                sudo('bash restart.sh')


# Regular expression for comments
comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)
