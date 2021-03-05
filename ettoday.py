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
from selenium.webdriver.chrome.options import Options

def remove_not_Ch_Eng(cont):
    # chinese unicode range: [0x4E00,0x9FA5]
    rule = u'[\u4E00-\u9FA5\w]'
    pChEng = re.compile(rule).findall(cont)
    ChEngText = "".join(pChEng)
    cont = ChEngText
    return cont

def fetch_title(driver, base, topic_url, pages):
    title_list = []
    title_url = []
    url = base + topic_url
    driver.get(url)
    for p in range(pages):
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')

    contents = BeautifulSoup(driver.page_source, 'html.parser')
    contents = contents.find('div', class_='part_pictxt_3 lazyload')
    news_li = contents.find_all('div', class_='piece clearfix')
    for news in news_li:
        u = news.select_one('a').get('href')
        t = news.find('h3').select_one('a').getText()
        title_url.append(base+u)
        title_list.append(t)
        #print(base+u)
        #print(t)
    return title_list, title_url

def fetch_article(driver, url):
    driver.get(url)
    contents = BeautifulSoup(driver.page_source, 'html.parser')
    contents = contents.find('div', class_='story', itemprop='articleBody')
    contents = contents.getText()
    return contents

if __name__ == '__main__': 
    option = Options()
    option.add_argument('--headless')
    option.add_argument('--disable-gpu')
    option.add_argument('--disable-notifications')
    option.add_argument("--log-level=3")
    option.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome('./chromedriver.exe', chrome_options=option)

    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    config = config['ETTODAY']
    bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:50}{r_bar}'

    pages = 200
    topic_url_list = []
    topic_name_list = []
    title_list = []
    title_url = []
    save_path_list = []
    article_list = []

    for topic in config:
        topic_name_list.append(topic)
        topic_url_list.append(config[topic])
    print('fetching news title...')
    for t in tqdm(range(len(topic_url_list)-1), bar_format=bar_format):
        l, u = fetch_title(driver, topic_url_list[0], topic_url_list[t+1], pages)
        title_list.append(l)
        title_url.append(u)

    for t in range(len(topic_name_list)-1):
        for i in range(len(title_list[t])):
            title = title_list[t][i]
            #print(title)
            title = remove_not_Ch_Eng(title)
            save_path = './/ETtoday//'+topic_name_list[t+1]+'//'+title+'.txt'
            url = title_url[t][i]
            save_path_list.append([save_path, url])
    #print(save_path_list)
    print('fetching news articles...')

    for n in tqdm(range(len(save_path_list)), bar_format=bar_format):
        a = fetch_article(driver, save_path_list[n][1])
        #print(a)
        save_path_list[n][1] = a
    
    print('output to <Headline>.txt...')
    for t in tqdm(range(len(save_path_list)), bar_format=bar_format):
        os.makedirs(os.path.dirname(save_path_list[t][0]), exist_ok=True)
        with open(save_path_list[t][0], 'w', encoding='utf-8') as writer:
            writer.write(save_path_list[t][1])
    driver.quit()
    print('done')