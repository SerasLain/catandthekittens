import argparse
from conllu import parse
from collections import defaultdict
import json
from find_mistakes.search_for_mistakes import Searcher
import os
from tqdm import tqdm
from statistics import mean, median, mode

SENTENCE_LENGTHS_THRESHOLDS = 'sentence_length_thresholds.json'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='file to check')
    parser.add_argument('domain', help='domain the file belongs to')
    parser.add_argument('--threshold_genitives', default=3, help='threshold for genitives')
    parser.add_argument('--marked_path', help='path to marked files')
    args = parser.parse_args()
    return args


def parse_file(file):
    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()
        tree = parse(data)
    return tree


def dump_to_json(obj):
    with open(SENTENCE_LENGTHS_THRESHOLDS, 'w', encoding='utf-8') as f:
        json.dump(obj, f)



def count_sentence_length_threshold(marked_path):
    domain_means = defaultdict(int)
    domain_maxs = defaultdict(int)
    domain_medians, domain_modes = defaultdict(int), defaultdict(int)
    for file in tqdm(os.listdir(marked_path)):
        if file[-5:] == 'conll':
            tree = parse_file(os.path.join(marked_path, file))
            lengths = []
            length = 0
            for x in tree:
                for i in range(len(x) - 1):
                    if x[i]['feats'] not in {'SENT', 'PUNC'} and len(x[i]['form']) > 1 and len(x[i - 1]['form']) > 1:
                        length += 1
                    if x[i]['id'] > x[i + 1]['id'] and length > 0:
                        lengths.append(length)
                        length = 0
            domain = file.split('.')[0]
            domain_means[domain] = mean(lengths)
            domain_maxs[domain] = max(lengths)
            domain_medians[domain] = median(lengths)
            domain_modes[domain] = mode(lengths)
    dump_to_json({'means': domain_means, 'maxs': domain_maxs, 'medians': domain_medians, 'modes': domain_modes})


if __name__ == '__main__':
    args = parse_args()
    if SENTENCE_LENGTHS_THRESHOLDS not in os.listdir(os.getcwd()):
        count_sentence_length_threshold(args.marked_path)
    searcher = Searcher()
    searcher.check_all(args, parse_file(args.file))
