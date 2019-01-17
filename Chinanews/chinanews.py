#!/usr/bin/env python

import requests
from requests.exceptions import RequestException
import re
import time
import pymongo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from Chinanews.config import *
from multiprocessing import Pool
import urllib
import random

myclient = pymongo.MongoClient(MONGO_URL, connect=False)
mydb = myclient[MONGO_DB]
#mycol = mydb[MONGO_COL]


def get_page_index(page, usr_ag):
    data = {
        'pager': page,
        'pagenum': '10',
        '_': str(int(round(time.time() * 1000))),
    }
    # url = 'http://channel.chinanews.com/cns/cjs/sh.shtml?'+ urlencode(data)
    url = 'http://channel.chinanews.com/cns/cjs/cul.shtml?'+ urlencode(data)
    try:
        #请求中加入UserAgent的信息
        headers = {'User-Agent': usr_ag}
        req = urllib.request.Request(url=url, headers=headers)
        response = urllib.request.urlopen(req)
        html = response.read()
        return html
    except RequestException:
        print('请求索引页出错')
        return None

def parse_page_index(html):
    pattern = re.compile('"url":"(.*?)"', re.S)
    items = re.findall(pattern, str(html))
    return items

def get_page_detail(url, usr_ag):
    try:
        headers = {'User-Agent': usr_ag}
        req = urllib.request.Request(url=url, headers=headers)
        response = urllib.request.urlopen(req)
        html = response.read()
        return html
    except RequestException:
        print('请求详情页出错')
        return None

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    #标题列表判断
    if soup.select('input[name="newstitle"]'):
        title = soup.select('input[name="newstitle"]')[0]['value']
        # [s.extract() for s in soup('script')]
        #正文列表判断
        if soup.select('.left_zw'):
            #去除正文中的script标签
            if soup.select('.left_zw')[0].script:
                soup.select('.left_zw')[0].script.extract()
            return {
                'keywords': soup.select('meta[name="keywords"]')[0]['content'],
                'description': soup.select('meta[name="description"]')[0]['content'],
                'title': title,
                'time': soup.select('span[id="pubtime_baidu"]')[0].get_text(),
                'content': soup.select('.left_zw')[0].get_text().replace('\u3000','').replace('\n','').replace('\r',''),
                'url': url
            }
    return None

def save_to_mongo(result,mycol):
    if mycol.insert_one(result):
        print('存储到',mycol.name,'成功：',result)
        return True
    return False

def main(page):
    #随机选择一个usr_ag访问网址，避免反爬
    usr_ag = random.randint(0, len(USR_AG_LIST)-1)
    html = get_page_index(page, usr_ag)
    parse_page_index(html)
    mycol = mydb[MONGO_COL]
    for url in parse_page_index(html):
        usr_ag = random.randint(0, len(USR_AG_LIST)-1)
        h = get_page_detail(url,usr_ag)
        if h:
            result = parse_page_detail(h, url)
            if result:
                #print(result)
                save_to_mongo(result, mycol)

if __name__ == '__main__':
    #创建线程池，main函数参数为页码
    groups = [x for x in range(GROUP_START, GROUP_END+1)]
    pool = Pool()
    pool.map(main,groups)

