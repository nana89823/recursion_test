"""Recursion test."""
import requests

# from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import tldextract
import json
import logging

# from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures

# 配置 logging，设置日志级别和输出格式
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_all_links(url):
    """Get_all_links."""
    global request_count  # 使用全局变量
    request_count += 1
    logging.info(f"Crawling: #{request_count} : {url}")
    flag = True
    fail_count = 0
    while flag:
        try:
            response = requests.get(url)
            flag = False
        # except ConnectionError as ce:
        #     logging.error(f"ConnectionError: {ce}")
        #     time.sleep(1)
        # except HTTPError as he:
        #     logging.error(f"HTTPError: {he}")
        #     time.sleep(1)
        # except Timeout as te:
        #     logging.error(f"Timeout: {te}")
        #     time.sleep(1)
        # except RequestException as re:
        #     logging.error(f"RequestException: {re}")
        #     time.sleep(1)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            fail_count += 1
            if fail_count >= 3:
                flag = False
                response = None
            time.sleep(1)
    if response:
        soup = BeautifulSoup(response.text, "lxml")

        # 提取页面上的所有链接
        links = [a.get("href") for a in soup.find_all("a", href=True)]

        # 将相对链接转换为绝对链接
        links = [urljoin(url, link) for link in links]
    else:
        return None
    return links


def crawl_website(
    url, all_links_set=set(), visited_links=set(), start_time=None, max_duration=3600
):
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
        return all_links_set

    # 获取当前页面的所有链接
    links = get_all_links(url)

    # 将当前页面的链接添加到总的链接集合
    all_links_set.update(links)

    # 添加当前页面到已访问的链接集合
    visited_links.add(url)

    # 創建 ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 使用 executor.submit 提交任务，得到 Future 对象列表
        futures = [
            executor.submit(
                crawl_website,
                link,
                all_links_set,
                visited_links,
                start_time,
                max_duration,
            )
            for link in links
            if urlparse(link).netloc == urlparse(url).netloc
        ]

        # 使用 concurrent.futures.wait 等待所有任务完成
        done, not_done = concurrent.futures.wait(
            futures, timeout=max_duration - elapsed_time
        )

        # 檢查已完成的任務
        for future in done:
            result = future.result()
            if result is not None:
                all_links_set.update(result)

    return all_links_set


# def crawl_website(
#     url, all_links_set=set(), visited_links=set(), start_time=None, max_duration=3600
# ):
#     """Crawl_website."""
#     if url in visited_links:
#         return

#     if start_time is None:
#         start_time = time.time()

#     # 检查是否超过最大运行时间
#     current_time = time.time()
#     elapsed_time = current_time - start_time
#     if elapsed_time > max_duration:
#         logging.info(f"Reached maximum duration ({max_duration} seconds). Stopping.")
#         return all_links_set

#     # 获取当前页面的所有链接
#     links = get_all_links(url)

#     # 将当前页面的链接添加到总的链接集合
#     all_links_set.update(links)

#     # 添加当前页面到已访问的链接集合
#     visited_links.add(url)

#     # 创建 ThreadPoolExecutor
#     with ThreadPoolExecutor() as executor:
#         # 使用 executor.submit 提交任务，得到 Future 对象列表
#         futures = [
#             executor.submit(
#                 crawl_website,
#                 link,
#                 all_links_set,
#                 visited_links,
#                 start_time,
#                 max_duration,
#             )
#             for link in links
#             if urlparse(link).netloc == urlparse(url).netloc
#         ]

#         # 使用 as_completed 函数等待任务完成，获取已完成的 Future 对象
#         for future in as_completed(futures):
#             result = future.result()
#             if result is not None:
#                 all_links_set.update(result)

#     return all_links_set


if __name__ == "__main__":
    urls = [
        "https://www.don1don.com/",
        "https://news.pts.org.tw/",
        "https://www.everydayobject.us/",
        "https://www.ettoday.net/dalemon",
        "https://news.pts.org.tw",
        "https://www.dramaqueen.com.tw/",
        "https://applianceinsight.com.tw/",
        "https://easylife.tw/",
        "https://e-creative.media/",
    ]
    for start_url in urls:
        filename = tldextract.extract(start_url).domain
        # 记录请求次数的全局变量
        request_count = 0
        all_links = crawl_website(start_url)
        with open(f"{filename}.txt", "w") as file:
            urls_list = list(all_links)
            json.dump(urls_list, file)
