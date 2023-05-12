# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field, Selector
from itemloaders.processors import TakeFirst, MapCompose, Join
from scrapy.loader import ItemLoader

def transform_links(html: str) -> str:
    for link_tag in Selector(text=html).xpath('//a[.//text()]').getall():
        link_selector = Selector(text=link_tag)
        url = link_selector.xpath('//@href').get()
        anchor_parts = link_selector.xpath('//text()').getall()
        anchor_parts = [i.strip() for i in anchor_parts]
        anchor = ' '.join(anchor_parts)

        if anchor == url:
            link_text_version = url
        else:
            link_text_version = f'{anchor} ({url})'

        html = html.replace(link_tag, link_text_version)

    return html

def remove_tags(html: str) -> str:
    texts = Selector(text=html).xpath('//text()').re('.*\w+.*')
    texts = [i.strip() for i in texts]

    return ' '.join(texts)

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

    text_in = MapCompose(transform_links, remove_tags)
    text_out = Join('\n\n')
