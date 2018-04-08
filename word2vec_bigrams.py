from gensim.models import Phrases, Word2Vec
import os
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='directory with corpus')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    documents = []
    dir = args.dir
    ling = os.listdir(dir)
    for file in ling:
        if file[-3:] == 'txt':
            with open(dir + "/" + file, 'r', encoding='utf-8') as f:
                documents.append(f.read().replace('\n', ' ').lower())

    sentence_stream = []
    for doc in documents:
        sents = doc.split(".")
        for sent in sents:
            sentence_stream.append(sent.split(' '))
    bigram = Phrases(sentence_stream, min_count=1, threshold=2)
    new_sents = []
    for sent in sentence_stream:
        new_sents += bigram[sent]

    model = Word2Vec([new_sents], min_count=1)
    model.save('model')
