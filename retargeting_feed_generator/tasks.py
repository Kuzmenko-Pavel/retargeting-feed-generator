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

from retargeting_feed_generator.helper import image_link, price, text_normalize, url

tpl_xml_start = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE yml_catalog SYSTEM "shops.dtd">
<yml_catalog date="{date}">
<shop>
<name>{login}</name>
<company>{login}</company>
<url>https://yottos.com/</url>
<email>admin@yottos.com</email>
<currencies>
<currency id="UAH" rate="1"/>
</currencies>
<categories>
<category id="1">Товары</category>
</categories>
<offers>'''

tpl_xml_offer = '''<offer id='{offer_id}'>
<categoryId>1</categoryId>
<name>{name}</name>
<url>{url}</url>
<price>{price}</price>
<currencyId>UAH</currencyId>
<picture>{picture}</picture>
<logo>{logo}</logo>
<description>{description}</description>
<recommended>{recommended}</recommended>
<sale_count>{sale_count}</sale_count>
</offer>'''
tpl_xml_end = '''</offers>
</shop>
</yml_catalog>'''


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
          ,M.Title
          ,U.Login
      FROM Market as M
      INNER JOIN Users as U ON U.UserID = M.UserID
      where M.ExportLink not like '%yottos.com%'
    ''')
    for adv in result:
        user_id = adv[0]
        market_id = adv[1]
        title = re.sub('[^0-9a-zA-Z]+', '_', adv[2])
        login = re.sub('[^0-9a-zA-Z]+', '_', adv[3])
        data[(user_id, login)].append((("'%s'" % market_id), title))
    result.close()
    dbsession.commit()
    for key, value in data.items():
        create_feed.delay(key[0], key[1], value)
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(user_id, login, markets):
    print('START CREATE FEED %s' % user_id)
    ids = []
    data = defaultdict(lambda:{'markets': [], 'offers': []})
    r = redis.Redis(host='srv-13.yottos.com', port=6379, db=10)
    exists = r.exists('exists::%s' % user_id)
    if exists:
        for key in r.scan_iter(match='%s::*' % user_id, count=100):
            tmp = key.split(b'::')
            if len(tmp) == 2:
                of_id = tmp[1].decode('utf-8')
                try:
                    c = int(r.get(key))
                except Exception as e:
                    print(e)
                    c = 0
                if c > 0:
                    ids.append((of_id, c))
            if len(ids) > 100:
                break

    ids.sort(key=lambda x: x[1], reverse=True)
    if ids:
        for market_id, title in markets:
            data['ALL']['markets'].append(market_id.upper())
            data[title]['markets'].append(market_id.upper())
        if len(data['ALL']['markets']) > 0:
            for item in ids:
                dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
                market_ids = data['ALL']['markets']
                market_by_id = {str(x).upper(): str(y) for x, y in markets}
                result = dbsession.execute('''
                SELECT TOP 1 [Title]
                            ,[Descript]
                            ,[Price]
                            ,[ExternalURL]
                            ,[ImgURL]
                            ,[Logo]
                            ,[Recommended]
                            ,[MarketID]
                  FROM Lot
                  WHERE MarketID in (%s)
                  and RetargetingID= '%s'
                ''' % (','.join(market_ids), item[0]))
                for offer in result:
                    lot = {
                        'offer_id': item[0],
                        'name': text_normalize(offer[0]),
                        'description': text_normalize(offer[1]),
                        'price': price(offer[2]),
                        'url': url(offer[3]),
                        'picture': image_link(offer[4]),
                        'logo': image_link(offer[5]),
                        'recommended': offer[6],
                        'sale_count': item[1]
                    }
                    data['ALL']['offers'].append(lot)
                    market_title = market_by_id.get(str("'%s'" % offer[7]).upper())
                    if market_title:
                        data[market_title]['offers'].append(lot)
                result.close()
                dbsession.commit()
    for k, v in data.items():
        line = 0
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
        file_path = os.path.join(dir_path, "%s::%s::%s.xml" % (login, user_id, k))
        temp_file = file_path + '.' + str(int(time.time()))
        with open(temp_file, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            template_data = {
                'login': login,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            f.write(tpl_xml_start.format(**template_data))
            f.flush()
            for item in v.get('offers', []):
                f.write(tpl_xml_offer.format(**item))
                line += 1
                if line > 100:
                    f.flush()
                    break
                f.flush()
            f.write(tpl_xml_end)
            f.flush()
        move(temp_file, file_path)
    r.connection_pool.disconnect()
    del ids
    print('STOP CREATE FEED %s' % user_id)
