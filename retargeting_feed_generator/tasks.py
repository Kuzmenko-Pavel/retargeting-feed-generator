# -*- coding: UTF-8 -*-
__author__ = 'kuzmenko-pavel'
import os
import time
from shutil import move

from pyramid_celery import celery_app as app

from retargeting_feed_generator.helper import redirect_link, image_link, price, text_normalize

tpl_xml_start = '''<?xml version="1.0"?>\n<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">\n<channel>
<title></title>\n<link>https://yottos.com</link>\n<description></description>'''

tpl_xml_offer = '''\n<item>\n<g:id>%s</g:id>\n<g:title>%s</g:title>\n<g:description>%s</g:description>
<g:link>%s</g:link>\n<g:image_link>%s</g:image_link>\n<g:price>%s</g:price>\n<g:condition>new</g:condition>
<g:availability>in stock</g:availability>
<g:google_product_category>111</g:google_product_category>
<g:gtin>2112345678900</g:gtin>
<g:brand>yottos.com</g:brand>
</item>'''
tpl_xml_end = '''\n</channel>\n</rss>'''


@app.task(ignore_result=True)
def check_feed():
    print('START RECREATE FEED')
    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    result = dbsession.execute('''SELECT
                                      a.AdvertiseID AS AdvertiseID
                                      FROM Advertise a
                                      LEFT OUTER JOIN MarketByAdvertise mark ON mark.AdvertiseID = a.AdvertiseID
                                      WHERE MarketID IS NOT NULL
                                        ''')
    for adv in result:
        create_feed.delay(adv[0])
    result.close()
    dbsession.commit()
    print('STOP RECREATE FEED')


@app.task(ignore_result=True)
def create_feed(id):
    print('START CREATE FEED %s' % id)
    count = 2000000
    q = '''
                    SELECT TOP %s  
                    View_Lot.LotID AS LotID,
                    View_Lot.Title AS Title,
                    ISNULL(View_Lot.Descript, '') AS Description,
                    ISNULL(View_Lot.Price, '0') Price,
                    View_Lot.ExternalURL AS UrlToMarket,
                    View_Lot.ImgURL,
                    RetargetingID,
                    View_Lot.Auther 
                    FROM View_Lot 
                    INNER JOIN LotByAdvertise ON LotByAdvertise.LotID = View_Lot.LotID
                    INNER JOIN View_Advertise ON View_Advertise.AdvertiseID = LotByAdvertise.AdvertiseID
                    WHERE View_Advertise.AdvertiseID = '%s' AND View_Lot.ExternalURL <> '' 
                        AND View_Lot.isTest = 1 AND View_Lot.isAdvertising = 1
                    ''' % (count, id)

    dbsession = app.conf['PYRAMID_REGISTRY']['dbsession_factory']()
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/xml')
    file_path = os.path.join(dir_path, id + ".xml")
    temp_file = file_path + '.' + str(int(time.time()))
    line = 0
    with open(temp_file, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
        f.write(tpl_xml_start)
        f.flush()
        result = dbsession.execute(q)
        for offer in result:
            data = ''
            try:
                offer_id = '%s...%s' % (offer[0], offer[7])
                if offer[6]:
                    offer_id = '%s...%s' % (offer[6], offer[7])
                data = tpl_xml_offer % (
                    offer_id,
                    text_normalize(str(offer[1])),
                    text_normalize(str(offer[2])),
                    redirect_link(offer[4], offer[0], id),
                    image_link(offer[5]),
                    price(offer[3])
                )
            except Exception as e:
                print(e)
            else:
                f.write(data)
            line += 1
            if line % 1000 == 0:
                print('Writen %d offers' % line)
                f.flush()
        result.close()
        f.flush()
        f.write(tpl_xml_end)
        f.flush()
    dbsession.commit()
    move(temp_file, file_path)
    print('STOP CREATE FEED %s on %d offers' % (id, line))
