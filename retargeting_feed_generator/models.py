# -*- coding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from copy import copy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import MetaData
from zope.sqlalchemy import ZopeTransactionExtension


DBScopedSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: http://alembic.readthedocs.org/en/latest/naming.html
NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


Base = declarative_base(metadata=metadata)


from sqlalchemy import engine_from_config, event
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix, echo=False)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    dbsession = session_factory()
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def includeme(config):
    settings = config.get_settings()
    config.include('pyramid_tm')
    engine = get_engine(settings)
    engine.pool._use_threadlocal = True
    metadata.bind = engine
    DBScopedSession.configure(bind=engine)
    session_factory = get_session_factory(engine)
    config.registry['dbsession_factory'] = session_factory

    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )
