# 导入:
from sqlalchemy import create_engine, Column, String, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# 创建对象的基类:
Base = declarative_base()
# 初始化数据库连接:
engine = create_engine('mysql+pymysql://root:qazsedcft@localhost:3306/test_hammer')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

# 定义User对象:
class LivesNews(Base):
    def __init__(self, lives_title, introduction, manager_id):
        # self.lives_id = 0
        self.lives_title = lives_title
        self.introduction = introduction
        self.manager_id = manager_id
        self.lives_count = 1
        # self.lives_time = lives_time

    # 表的名字:
    __tablename__ = 'lives_news'

    # 表的结构:
    lives_id = Column(Integer, primary_key=True, autoincrement=True)
    lives_title = Column(String(45))
    introduction = Column(String(500))
    manager_id = Column(Integer)
    lives_count = Column(Integer)
    lives_time = Column(TIMESTAMP)

    details = relationship('LivesDetail', back_populates="lives_news")

class LivesDetail(Base):
    def __init__(self, url, title, detail_text, time):
        # self.lives_id = lives_id;
        self.url = url
        self.title = title
        self.detail_text = detail_text
        self.time = time
        self.words_count = 0

    __tablename__ = 'lives_detail'

    detail_id = Column(Integer, primary_key=True, autoincrement=True)
    lives_id = Column(Integer, ForeignKey('lives_news.lives_id'))
    website_id = Column(Integer, ForeignKey('source_website.website_id'))
    website_name = ''

    lives_news = relationship("LivesNews", back_populates="details")
    # source_website = relationship("SourceWebsite", back_populates = "details")

    url = Column(String(255))
    title = Column(String(45))
    detail_text = Column(String(255))
    words_count = Column(Integer)
    time = Column(TIMESTAMP)

class SourceWebsite(Base):
    def __init__(self, website_name):
        self.website_name = website_name

    __tablename__ = 'source_website'

    website_id = Column(Integer, primary_key=True, autoincrement=True)
    website_name = Column(String(45))

    # details = relationship('LivesDetail', back_populates="source_website")
