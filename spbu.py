import requests
from bs4 import BeautifulSoup
import time
import os
import re
for i in range(16,18):
    #Для скачивания каждого выпуска ссылка меняется руками (допустим, все места с s14v4 заменятся на s14v1)
    #Папки создаются только один раз под каждый домен, поэтому здесь они закомментированы
    #os.mkdir('spbu_law_articles_20{}'.format(i))
    #os.mkdir('spbu_law_articles_20{}_meta'.format(i))
    year = str(i)
    r = requests.get('http://vestnik.spbu.ru/html{}/s14/s14v4/s14v4.html'.format(year, str(v)))
    r.encoding='utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    p = re.compile('[а-яА-ЯёЁ]')
    content = soup.find_all('table', attrs={'class':'tab-contents'})
    n=0
    for i in content:
        for m in i.find_all('td'):
            meta = []
            for j in m.find_all('a'):
                if p.search(j.text):
                    url = 'http://vestnik.spbu.ru/html{0}/s14/s14v4/{1}'.format(year, j['href'])
                    pdf = requests.get(url)
                    with open('spbu_law_articles_20{0}/spbu_law_20{1}_v4_{2}.pdf'.format(year, year, str(n)), 'wb') as f:
                        f.write(pdf.content)
                    meta.append(url)
                    meta.append(j.text)
            for k in m.find_all('i'):
                if p.search(k.text):
                    meta.append(k.text)
                    meta.append('20{}'.format(year))
                    meta.append('Право')
            if meta:
                with open('spbu_law_articles_20{0}_meta/spbu_law_20{1}_v4_{2}_meta.txt'.format(year, year, str(n)), 'w') as f:
                    for i in meta:
                        f.writelines(i + '\r\n')
            n+=1
            time.sleep(0.5)
