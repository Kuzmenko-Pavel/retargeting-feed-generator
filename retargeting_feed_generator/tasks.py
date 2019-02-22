# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
import os
import time
from shutil import move

from pyramid_celery import celery_app as app

# from retargeting_feed_generator.helper import redirect_link, image_link, price, text_normalize

tpl_xml_start = ''''''

tpl_xml_offer = ''''''
tpl_xml_end = ''''''


@app.task(ignore_result=True)
def check_feed():
    print('START RECREATE FEED')
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    result = dbsession.execute('''''')
    for adv in result:
        pass
    result.close()
    dbsession.commit()
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(id):
    print('START CREATE FEED %s' % id)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    file_path = os.path.join(dir_path, id + ".xml")
    temp_file = file_path + '.' + str(int(time.time()))
    line = 0
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
    print('STOP CREATE FEED %s on %d offers' % (id, line))
