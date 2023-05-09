# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from datetime import datetime
import hashlib

from itemadapter import ItemAdapter
from furl import furl
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from scrapy_project.db import Session, Article


class PgPipeline:
    def open_spider(self, spider):
        self.session = Session()

    def close_spider(self, spider):
        self.session.commit()

    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        
        item_dict['timestamp'] = datetime.now()
        
        url_parsed = furl(item_dict['url'])
        item_dict['id'] = int(hashlib.sha256(str(url_parsed.path).encode('utf-8')).hexdigest(), 16) % 10**8
        if len(url_parsed.path.segments) > 1:
            url_parsed.path.segments.pop()
            item_dict['parent_id'] = int(hashlib.sha256(str(url_parsed.path).encode('utf-8')).hexdigest(), 16) % 10**8
        
        art = Article(**item_dict)
        self.session.merge(art)
        return item
