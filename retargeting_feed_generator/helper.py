import html
import re


price_clean = re.compile(r'[^0-9]')


def image_link(url):
    url = url.split(',')
    url = [html.escape(x) for x in url]
    return url[0]


def price(p):
    p = price_clean.sub('', p)
    return '%s' % p


def text_normalize(text):
    words = text.split()
    upper_words = [word for word in words if word.isupper()]
    if len(upper_words) >= len(words):
        text = text.capitalize()
    return html.escape(text)