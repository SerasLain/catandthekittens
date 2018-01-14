import requests
from bs4 import BeautifulSoup
import time
import os
from alphabet_detector import AlphabetDetector
import logging


# Анин код с изменениями


def get_articles(year1, year2, subject_code, subject_name, subject_name_rus):
    """ Скачивает тексты вестника СПбГУ в pdf
    year1, year2 - годы, выпуски которых скачиваем
    subject_code - код предметной области в url-e, н-р, право 14, социология 12
    subject_name, subject_name_rus - название предметной области
    """
    ad = AlphabetDetector()
    logging.basicConfig(level=logging.INFO)
    for i in range(year1, year2):
        os.mkdir('spbu_' + subject_name + '_articles_{}'.format(i))
        os.mkdir('spbu_' + subject_name + '_{}_meta'.format(i))
        year = str(i)[-2:]
        for v in range(1, 5):
            url = 'http://vestnik.spbu.ru/html' + year + '/s' + subject_code + '/s' + subject_code + 'v{}/s'.format(
                v) + subject_code + 'v{}.html'.format(v)
            logging.info(url)
            r = requests.get(url)
            r.encoding = 'cp1251' #какая нечисть делала этот сайт, хочу посмотреть ей в глаз!!!
            soup = BeautifulSoup(r.text, 'lxml')
            # p = re.compile('[а-яА-ЯёЁ]')
            content = soup.find_all('table', attrs={'class': 'tab-contents'})
            n = 0
            for i in content:
                td = i.find_all('td')
                for m in td:
                    meta = []
                    for j in m.find_all('a'):
                        if ad.only_alphabet_chars(j.text, "CYRILLIC"):
                            url = 'http://vestnik.spbu.ru/html{0}/s{1}/s{2}v{3}/{4}'.format(year, subject_code,
                                                                                            subject_code, v, j['href'])
                            pdf = requests.get(url)
                            with open('spbu_{0}_articles_20{1}/spbu_{2}_{3}'
                                      '_v{4}_{5}.pdf'.format(subject_name, year, subject_name, year, v, str(n)), 'wb') as f:
                                f.write(pdf.content)
                            meta.append(url)
                            meta.append(j.text)
                    for k in m.find_all('i'):
                        if ad.only_alphabet_chars(k.text, "CYRILLIC"):
                            meta.append(k.text)
                            meta.append('20{}'.format(year))
                            meta.append(subject_name_rus)
                    if meta:
                        with open('spbu_{0}_20{1}_meta/'
                                  'spbu_{2}_20{3}_v{4}_{5}_meta.txt'.format(subject_name, year, subject_name,
                                                                            year, v, str(n)), 'w',
                                  encoding='utf-8') as f:
                            for i in meta:
                                f.writelines(i + '\r\n')
                    n += 1
                    time.sleep(0.5)


if __name__ == '__main__':
    get_articles(2016, 2018, '12', 'sociology', 'Социология')
