import subprocess
import argparse
import os
import logging
"""
Скрипт для разметки корпуса ru-syntax-ом.
Запускать из-под линукса, ибо maltparser с windows не дружит.
Модель с сайта ru-syntax работает с версией maltparser-а 1.8.1, но не позднее.
Названия размечаемых файлов должны быть без пробелов.
"""


def parse_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('python', help='python path variable')
    parser.add_argument('parser', help='path to ru-syntax.py')
    parser.add_argument('test_dir', help='path to test directory')
    return parser.parse_args()


def ru_syntax_subprocess(infile,args):
    command = args.python+' '+args.parser+ ' '+infile
    proc = subprocess.run(command, shell=True)
    
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    test_dir = args.test_dir
    test_dir_abs = os.path.abspath(test_dir)
    for filename in os.listdir(test_dir):
        logging.info(filename)
        ru_syntax_subprocess(test_dir_abs+'/'+filename,args)
        
        
    

