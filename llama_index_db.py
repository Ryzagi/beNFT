import asyncio
import re

from llama_index import GPTVectorStoreIndex, download_loader

from config import base_url
from scrap import scrapper

if __name__ == '__main__':

    from llama_index import TrafilaturaWebReader, SimpleWebPageReader

    # Create an instance of the TrafilaturaWebReader
    web_reader = TrafilaturaWebReader()

    hyperlinks_with_text, links = asyncio.run(scrapper(base_url))
    print(hyperlinks_with_text, links)
    documents = web_reader.load_data(links)
    texts = ""
    print(documents)
    for document in documents:
        texts += document.text
    texts += f"\n\n{hyperlinks_with_text}"
    print(texts)
