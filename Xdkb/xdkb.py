#!/usr/bin/env python

import requests
from requests.exceptions import RequestException
import re
import time
import pymongo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from Xdkb.config import *
from multiprocessing import Pool

myclient = pymongo.MongoClient(MONGO_URL, connect=False)
mydb = myclient[MONGO_DB]
#mycol = mydb[MONGO_COL]


def get_page_index(page,type):
    url = 'http://news.xdkb.net/node_'+ str(type) + '.htm'
    try:
        response= requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None

def parse_page_index(html):
    soup = BeautifulSoup(html, 'lxml')
    items=[]
    for u in soup.select('.feeds-item-pic'):
        item = u.a['href']
        if re.match('\d*?-\d\d',item):
            items.append('http://news.xdkb.net/'+item)
    return items

def get_page_detail(url):
    try:
        response= requests.get(url)
        if response.status_code == 200:
            response.encoding = 'UTF-8'
            return response.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    if soup.select('.con-news-title'):
        title = soup.select('.con-news-title')[0].get_text().strip('\r\n\t '),
        return {
            'keywords': soup.select('meta[name="keywords"]')[0]['content'],
            'description': soup.select('meta[name="description"]')[0]['content'],
            'title': title,
            'time': soup.select('.con-time')[0].get_text(),
            'content': soup.select('.con-news-art')[0].get_text(),
            'url': url
        }
    return None

def save_to_mongo(result,mycol):
    if mycol.insert_one(result):
        print('存储到',mycol.name,'成功：',result)
        return True
    return False

def main(type):
    groups = [x for x in range(GROUP_START, GROUP_END+1)]
    for page in groups:
        html = get_page_index(page,type)
        mycol = mydb[MONGO_COL_HEAD + str(type)]
        for url in parse_page_index(html):
            h = get_page_detail(url)
            if h:
                result = parse_page_detail(h, url)
                if result:
                    #print(result)
                    save_to_mongo(result, mycol)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main,XDKB_NEWS_TYPE_LIST)
