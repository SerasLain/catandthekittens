import requests
from bs4 import BeautifulSoup
import time
import os
"""Скачивает "Вопросы языкознания и пишет к ним метаданные"""
for i in range (2015,2016): 
    r = requests.get("http://issuesinlinguistics.ru/pubs/?year={0}".format(i))
    soup = BeautifulSoup(r.text, "lxml")
    titles_and_authors = soup.find_all(class_="post-item")
    os.mkdir("meta{0}".format(i))
    print("Making metadata...")
    for j,title in enumerate(titles_and_authors):
        meta = []
        a=title.h1.a
        meta.append(a["href"])#url
        meta.append(a.get_text().replace('\t',''))#название статьи
        meta.append(title.ul.li.a.get_text())#автор
        meta.append(str(i))#год
        meta.append("Лингвистика")#домен
        with open('meta{0}\meta_issuesinlinguistics{1}-{2}.txt'.format(i,i,j), 'w',encoding='utf-8') as f:
            for element in meta:
                f.writelines(element+'\r\n')
    readmores = soup.find_all(class_="readmore")
    readmores_list = []
    print("Crawling texts...")
    for readmore in readmores:
        readmores_list.append(requests.get(readmore["href"]))
        time.sleep(0.5)
    os.mkdir("articles{0}".format(i))
    for j, readmore in enumerate(readmores_list):
        download = BeautifulSoup(readmore.text, "lxml").find(class_="elastic-button download")
        pdf = requests.get(download["href"])
        print("Writing text{0}...".format(j))
        with open('articles{0}\issuesinlinguistics{1}-{2}.pdf'.format(i,i,j), 'wb') as f:
            f.write(pdf.content)
        time.sleep(0.5)
