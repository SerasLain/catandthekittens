# installations: docx2txt, pdfminer.six
# author: Terekhina Maria
# edited: Maria Fedorova
# не работает под линуксом

import docx2txt
import io
import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import argparse
import os


def remove_ending(text):
    '''
    Remove bibliography.
    '''
    text = re.sub('(Литература|Список( использованной)? литературы|Библиография)(\.)?.*', '', text, flags=re.S)
    return text


def remove_begining(text):
    '''
    Remove all before introduction
    '''
    text = re.sub('.*?Введение(\.)?', 'Введение', text, flags=re.S)
    return text


def clean_text(text):
    '''
    Remove page numbers and system symbols
    '''
    text = re.sub('\f.+\n', '\n', text)
    text = re.sub('-\n', '', text)
    text = re.sub('\n+', '\n', text)

    text = re.sub('\n+( )*[0-9]+( )*\n+', '', text)
    text = remove_begining(text)
    text = remove_ending(text)
    text_to_count = re.sub('^[а-яА-ЯЁёA-Za-z-\s]', ' ', text)
    count = len(re.split('\s+', text_to_count))
    return text, count


def convert_pdf_to_txt(path):
    '''
    Convert pdf to plain text
    '''
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                  password=password,
                                  caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return clean_text(text)


def document_to_text(path):
    '''
    Choose a convertor for the file: pdf or docx
    '''
    if path[-5:] == ".docx":
        text = docx2txt.process(path)
        return clean_text(text)
    elif path[-4:] == ".pdf":
        return convert_pdf_to_txt(path)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('target_dir', help='where documents to clean are')
    parser.add_argument('journal', help='journal')
    parser.add_argument('year', help='year')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    target_dir, journal, year = args.target_dir, args.journal, args.year
    cleaned = 'cleaned'
    if cleaned not in os.listdir(os.getcwd()):
        os.mkdir(cleaned)
    res_dir = cleaned+'/'+journal
    if journal not in os.listdir(os.getcwd()+'/'+cleaned):
        os.mkdir(cleaned+'/'+journal)
    total_count = 0
    for i, file in enumerate(os.listdir(target_dir)):
        with open("cleaned/{0}/{1}_{2}.txt".format(journal, year, i), 'w', encoding='utf-8') as f:
            text, count = document_to_text(target_dir+'/'+file)
            f.write(text)
            print(i, count)
            total_count += count
    print("Files in this directory contain {0} tokens".format(total_count))
