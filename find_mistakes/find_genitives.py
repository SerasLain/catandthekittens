import argparse
from conllu import parse
import os

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='file to check')
    parser.add_argument('threshold', help='file to check')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    file = args.file
    tree = None
    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()
        tree = parse(data)[0]
    gen_chains = []
    gen_chain = []
    for i in range(len(tree)):
        line = tree[i]
        if 'gen' in line['feats']:
            gen_chain.append((line['form'], i))
        else:
            if len(gen_chain) >= int(args.threshold):
                gen_chains.append(gen_chain)
            gen_chain = []
    with open("gen.{}.txt".format(file).replace('/','_'),'w',encoding='utf-8') as f:
        for ch in gen_chains:
            for g in ch:
                f.write(g[0]+' ')
            f.write('\r\n')