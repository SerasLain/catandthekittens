import argparse
from conllu import parse
from find_mistakes.search_for_shit import Searcher
import os
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='file to check')
    parser.add_argument('--threshold', help='threshold')
    args = parser.parse_args()
    return args


def parse_file(file):
    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()
        tree = parse(data)
    return tree


if __name__ == '__main__':
    args = parse_args()
    file = args.file
    tree = parse_file(file)
    threshold = args.threshold
