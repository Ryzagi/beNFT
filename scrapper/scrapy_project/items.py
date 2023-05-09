# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from datetime import datetime
from w3lib.html import remove_tags

from scrapy import Item, Field
from itemloaders.processors import TakeFirst, MapCompose, Join
from scrapy.loader import ItemLoader


class Article(Item):
    # define the fields for your item here like:
    source = Field()
    url = Field()
    title = Field()
    text = Field()

class ArticleLoader(ItemLoader):
    default_output_processor = TakeFirst()

    title_in = MapCompose(remove_tags, str.strip)
    title_out = Join()

    text_in = MapCompose(remove_tags, str.strip)
    text_out = Join('\n\n')
