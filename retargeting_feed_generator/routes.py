# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'


def includeme(config):
    config.add_route('index', '/')
    config.add_route('feeds', '/feeds')
    config.add_route('check_feed', '/check_feed')
    config.add_route('export', '/export/{id}.xml')
    config.add_static_view('static', 'static', cache_max_age=0)
