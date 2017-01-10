# -*- coding: utf-8 -*-
import facebook


def get_user_profile(access_token):
    third_id, username = get_current_user_name(access_token)
    avatar_url = get_current_user_avatar_url(access_token)
    return third_id, username, avatar_url


def get_current_user_name(access_token):
    return get_user_name('me', access_token)


def get_current_user_avatar_url(access_token):
    return get_user_avatar_url('me', access_token)


def get_user_name(third_id, access_token):
    graph = facebook.GraphAPI(access_token=access_token, version='2.7')
    object_id = '%s' % third_id
    data = graph.get_object(id=object_id)
    return data.get('id'), data.get('name')


def get_user_avatar_url(third_id, access_token):
    graph = facebook.GraphAPI(access_token=access_token, version='2.7')
    object_id = '%s/picture' % third_id
    data = graph.get_object(id=object_id, type='large')
    return data.get('url')

