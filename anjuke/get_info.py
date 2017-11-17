# -*- coding: utf-8 -*-
"""
Created on 2017/11/16 下午9:05
@author: SimbaZhang
"""

import requests
import MySQLdb
import os
import logzero
from cos_lib3.cos import Cos
from bs4 import BeautifulSoup as bs
from config import change_form, field

class Crawl:
    def __init__(self):
        self.headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
        }
        self.pic_path = os.path.dirname(os.path.dirname(__file__))
        self.db = self.db_connect()[0]
        self.cur = self.db_connect()[1]
        self.bucket = self.cloud_tenxun()
        self.pic_path = self.make_path()
        self.city = str()
        self.file_name = str()
        pass

    def make_path(self):
        try:
            os.mkdir(os.path.dirname(os.path.dirname(__file__)) + '/xiaoqu_pic')
        except FileExistsError:
            pass
        except:
            raise Exception('os path make fail...')
        finally:
            return os.path.dirname(os.path.dirname(__file__)) + '/xiaoqu_pic'

    def db_connect(self):
        conn = MySQLdb.connect(
            host='192.168.1.106',
            port=3306,
            user='root',
            passwd='123456',
            db='anjuke',
        )
        return conn, conn.cursor()

    def cloud_tenxun(self):
        cos = Cos(app_id=1251013204, secret_id='AKIDhKl0Xu66uWw9Aze1EF4iAQWQBk7HM5jA',
                  secket_key='NYXfgVAf2IOK3av8A0d6MQOBoBQTPBl9', region='sh')
        bucket = cos.get_bucket("xq")
        return bucket

    def get_city_xiaoqu(self):
        with open('citys.txt', 'r') as f:
            for item in f.readlines():
                city_url = item.split('\t')[0]
                city = item.split('\t')[1].strip()
                xiaoqu_dict = {'city': city, 'city_xiaoqu': city_url+'xiaoqu/'}
                self.city = city
                yield xiaoqu_dict

    def get_xiaoqu_url(self):
        for url_dict in self.get_city_xiaoqu():
            html = requests.get(url_dict.get('city_xiaoqu'), headers=self.headers).text
            soup = bs(html, 'lxml')
            items = soup.select('div.itemsCont > div > a')
            url_iter = map(lambda x: x.get('href'), items)
            logzero.logger.info('=' * 250)
            logzero.logger.info('开始收集%s' % self.city)
            logzero.logger.info('=' * 250)
            yield from url_iter

    def get_xiaoqu_info(self):
        for ix, url in enumerate(self.get_xiaoqu_url()):
            print(url)
            self.worker(url)
            if ix % 100 == 0 and ix != 0:
                logzero.logger.info('%s小区已收集%s' % (self.city, ix))

    @staticmethod
    def get_text(item):
        return item.get_text().strip()

    def push_picture(self):
        file_name = '%s.jpg' % self.pic_name
        self.bucket.upload_file(real_file_path=self.pic_path+'/'+file_name, file_name=file_name, dir_name='anjuke')
        print('pic has ben upload success')

    def worker(self, url):
        html = requests.get(url, headers=self.headers).text
        soup = bs(html, 'lxml')
        xiaoqu_name = self.get_text(soup.select('div.price-mod > div.comm-tit > h1')[0])
        average_price = self.get_text(soup.select('div > p.price')[0])
        price_text = self.get_text(soup.select('div > p.desc-text')[0])
        xiaoqu_area = self.city + self.get_text(soup.select('div.comm-tit > div > p')[0]).split('：')[1]
        month_price_change = self.get_text(soup.select('div > p.price > span')[0])[1:]
        mouth_change_form = change_form.get(soup.select('div > p.price > span')[0].get('class')[0])
        year_price_change = self.get_text(soup.select('div > p.price > span')[1])[1:]
        year_change_form = change_form.get(soup.select('div > p.price > span')[0].get('class')[0])
        new_price = price_text + average_price
        xiaoqu_type = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[0]).split('：')[1]
        wuyefee = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[1]).split('：')[1]
        time_of_completion = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[2]).split('：')[1]
        green_rate = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[3]).split('：')[1]
        total_num = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[4]).split('：')[1]
        plot_ratio = self.get_text(soup.select('div.comm-mod.comm-brief-mod > div > span')[5]).split('：')[1]
        brief_introduction = self.get_text(soup.select('div.comm-survey-field > p')[0]).replace(' ', '')
        developer = self.get_text(soup.select('#more-brief-content > dl > dd')[0])
        property_manage = self.get_text(soup.select('#more-brief-content > dl > dd')[1])
        coordinate = soup.select('div.linkwraps > div > a')[2].get('href').split('&')
        coordinate = coordinate[1] + '\t' + coordinate[2]
        if soup.select('#imglist > li > img'):
            image = soup.select('#imglist > li > img')[0].get('data-src')
            self.pic_name = self.city + '-' + xiaoqu_name
            with open('%s/%s.jpg' % (self.pic_path, self.pic_name), 'wb') as f:
                f.write(requests.get(image).content)
        self.push_picture()
        if mouth_change_form:
            month_price_change = '与上月相比' + mouth_change_form + month_price_change
        else:
            month_price_change = '与上月相比持平'
        if year_change_form:
            year_price_change = '与去年相比' + year_change_form + year_price_change
        else:
            year_price_change = '与去年持平'
        sql = "INSERT INTO xiaoqu(%s) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" \
              % (
              field, xiaoqu_name, xiaoqu_area, month_price_change, year_price_change, new_price, xiaoqu_type, wuyefee,
              time_of_completion, green_rate, total_num, plot_ratio, brief_introduction, developer, property_manage,
              coordinate)
        self.cur.execute(sql)
        self.cur.execute('commit')


if __name__ == '__main__':
    res = Crawl()
    print(res.get_xiaoqu_info())
