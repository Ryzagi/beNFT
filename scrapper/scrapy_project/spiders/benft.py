from scrapy import Spider

from scrapy_project.items import Article, ArticleLoader

class Benft(Spider):
    name = 'benft'

    allowed_domains = ['whitepaperv2.benft.solutions']

    start_urls = ['https://whitepaperv2.benft.solutions']

    def parse(self, response, **kwargs):
        """This function parses a sample response. Some contracts are mingled
        with this docstring.

        @url https://whitepaperv2.benft.solutions/benft
        @returns items 1 1
        @returns requests 10 
        @scrapes source url title text
        """
        l = ArticleLoader(item=Article(), response=response)

        l.add_value('source', 'whitepaperv2.benft.solutions')
        l.add_value('url', response.url)
        l.add_xpath('title', '//h1')
        l.add_xpath('text', '//div[@data-block-content]')
        # rel_url = response.url.split(self.allowed_domains[0], 1)[1]
        # l.add_xpath('parent', f'//a[@href="{rel_url}"]//ancestor::div/a[not(@href="{rel_url}")]/@href')
        yield l.load_item()

        yield from response.follow_all(
            response.xpath('//nav//a/@href').getall(),
            self.parse,
        )


