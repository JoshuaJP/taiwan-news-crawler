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

def fetch_title_nextPage(driver, base, topic_url, pages, btn_id):
    title_list = []
    title_url = []

    url = base + topic_url
    driver.get(url)
    for p in range(pages):
        try:
            element_present = EC.presence_of_element_located((By.ID, btn_id))
            WebDriverWait(driver, 60).until(element_present)
        except TimeoutException:
            print('Timed out waiting for button to load')
        element = driver.find_element_by_id(btn_id)
        driver.execute_script("arguments[0].click();", element)
    contents = BeautifulSoup(driver.page_source, 'html.parser')
    news_li = contents.find('div', class_='scrollable')
    news_li = news_li.find_all('li')
    for news in news_li:
        if 'www.cna.com.tw' in news.select_one('a').get('href'):
            title_list.append(news.getText())
            title_url.append(news.select_one('a').get('href'))
    return title_list, title_url

def fetch_article(driver, url):
    driver.get(url)
    contents = BeautifulSoup(driver.page_source, 'html.parser')
    contents = contents.select_one('.paragraph').getText()
    return contents

option = Options()
option.add_argument('--headless')
option.add_argument('--disable-gpu')
option.add_argument('--disable-notifications')
option.add_argument("--log-level=3")
option.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome('./chromedriver.exe', chrome_options=option)

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
config = config['CNA']
bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:50}{r_bar}'

#100
pages = 100
btn_id = 'SiteContent_uiViewMoreBtn'
topic_name_list = []
topic_url_list = []
title_list = []
title_url = []
save_path_list = []
for topic in config:
    topic_name_list.append(topic)
    topic_url_list.append(config[topic])
print('fetching news title...')
for t in tqdm(range(len(topic_url_list)-1), bar_format=bar_format):
    l, u = fetch_title_nextPage(driver, topic_url_list[0], topic_url_list[t+1], pages, btn_id)
    title_list.append(l)
    title_url.append(u)

for t in range(len(topic_name_list)-1):
    for i in range(len(title_list[t])):
        title = title_list[t][i]
        title = remove_not_Ch_Eng(title)
        save_path = './/CNA//'+topic_name_list[t+1]+'//'+title+'.txt'
        url = title_url[t][i]
        save_path_list.append([save_path, url])

print('fetching news articles...')
for t in tqdm(range(len(save_path_list)), bar_format=bar_format):
    a = fetch_article(driver, save_path_list[t][1])
    save_path_list[t][1] = a

print('output to <Headline>.txt...')
for t in tqdm(range(len(save_path_list)), bar_format=bar_format):
    os.makedirs(os.path.dirname(save_path_list[t][0]), exist_ok=True)
    with open(save_path_list[t][0], 'w', encoding='utf-8') as writer:
        writer.write(save_path_list[t][1])
driver.quit()
print('done')