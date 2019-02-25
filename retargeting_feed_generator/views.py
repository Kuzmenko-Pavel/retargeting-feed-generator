import os

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.response import FileResponse
from pyramid.security import forget
from pyramid.view import forbidden_view_config
from pyramid.view import view_config
from retargeting_feed_generator import tasks


@view_config(route_name='index', renderer='templates/index.html', permission='view')
def index(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}


@view_config(route_name='check_feed', renderer='json', permission='view')
def check_feed(request):
    tasks.check_feed.delay()
    return {}


@view_config(route_name='export', renderer='templates/xml.html')
def export(request):
    request.response.content_type = 'application/xml'
    id = request.matchdict.get('id', '')
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    file_path = os.path.join(dir_path, id + ".xml")
    file_exists = os.path.isfile(file_path)
    if id:
        if file_exists:
            response = FileResponse(
                file_path,
                request=request,
                content_type=request.response.content_type
            )
            return response
    return {}


@view_config(route_name='feeds', renderer='json', permission='view')
def feeds(request):
    data = []
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    files = os.listdir(dir_path)
    for name in files:
        if '.xml' in name:
            name = name.replace('.xml', '')
            tmp = name.split('::')
            if len(tmp) == 2:
                data.append((tmp[1],
                             tmp[0],
                             "<a href='%s' target='_blank''>File Export</a>" % request.route_url('export', id=name)
                             ))
    return {
        'data': data
    }


@forbidden_view_config()
def forbidden_view(request):
    if request.authenticated_userid is None:
        response = HTTPUnauthorized()
        response.headers.update(forget(request))
    else:
        response = HTTPForbidden()
    return response
