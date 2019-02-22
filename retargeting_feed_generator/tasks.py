# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
import os
import time
from shutil import move
from collections import defaultdict
import re
import redis

from pyramid_celery import celery_app as app

# from retargeting_feed_generator.helper import redirect_link, image_link, price, text_normalize

tpl_xml_start = ''''''

tpl_xml_offer = ''''''
tpl_xml_end = ''''''


@app.task(ignore_result=True)
def check_feed():
    print('START RECREATE FEED')
    data = defaultdict(lambda: list())
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    result = dbsession.execute('''
        SELECT M.UserID
          ,M.MarketID
          ,U.Login
      FROM [Adload].[dbo].[Market] as M
      INNER JOIN [Adload].[dbo].[Users] as U ON U.UserID = M.UserID
      where M.ExportLink not like '%yottos.com%'
    ''')
    for adv in result:
        user_id = adv[0]
        market_id = adv[1]
        login = re.sub('[^0-9a-zA-Z]+', '_', adv[2])
        data[(user_id, login)].append(market_id)
    result.close()
    dbsession.commit()
    for key, value in data.items():
        create_feed(key[0], key[1], value)
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(user_id, login, market_ids):
    print('START CREATE FEED %s' % user_id)
    ids = []
    r = redis.Redis(host='srv-13.yottos.com', port=6379, db=10)
    for key in r.scan_iter(match='%s:*' % user_id):
        of_id = key.split(':')[1]
        c = r.get(key)
        ids.append((of_id, c))

    ids.sort(key=lambda x: x[1], reverse=True)
    line = 0
    if ids:
        print(ids[:15])
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
        file_path = os.path.join(dir_path, "%s::%s.xml" % (login, user_id))
        temp_file = file_path + '.' + str(int(time.time()))
        with open(temp_file, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            f.write(tpl_xml_start)
            f.flush()
            result = []
            for offer in result:
                data = ''
                try:
                    data = tpl_xml_offer % ()
                except Exception as e:
                    print(e)
                else:
                    f.write(data)
                line += 1
                if line % 1000 == 0:
                    print('Writen %d offers' % line)
                    f.flush()
            f.flush()
            f.write(tpl_xml_end)
            f.flush()
        move(temp_file, file_path)
    print('STOP CREATE FEED %s on %d offers' % (user_id, line))
