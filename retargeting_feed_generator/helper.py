import base64
import html
import re
from random import randint

price_clean = re.compile(r'[^0-9]')


def redirect_link(url, guid, campaign_guid):
    offer_url = url
    base64_url = base64.urlsafe_b64encode(str('id=%s\nurl=%s\ncamp=%s' % (
        guid,
        offer_url,
        campaign_guid
    )).encode('utf-8'))
    params = 'a=%s&amp;b=%s&amp;c=%s' % (randint(1, 9), base64_url.decode('utf-8'), randint(1, 9))
    return 'https://click.yottos.com/click/fb?%s' % params


def image_link(url):
    url = url.split(',')
    url = [html.escape(x) for x in url]
    return url[0]


def price(p):
    p = price_clean.sub('', p)
    return '%s UAH' % p


def text_normalize(text):
    words = text.split()
    upper_words = [word for word in words if word.isupper()]
    if len(upper_words) >= len(words):
        text = text.capitalize()
    return html.escape(text)