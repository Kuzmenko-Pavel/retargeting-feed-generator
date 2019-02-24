# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from shutil import move

import redis
from pyramid_celery import celery_app as app

# from retargeting_feed_generator.helper import redirect_link, image_link, price, text_normalize

tpl_xml_start = '''
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE yml_catalog SYSTEM "shops.dtd">
<yml_catalog date="{date}">
<shop>
<name>{login}</name>
<company>{login}</company>
<url>https://yottos.com/</url>
<email>admin@yottos.com</email>
<currencies>
</currencies>
<categories>
</categories>
<offers>
'''

tpl_xml_offer = '''
<offer id='{offer_id}'>
<name>{name}</name>
<url>{url}</url>
<price>{price}</price>
<currencyId>UAH</currencyId>
<picture>{picture}</picture>
<logo>{logo}</logo>
<description>{description}</description>
<recommended>{recommended}</recommended>
</offer>
'''
tpl_xml_end = '''
</offers>
</shop>
</yml_catalog>
'''


@app.task(ignore_result=True)
def check_feed():
    print('START RECREATE FEED')
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    for the_file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    data = defaultdict(lambda: list())
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    result = dbsession.execute('''
        SELECT M.UserID
          ,M.MarketID
          ,U.Login
      FROM Market as M
      INNER JOIN Users as U ON U.UserID = M.UserID
      where M.ExportLink not like '%yottos.com%'
    ''')
    for adv in result:
        user_id = adv[0]
        market_id = adv[1]
        login = re.sub('[^0-9a-zA-Z]+', '_', adv[2])
        data[(user_id, login)].append("'%s'" % market_id)
    result.close()
    dbsession.commit()
    for key, value in data.items():
        create_feed.delay(key[0], key[1], value)
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(user_id, login, market_ids):
    print('START CREATE FEED %s' % user_id)
    line = 0
    ids = []
    r = redis.Redis(host='srv-13.yottos.com', port=6379, db=10)
    exists = r.exists('exists::%s' % user_id)
    if exists:
        for key in r.scan_iter(match='%s::*' % user_id, count=100):
            tmp = key.split(b'::')
            if len(tmp) == 2:
                of_id = tmp[1].decode('utf-8')
                c = int(r.get(key))
                if c > 0:
                    ids.append((of_id, c))

            # if len(ids) > 100:
            #     break

    ids.sort(key=lambda x: x[1], reverse=True)
    if ids:
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
        file_path = os.path.join(dir_path, "%s::%s.xml" % (login, user_id))
        temp_file = file_path + '.' + str(int(time.time()))
        with open(temp_file, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            data = {
                'login': login,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            f.write(tpl_xml_start.format(**data))
            f.flush()
            for item in ids:
                dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
                result = dbsession.execute('''
                SELECT [Title]
                      ,[Descript]
                      ,[Price]
                      ,[ExternalURL]
                      ,[ImgURL]
                      ,[Logo]
                      ,[Recommended]
                  FROM Lot
                  WHERE Auther = '%s'
                  and MarketID in (%s)
                  and RetargetingID= '%s'
                ''' % (user_id, ','.join(market_ids), item[0]))
                for offer in result:
                    data = {
                        'offer_id': item[0],
                        'name': offer[0],
                        'description': offer[1],
                        'price': offer[2],
                        'url': offer[3],
                        'picture': offer[4],
                        'logo': offer[5],
                        'recommended': offer[6]
                    }
                    f.write(tpl_xml_offer.format(**data))
                    line += 1
                    if line % 1000 == 0:
                        print('Writen %d offers' % line)
                        f.flush()
                result.close()
                dbsession.commit()
            f.flush()
            f.write(tpl_xml_end)
            f.flush()
        move(temp_file, file_path)
    r.connection_pool.disconnect()
    del ids
    print('STOP CREATE FEED %s on %d offers' % (user_id, line))
