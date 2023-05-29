import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scrapy import Selector

#base_url = 'https://whitepaperv2.benft.solutions'
from config import base_url

delay = 1  # Delay in seconds between requests
visited_urls = set()  # Set to store visited URLs


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def transform_links(html: str) -> str:
    link_strings = ""
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

        link_strings += link_text_version

    return link_strings


async def get_hyperlinks(url: str):
    connector = aiohttp.TCPConnector(keepalive_timeout=120)
    async with aiohttp.ClientSession(connector=connector) as session:
        response_text = await fetch(session, url)
        return await transform_links(response_text)


async def crawl_website(url):
    visited_urls.add(url)  # Add the current URL to visited_urls
    connector = aiohttp.TCPConnector(keepalive_timeout=120)

    async with aiohttp.ClientSession(connector=connector) as session:
        response_text = await fetch(session, url)

        soup = BeautifulSoup(response_text, 'html.parser')
        links = soup.find_all('a', href=True)

        subdirectories = []

        for link in links:
            href = link['href']
            absolute_url = urljoin(url, href)
            if absolute_url.startswith(base_url) and absolute_url not in visited_urls:
                subdirectories.append(absolute_url)
                print(absolute_url)
                # await asyncio.sleep(delay)  # Adding a delay between requests
                subdirectories += await crawl_website(absolute_url)  # Accumulate subdirectories from recursive calls

        return subdirectories


async def scrapper(base_url):
    hyperlinks_with_text = await get_hyperlinks(base_url)
    loop = asyncio.get_event_loop()
    links = await crawl_website(base_url)  # Await the initial call to crawl_website
    return hyperlinks_with_text, links

if __name__ == '__main__':
    hyperlinks_with_text, links = asyncio.run(scrapper(base_url))
    print(hyperlinks_with_text, links)
    # loop = asyncio.get_event_loop()
    # result = loop.run_until_complete(crawl_website(base_url))
    # print(result)
    #print(txt_links)
