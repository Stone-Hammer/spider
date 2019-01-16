#!/usr/bin/env python

import requests
from requests.exceptions import RequestException
import re
import time
import pymongo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from Pengpai.config import *
from multiprocessing import Pool
#from pathos.multiprocessing import ProcessingPool as Pool

myclient = pymongo.MongoClient(MONGO_URL, connect=False)
mydb = myclient[MONGO_DB]
#mycol = mydb[MONGO_COL]


def get_page_index(page,nodeids):
    data = {
        'nodeids': nodeids,
        'topCids': '',
        'pageidx': page,
        'isList': 'true',
        'lastTime': str(int(round(time.time() * 1000)))
    }
    url = 'https://www.thepaper.cn/load_index.jsp?'+ urlencode(data)
    try:
        response= requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None

def parse_page_index(html):
    pattern = re.compile('<a.*?id="clk(.*?)"', re.S)
    items = re.findall(pattern, html)
    return items

def get_page_detail(url):
    try:
        response= requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    if soup.select('.news_title'):
        title = soup.select('.news_title')[0].get_text()

        return {
            'keywords': soup.select('meta[name="Keywords"]')[0]['content'],
            'description': soup.select('meta[name="Description"]')[0]['content'],
            'title': title,
            'time': soup.select('.news_about > p')[1].get_text().strip('\n\t')[0:16],
            'content': soup.select('.news_txt')[0].get_text(),
            'zan': soup.select('.zan')[0].get_text().strip('\n '),
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
        for item in parse_page_index(html):
            url = 'https://www.thepaper.cn/newsDetail_forward_' + str(item)
            h = get_page_detail(url)
            if h:
                result = parse_page_detail(h, url)
                if result:
                    print(result)
                    #save_to_mongo(result, mycol)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main,PENGPAI_NEWS_TYPE_LIST)
