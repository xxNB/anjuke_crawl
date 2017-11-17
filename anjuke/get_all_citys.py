# -*- coding: utf-8 -*-
"""
Created on 2017/11/16 下午8:49
@author: SimbaZhang
"""

import requests
from bs4 import BeautifulSoup as bs


def get_all_citys():
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
    }
    url = 'https://m.anjuke.com/cityList/'
    html = requests.get(url, headers=headers).text
    soup = bs(html, 'lxml')
    items = soup.select('ul > li > a')
    with open('citys.txt', 'w') as f:
        for ix, item in enumerate(items):
                f.write(item.get('href') + '\t' + item.get_text().strip() + '\n')
                if ix % 100 == 0:
                    print(ix)

if __name__ == '__main__':
    get_all_citys()