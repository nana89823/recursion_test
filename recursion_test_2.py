import threading
import queue
import requests
import time
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import tldextract
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_all_links(url):
    """Get_all_links."""
    global request_count
    request_count += 1
    logging.info(f"Crawling: #{request_count} : {url}")
    fail_count = 0
    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = bs(response.text, "lxml")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            links = [urljoin(url, link) for link in links if urlparse(link).netloc == urlparse(url).netloc]
            return links
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            fail_count += 1
            if fail_count > 3:
                logging.error(f"Failed to fetch: {url}")
                return []
            time.sleep(1)


def crawl():
    """crawl."""
    while not url_queue.empty() and not stop_flag.is_set():
        current_url = url_queue.get()
        if current_url in visited_links:
            continue
        links = get_all_links(current_url)
        with thread_lock:
            all_links_set.update(links)
            visited_links.add(current_url)
        for link in links:
            if link not in visited_links:
                url_queue.put(link)
        url_queue.task_done()


if __name__ == "__main__":
    start_urls = [
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
    thread_count = 50  # 使用的線程數量
    thread_lock = threading.Lock()  # 用於修改共享數據的鎖

    for start_url in start_urls:
        start_time = time.time()
        visited_links = set()
        all_links_set = set()
        request_count = 0
        max_duration = 3600
        filename = tldextract.extract(start_url).domain

        # 線程安全的隊列
        url_queue = queue.Queue()
        stop_flag = threading.Event()

        # 填充初始隊列
        url_queue.put(start_url)
        # stop_flag.clear()

        # 啟動線程
        threads = []
        for _ in range(thread_count):
            thread = threading.Thread(target=crawl)
            thread.start()
            threads.append(thread)

        # 等待線程完成或直到達到最大執行時間
        while time.time() - start_time < max_duration:
            time.sleep(1)

        stop_flag.set()  # 設置停止標誌

        for t in threads:
            t.join(timeout=0)

        # 保存結果
        with open(f"{filename}.txt", "w") as file:
            json.dump(list(all_links_set), file)
