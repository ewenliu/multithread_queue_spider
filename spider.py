# -*- coding: utf-8 -*-#
import requests
# 下载图片文件等
import urllib.error
import urllib.request
# xml解析
from bs4 import BeautifulSoup
import os

from threading import Thread, current_thread
import queue


# 基础url
GENERAL_URL = 'https://www.doutula.com/photo/list/?page='
url_q = queue.Queue(6)


def get_all_page_url(page_amount=2):
    """
        page_amount: 总共要获取多少页
    """
    all_page_url = []
    for x in range(1, page_amount+1):
        url = GENERAL_URL + str(x)
        all_page_url.append(url)
    return all_page_url


def download_image(img_url):
    """
        url: 图片url连接
    """
    # 加入请求头避免403错误
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                          '55.0.2883.75 Safari/537.36')]
    urllib.request.install_opener(opener)
    # 获取图片名字
    split_list = img_url.split('/')
    filename = split_list.pop()
    path = os.getcwd() + os.sep + 'images' + os.sep + filename
    try:
        urllib.request.urlretrieve(img_url, filename=path)
    except urllib.error.HTTPError:
        print('下载失败，检查请求头')


class Producer(Thread):
    def __init__(self, page_url_l):
        super().__init__()
        self.page_url_l = page_url_l

    def run(self):
        """
            url: 将要爬取的url
        """
        while len(self.page_url_l) != 0:
            if not url_q.full():
                page_url = self.page_url_l.pop()
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                                  '76.0.3809.87 Safari/537.36'}
                result = requests.get(page_url, headers=headers)
                content = result.content
                # 解析该页面
                soup = BeautifulSoup(content, 'lxml')
                # 找到class为'img-responsive lazy image_dta'的所有img对象
                img_list = soup.find_all('img', attrs={'class': 'img-responsive lazy image_dta'})
                url_q.put(img_list)
            # 队列满了，继续等待队列被消费直到有空位
            else:
                continue
        else:
            print('生产者%s: Url生产完毕 线程回收' % current_thread().getName())


class Consumer(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            img_list = url_q.get()
            # 判断从队列里拿出来的是不是None，如果是，则说明生产者生产完毕，消费者也不用消费了，线程回收
            if img_list is None:
                print('消费者%s: 队列为空，线程回收' % (current_thread().getName()))
                break
            for img in img_list:
                url = img["data-original"]
                download_image(url)
            print('消费者%s: 本次消费完毕' % current_thread().getName())


def main():
    page_url_l = get_all_page_url(10)
    p_l = []
    c_l = []


    # 两个线程用来生产url，放入队列
    for i in range(2):
        p = Producer(page_url_l=page_url_l)
        p_l.append(p)

    # 四个线程从队列中取出url，下载图片
    for i in range(4):
        c = Consumer()
        c_l.append(c)

    for p in p_l:
        p.start()

    for c in c_l:
        c.start()

    for p in p_l:
        p.join()

    # 等待生产者全部生产完，放入与消费者数量等同的None，防止消费者线程阻塞，回收消费者线程
    for i in range(len(c_l)):
        url_q.put(None)


if __name__ == '__main__':
    main()
