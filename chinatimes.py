import configparser
import requests
import configparser
import os
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def fetch_title_url(driver, base, topic_url, pages, tag, cls):
    title_list = []
    title_url = []

    url = base + topic_url
    for p in range(pages):
        page_url = url.replace('${page}', str(p+1))
        driver.get(page_url)
        contents = BeautifulSoup(driver.page_source, 'html.parser')
        news_li = contents.find_all(tag, cls)

        for news in news_li:
            if 'https' not in news.select_one('a').get('href'):
                title_list.append(news.getText())
                title_url.append(base+news.select_one('a').get('href'))

    return title_list, title_url

def fetch_article(driver, urls):
    ret_list = []
    for u in urls:
        driver.get(u)
        contents = BeautifulSoup(driver.page_source, 'html.parser')
        arti = contents.find('div', class_='article-body').getText()
        #arti = contents.select_one(tag).getText()
        #print(arti)
        ret_list.append(arti)
    return ret_list

option = Options()
option.add_argument('--headless')
option.add_argument('--disable-gpu')
option.add_argument('--disable-notifications')
option.add_argument("--log-level=3")
driver = webdriver.Chrome('./chromedriver.exe', chrome_options=option)

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
config = config['CHINATIMES']


# max pages 10
pages = 10
topic_url_list = []
topic_name_list = []
title_list = []
title_url = []
article_list = []
for topic in config:
    topic_name_list.append(topic)
    topic_url_list.append(config[topic])


print('fetching news title...')
for t in tqdm(range(len(topic_url_list)-1)):
    l, u = fetch_title_url(driver, topic_url_list[0], topic_url_list[t+1], pages, 'h3', 'title')
    title_list.append(l)
    title_url.append(u)

#print(title_url)
print('fetching news articles...')
for t in tqdm(range(len(title_url))):
    a = fetch_article(driver, title_url[t])
    article_list.append(a)

print('output to <Headline>.txt...')
for t in tqdm(range(len(topic_name_list)-1)):
    for i in range(len(title_list[t])):
        filename = './CHINATIMES/'+topic_name_list[t+1]+'/'+title_list[t][i].replace('/', '')+'.txt'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding="utf-8") as writer:
            writer.write(article_list[t][i])