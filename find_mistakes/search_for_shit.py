from collections import defaultdict
from gensim.models import Word2Vec
from tqdm import tqdm
import logging
from alphabet_detector import AlphabetDetector

class Searcher:
    def __init__(self):
        self.found = defaultdict(list)

    def find_genitives(self, tree, file, threshold):
        gen_chain = []
        for i in range(len(tree)):
            line = tree[i]
            if 'gen' in line['feats']:
                gen_chain.append((line['form'], i))
            else:
                if len(gen_chain) >= int(threshold):
                    self.found['genitives'].append(gen_chain)
                gen_chain = []
        with open("gen.{}.txt".format(file).replace('/', '_'), 'w', encoding='utf-8') as f:
            for ch in self.found['genitives']:
                for g in ch:
                    f.write(g[0] + ' ')
                f.write('\r\n')

    def find_wrong_comparativ(self, tree):
        more_less = ['более', 'менее']
        for i in range(len(tree) - 1):
            line = tree[i]
            next = tree[i + 1]
            if line['form'] in more_less and 'comp' in next['feats']:
                self.found['comparatives'].append((line['form'], next['form'], i))

    def find_wrong_coordinate_NPs(self, tree):
        model = Word2Vec.load('../collocation_frequences/Models/LinguisticModel')
        for i in range(1, len(tree) - 1):
            if tree[i]['form'] == 'и':
                t = i
                pair = []
                while 'S' not in tree[t]['feats'] and 'V' not in tree[t]['feats'] and t > 0:
                    t -= 1
                if 'S' in tree[t]['feats']:
                    pair.append(tree[t]['form'])
                t = i
                while 'S' not in tree[t]['feats'] and 'V' not in tree[t]['feats'] and t < len(tree):
                    t += 1
                if 'S' in tree[t]['feats']:
                    pair.append(tree[t]['form'])
                if len(pair) > 1:
                    if pair[0] in model.wv.vocab and pair[1] in model.wv.vocab:
                        self.found['coordinate_NPs'].append(pair + [i, model.similarity(pair[0], pair[1])])
                    else:
                        self.found['coordinate_NPs'].append(pair + [i, float('-inf')])

    def not_in_vocabulary(self,tree):
        logging.basicConfig(level=logging.INFO)
        logging.info("Loading Word2Vec model")
        model = Word2Vec.load('../collocation_frequences/Models/LinguisticModel')
        ad = AlphabetDetector()
        for i,x in enumerate(tqdm(tree)):
            if x['form'].isalpha() and ad.only_alphabet_chars(x['form'], "CYRILLIC") and x['form'].lower() not in model.wv.vocab:
                self.found['not in vocabulary'].append((x['form'],i))

    def i_vs_we(self, tree, file):
        flag = ''
        self.found['i vs we']=dict()
        self.found['i vs we'][file]=[]
        for x in tree:
            for i, word in enumerate(x):
                if word['lemma']=='Я' and not flag:
                    flag ='i'
                    self.found['i vs we'][file].append((word['form'], i))
                elif (word['lemma']=='Я' and flag=='we') or (word['lemma']=='МЫ' and flag=='i'):
                    self.found['i vs we'][file].append((word['form'], i))
                elif word['lemma']=='МЫ' and not flag:
                    flag ='we'
                    self.found['i vs we'][file].append((word['form'], i))









