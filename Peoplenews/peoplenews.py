#!/usr/bin/env python

import requests
from requests.exceptions import RequestException
import re
import pymongo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from Peoplenews.config import *
from multiprocessing import Pool

myclient = pymongo.MongoClient(MONGO_URL, connect=False)
mydb = myclient[MONGO_DB]
#mycol = mydb[MONGO_COL]

def get_page_index(page):
    url = 'http://society.people.com.cn/index'+ str(page) + '.html'
    try:
        response= requests.get(url)
        if response.status_code == 200:
            response.encoding = 'gb2312'
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None

def parse_page_index(html):
    #pattern = re.compile('<strong><a href=\'(.*?)\'', re.S)
    pattern = re.compile('<h5><a href=\'(.*?)\'', re.S)
    items = re.findall(pattern, str(html))
    return items

def get_page_detail(url):
    try:
        response= requests.get(url)
        if response.status_code == 200:
            response.encoding = 'gb2312'
            return response.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    if soup.select('.text_title > h1'):
        title = soup.select('.text_title > h1')[0].get_text()
        t = soup.select('.box01')[0].get_text().strip('\n')[0:16]
        time = t[0:4]+"-"+t[5:7]+"-"+t[8:10]+" "+t[11:16]
        return {
            'keywords': soup.select('meta[name="keywords"]')[0]['content'],
            'description': soup.select('meta[name="description"]')[0]['content'].strip('\u3000'),
            'title': title,
            'time': time,
            'content': soup.select('.box_con')[0].get_text().replace('\n','').replace('\t','').replace('\u3000',''),
            'url': url
        }
    return None

def save_to_mongo(result,mycol):
    if mycol.insert_one(result):
        print('存储到',mycol.name,'成功：',result)
        return True
    return False

def main(page):
    html = get_page_index(page)
    parse_page_index(html)
    mycol = mydb[MONGO_COL_HEAD]
    for item in parse_page_index(html):
        if str(item):
            url = 'http://society.people.com.cn' + str(item)
            h = get_page_detail(url)
            if h:
                result = parse_page_detail(h, url)
                if result:
                    save_to_mongo(result, mycol)

if __name__ == '__main__':
    groups = [x for x in range(GROUP_START, GROUP_END+1)]
    pool = Pool()
    pool.map(main, groups)
