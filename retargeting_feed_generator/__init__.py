# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Authenticated


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    includeme(config, global_config)
    app = config.make_wsgi_app()
    return app


def check_credentials(username, password, request):
    if username == 'yottos' and password == '123qwe':
        return []


class Root:
    __acl__ = (
        (Allow, Authenticated, ALL_PERMISSIONS),
    )


def includeme(config, global_config):
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_search_path("retargeting_feed_generator:templates")
    authn_policy = BasicAuthAuthenticationPolicy(check_credentials)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_root_factory(lambda request: Root())
    config.include('pyramid_celery')
    config.configure_celery(global_config['__file__'])
    config.include('.models')
    config.include('.routes')
    config.commit()
    config.scan()
