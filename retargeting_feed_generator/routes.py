# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'


def includeme(config):
    config.add_route('index', '/')
    config.add_route('feeds', '/feeds')
    config.add_route('export', '/export/{id:[0-9a-fA-F\-]{36}}.xml')
    config.add_static_view('static', 'static', cache_max_age=0)
