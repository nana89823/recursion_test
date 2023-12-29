"""Recursion test."""
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import tldextract
import json
import logging

# 配置 logging，设置日志级别和输出格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_all_links(url):
    """Get_all_links."""
    global request_count  # 使用全局变量
    request_count += 1
    logging.info(f"Making request #{request_count} to {url}")
    flag = True
    while flag:
        try:
            response = requests.get(url)
            flag = False
        except ConnectionError as ce:
            logging.error(f"ConnectionError: {ce}")
            time.sleep(0.1)
        except HTTPError as he:
            logging.error(f"HTTPError: {he}")
            time.sleep(0.1)
        except Timeout as te:
            logging.error(f"Timeout: {te}")
            time.sleep(0.1)
        except RequestException as re:
            logging.error(f"RequestException: {re}")
            time.sleep(0.1)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            time.sleep(0.1)
    soup = BeautifulSoup(response.text, 'lxml')

    # 提取页面上的所有链接
    links = [a.get('href') for a in soup.find_all('a', href=True)]

    # 将相对链接转换为绝对链接
    links = [urljoin(url, link) for link in links]

    return links


def crawl_website(url, all_links=set(), visited_links=set(), start_time=None, max_duration=3600):
    """Crawl_website."""
    if url in visited_links:
        return

    if start_time is None:
        start_time = time.time()

    # 检查是否超过最大运行时间
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time > max_duration:
        logging.info(f"Reached maximum duration ({max_duration} seconds). Stopping.")
        return all_links

    logging.info(f"Crawling: {url}")

    # 获取当前页面的所有链接
    links = get_all_links(url)

    # 将当前页面的链接添加到总的链接集合
    all_links.update(links)

    # 添加当前页面到已访问的链接集合
    visited_links.add(url)

    # 递归爬取每个链接
    for link in links:
        # 解析链接，仅爬取同一域的链接
        parsed_url = urlparse(link)
        if parsed_url.netloc == urlparse(url).netloc:
            crawl_website(link, all_links, visited_links, start_time, max_duration)


if __name__ == "__main__":
    urls = ["https://animal-friendly.co/", "https://www.don1don.com/", "https://news.pts.org.tw/"]
    for start_url in urls:
        filename = tldextract.extract(start_url).domain
        # 记录请求次数的全局变量
        request_count = 0
        all_links_set = set()
        all_links = crawl_website(start_url, all_links_set)
        with open(f'{filename}.txt', 'w') as file:
            urls_list = list(all_links)
            json.dump(urls_list, file)
