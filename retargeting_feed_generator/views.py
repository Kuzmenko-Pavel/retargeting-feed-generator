import os
from pyramid.view import view_config
from pyramid.view import forbidden_view_config
from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget
from collections import defaultdict

from retargeting_feed_generator.tasks import create_feed
from retargeting_feed_generator.helper import redirect_link, image_link, price


@view_config(route_name='index', renderer='templates/index.html', permission='view')
def index(request):
    result = request.dbsession.execute('select 1')
    return {'project': result}


@view_config(route_name='export', renderer='templates/xml.html', permission='view')
def export(request):
    request.response.content_type = 'application/xml'
    id = request.matchdict.get('id', '').upper()
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
    q = [
        'm.Name IS NOT NULL',
        'isActive=1'
    ]
    sql = '''
                            SELECT
                            a.AdvertiseID AS AdvertiseID,
                            Title,
                            Login, 
                            m.Name AS Manager,
                            CASE WHEN MarketID IS NULL THEN 'false' ELSE 'true' END Market
                            FROM View_Advertise a
                            LEFT OUTER JOIN Users u ON u.UserID = a.UserID
                            LEFT OUTER JOIN Manager m  ON u.ManagerID = m.id
                            LEFT OUTER JOIN MarketByAdvertise mark ON mark.AdvertiseID = a.AdvertiseID
                            WHERE %s
                            ''' % (' AND '.join(q))
    result = request.dbsession.execute(sql)
    for campaign in result:
        data.append((campaign[1], campaign[2],
                     "<a href='%s' target='_blank''>File Export</a>" % request.route_url('export',
                                                                                         id=campaign[0])
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