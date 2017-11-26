import requests
from bs4 import BeautifulSoup
from alphabet_detector import AlphabetDetector #pip install alphabet-detector
import os
import time

for i in range(2017,2018):
    print("Year{0}".format(i))
    r = requests.get('http://www.dialog-21.ru/digest/{0}/articles'.format(i))
    soup = BeautifulSoup(r.text, "lxml")
    ad = AlphabetDetector()
    os.mkdir("dialogue_articles{0}".format(i))
    os.mkdir("meta_dialogue{0}".format(i))
    j=0
    for articles_ in soup:
        articles = soup.find_all(class_="article-link")
        for article in articles:
            title = article.contents[3].a
            tt = title.get_text()
            if ad.only_alphabet_chars(tt, "CYRILLIC"):
                meta = []
                url = "http://www.dialog-21.ru"+title["href"]
                pdf = requests.get(url)
                j+=1
                print("Writing article{0}...".format(j))
                with open('dialogue_articles{0}\dialogue{1}-{2}.pdf'.format(i,i,j), 'wb') as fout:
                    fout.write(pdf.content)
                print("Making metadata...")
                meta.append(url)
                meta.append(tt)
                meta.append(article.div.get_text())
                meta.append(str(i))
                meta.append("Лингвистика")
                with open('meta_dialogue{0}\meta_dialogue{1}-{2}.txt'.format(i,i,j), 'w', encoding='utf-8') as f:
                    for element in meta:
                        f.writelines(element + '\r\n')
                time.sleep(0.5)



