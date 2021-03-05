import configparser
import requests
import configparser
import os
import time
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
import multiprocessing
from multiprocessing import Pool


def remove_not_Ch_Eng(cont):
    # chinese unicode range: [0x4E00,0x9FA5]
    rule = u'[\u4E00-\u9FA5\w]'
    pChEng = re.compile(rule).findall(cont)
    ChEngText = "".join(pChEng)
    cont = ChEngText
    return cont


def fetch_title_url(base, topic_url, pages):
    t_url = []

    u = base + topic_url
    driver.get(u)
    for p in tqdm(range(pages), bar_format = '{desc:<5.5}{percentage:3.0f}%|{bar:50}{r_bar}'):
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    contents = BeautifulSoup(driver.page_source, 'html.parser')
    contents = contents.find('div', id='newslist-top')
    contents.find('div', class_='more').decompose()
    news_li = contents.find_all('a')
    for news in news_li:
        if 'https://news.cts.com' in news.get('href'):
            t_url.append(news.get('href'))
    return t_url


def fetch_article(inp):
    u, topic = inp.split("||")
    getSuccess = False
    while(not getSuccess):
        try:
            resp = requests.get(u)
            resp.encoding = 'utf-8'
            #driver.get(u)
            getSuccess = True
        except requests.exceptions.RequestException as e:
        #except (TimeoutException, WebDriverException) as ex:
            print('got exception at url: ' + u)
            print('try to reload')
            getSuccess = False
    contents = BeautifulSoup(resp.text, 'html.parser')
    #contents = BeautifulSoup(driver.page_source, 'html.parser')
    contents = contents.find('artical', class_='news-artical')
    headline = contents.find('div', class_='artical-titlebar')
    headline = headline.h1.getText()
    headline = remove_not_Ch_Eng(headline)
    #print(headline)
    contents = contents.find('div', class_='artical-content', itemprop='articleBody')
    contents = contents.getText()
    return [contents, headline, topic]


option = Options()
option.add_argument('--headless')
option.add_argument('--disable-gpu')
option.add_argument('--disable-notifications')
option.add_argument("--log-level=3")
option.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome('./chromedriver.exe', chrome_options=option)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    config = config['CTS']
    bar_format = '{desc:<5.5}{percentage:3.0f}%|{bar:50}{r_bar}'

    pages = 300
    topic_url_list = []
    topic_name_list = []
    title_url = []
    url_list = []
    article_list = []
    for topic in config:
        topic_name_list.append(topic)
        topic_url_list.append(config[topic])

    print('fetching news title...')
    for t in range(len(topic_url_list)-1):
        print('round '+str(t)+'/'+str(len(topic_url_list)-1))
        u = fetch_title_url(
            topic_url_list[0], topic_url_list[t+1], pages)
        title_url.append(u)

    for t in range(len(topic_name_list)-1):
        for i in range(len(title_url[t])):
            url_list.append(title_url[t][i]+'||'+topic_name_list[t+1])
    
    
    print('fetching news articles...')
    manager = multiprocessing.Manager()
    share_article_list = manager.list()
    share_path_list = manager.list()
    with Pool(processes=10) as p:
        with tqdm(total=len(url_list), bar_format=bar_format) as bar:
            for i, _ in enumerate(p.imap_unordered(fetch_article, url_list)):
                cont, head, topic = _
                share_article_list.append(cont)
                head = './/CTS//'+topic+'//'+head+'.txt'
                share_path_list.append(head)
                # print(head)
                bar.update()

    print('output to <Headline>.txt...')
    for t in tqdm(range(len(share_path_list)), bar_format=bar_format):
        os.makedirs(os.path.dirname(share_path_list[t]), exist_ok=True)
        with open(share_path_list[t], 'w', encoding='utf-8') as writer:
            writer.write(share_article_list[t])

    driver.quit()
    print('done')
    