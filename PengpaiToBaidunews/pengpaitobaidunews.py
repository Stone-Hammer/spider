#!/usr/bin/env python

import requests
from requests.exceptions import RequestException
import re
import time
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from multiprocessing import Pool
from PengpaiToBaidunews.entity import *
from PengpaiToBaidunews.config import *
import urllib
import random
from sqlalchemy import exists

# import pymongo
# myclient = pymongo.MongoClient(MONGO_URL, connect=False)
# mydb = myclient[MONGO_DB]
#mycol = mydb[MONGO_COL]
# import pymysql
# 打开数据库连接
# db = pymysql.connect("localhost", "root", "qazsedcft", "test_hammer")
# 使用 cursor() 方法创建一个游标对象 cursor
# cursor = db.cursor()

# 请求澎湃新闻目录页
def get_page_index(page,type):
    data = {
        'nodeids': type,
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

# 解析澎湃新闻目录页，返回新闻的url
def parse_page_index(html):
    pattern = re.compile('<a.*?id="clk(.*?)"', re.S)
    items = re.findall(pattern, html)
    return items

# 请求澎湃新闻详情页
def get_page_detail(url):
    try:
        response= requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错')
        return None

# 解析澎湃新闻详情页，返回需要的新闻内容数据
def parse_page_detail(html):
    soup = BeautifulSoup(html, 'lxml')
    if soup.select('.news_title'):
        title = soup.select('.news_title')[0].get_text()
        # keywords = soup.select('meta[name="Keywords"]')[0]['content']

        return (
             soup.select('meta[name="Keywords"]')[0]['content'],# keywords
             soup.select('meta[name="Description"]')[0]['content'],# description
             title,
             soup.select('.news_about > p')[1].get_text().strip('\n\t')[0:16] # lives_time
        )

        # return {
        #     'keywords': soup.select('meta[name="Keywords"]')[0]['content'],
        #     'description': soup.select('meta[name="Description"]')[0]['content'],
        #     'title': title,
        #     'time': soup.select('.news_about > p')[1].get_text().strip('\n\t')[0:16],
        #     # 'content': soup.select('.news_txt')[0].get_text(),
        #     # 'zan': soup.select('.zan')[0].get_text().strip('\n '),
        #     # 'url': url
        # }
    return None

# 为读取到的所有新闻数据创建一个词条lives_news以及新闻详情表lives_detail。
def save_to_mysql(lives_news, lives_time, url, details):
    # 插入一条lives_news数据
    # 创建session对象:
    session = DBSession()
    # 添加到session:
    # 新建澎湃新闻的lives_details
    source_website = session.query(SourceWebsite).filter(SourceWebsite.website_name == '澎湃新闻').one()
    lives_detail = LivesDetail(url, lives_news.lives_title, lives_news.introduction, lives_time)
    lives_detail.website_id = source_website.website_id;
    lives_news.details.append(lives_detail)

    count = 1;
    for detail in details:
        # sw = session.query(SourceWebsite).filter(SourceWebsite.website_name
        #                                                      == detail.source_website.website_name).one()
        # sw = session.query(SourceWebsite).from_statement("SELECT * FROM source_website where website_name=:website_name").\
        #     params(website_name=detail.source_website.website_name).one()

        # website_exists = session.query(
        #     exists().where(SourceWebsite.website_name == detail.website_name)
        # ).scalar()
        # if not website_exists:
        #     session.add(SourceWebsite(detail.website_name))
        #     session.commit()
        #     session.flush()
        sw = session.query(SourceWebsite).filter(SourceWebsite.website_name
                                                             == detail.website_name).first()
        if not sw:
            temp = SourceWebsite(detail.website_name)
            session.add(temp)
            # session.flush()
            # print("temp:",temp.website_id)
            session.commit()
            detail.website_id = temp.website_id
        else:
            detail.website_id = sw.website_id
        lives_news.details.append(detail)
        count += 1

    lives_news.lives_count = count

    session.add(lives_news)
    # session.add(lives_detail)
    # 提交即保存到数据库:
    session.commit()
    print('存储到lives_news成功：',lives_news.lives_title)
    # 关闭session:
    session.close()
    # sql = "INSERT INTO lives_news(lives_title, introduction, lives_count, manager_id) \
    #        VALUES ('%s', '%s',  %s,  %s)" % (title, description, 0, 1)
    # try:
    #     # 执行sql语句
    #     cursor.execute(sql)
    #     db.commit()
    # except:
    #     # 发生错误时回滚
    #     db.rollback()

# 请求百度新闻搜索页
def get_page_index_baidu(word, usr_ag):
    data = {
        'word': word,
        'tn': 'news',
        'from': 'news',
        'cl': '3',
        'rn': '20',
        'ct': '1',
    }
    url = 'http://news.baidu.com/ns?'+ urlencode(data)
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

# 解析百度新闻搜索页，返回需要的新闻内容数据
def parse_page_index_baidu(html, lives_news):
    soup = BeautifulSoup(html, 'lxml')
    details = []
    if soup.select('.c-author'):
        for i in range(0, len(soup.select('.c-author'))-10):
            if soup.select('.c-title'):
                # soup.select('.c-title')[i].em.extract()
                title = soup.select('.c-title > a')[i].get_text().replace('<em>', '').replace('</em>', '').replace(' ',
                                                                                                                   '').replace(
                    '\n', '')
                url = soup.select('.c-title > a')[i]['href']
                if soup.select('.c-author')[i] and soup.select('.c-author')[i].get_text():
                    temp = soup.select('.c-author')[i].get_text().split('\t', 1)
                    if len(temp) < 2:
                        break
                    website_name = temp[0].replace('\n', '').replace(' ', '').replace('\t', '').replace('\xa0', '')
                    detail_time = temp[1].replace('\n', '').replace(' ', '').replace('\t', '')
                    if "前" in detail_time:
                        continue
                    detail_time = detail_time.replace('年', '-').replace('月', '-').replace('日', ' ')
                    detail_text = soup.select('.c-summary')[i].get_text().replace('\n', '').replace(' ', '').replace('\t', '')\
                        .replace('<em>', '').replace('</em>', '').replace('百度快照', '').replace('>', '').replace('-', '')

                    lives_detail = LivesDetail(url, title, detail_text, detail_time)
                    # source_website = SourceWebsite(website_name)
                    # lives_detail.source_website = source_website
                    lives_detail.website_name = website_name
                    lives_detail.lives_news = lives_news
                    details.append(lives_detail)

    # pattern = re.compile('"url":"(.*?)"', re.S)
    # items = re.findall(pattern, str(html))
    return details

def main(type):
    groups = [x for x in range(GROUP_START, GROUP_END+1)]
    for page in groups:
        html = get_page_index(page,type)
        # mycol = mydb[MONGO_COL_HEAD + str(type)]
        for item in parse_page_index(html):
            url = 'https://www.thepaper.cn/newsDetail_forward_' + str(item)
            h = get_page_detail(url)
            if h:
                (keywords, description, title ,lives_time) = parse_page_detail(h)
                if keywords:
                    print(keywords)
                    usr_ag = random.randint(0, len(USR_AG_LIST)-1)
                    baidu_html = get_page_index_baidu(keywords, usr_ag)
                    lives_news = LivesNews(title, description, 1)
                    details = parse_page_index_baidu(baidu_html, lives_news)
                    # print(details)
                    save_to_mysql(lives_news, lives_time, url, details)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main,PENGPAI_NEWS_TYPE_LIST)
