import concurrent.futures
import asyncio
import aiohttp
import logging
import sys
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import time
import tldextract
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()
            return html
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


async def get_all_links(session, url, all_links_set):
    global request_count
    request_count += 1
    logging.info(f"Crawling: #{request_count} : {url}")

    html = await fetch_url(session, url)
    if html:
        soup = bs(html, "lxml")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        links = [urljoin(url, link) for link in links if urlparse(link).netloc == urlparse(url).netloc]
        all_links_set.update(links)


async def crawl_website(start_url, max_duration, all_links_set, visited_links):
    async with aiohttp.ClientSession() as session:
        await get_all_links(session, start_url, all_links_set)
        visited_links.add(start_url)
        if time.time() - start_time > max_duration:
            logging.info(f"Reached maximum duration ({max_duration} seconds). Stopping.")
            sys.exit()
            return

        # 從all_links_set取得Link再次執行crawl_website
        tasks = []
        for url in all_links_set:
            if url not in visited_links:
                task = crawl_website(url, max_duration, all_links_set, visited_links)
                tasks.append(task)

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    urls = [
        "https://news.pts.org.tw/",
        "https://www.don1don.com/",
    ]
    for start_url in urls:
        start_time = time.time()
        max_duration = 10
        request_count = 0
        all_links_set = set()
        visited_links = set()
        filename = tldextract.extract(start_url).domain
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.map(crawl_website(start_url, max_duration, all_links_set, visited_links))

        asyncio.run(crawl_website(start_url, max_duration, all_links_set, visited_links))

        with open(f"{filename}.txt", "w") as file:
            urls_list = list(all_links_set)
            json.dump(urls_list, file)
