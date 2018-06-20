from collections import defaultdict
from gensim.models import Word2Vec
from tqdm import tqdm
import logging
from alphabet_detector import AlphabetDetector
from find_mistakes.search import args, load_from_json

MORE_LESS = ['более', 'менее']
SENTENCE_LENGTHS_THRESHOLDS = 'sentence_length_thresholds.json'
STATISTICS = "maxs"

class Searcher:
    def __init__(self):
        self.found = defaultdict(list)
        self.flag_i_vs_we = ''


    def find_genitives(self, gen_chain, word, s, i, threshold):
        if 'gen' in word['feats']:
            gen_chain.append((word['form'], s, i))
        else:
            if len(gen_chain) >= int(threshold):
                self.found['genitives'].append(gen_chain)
            gen_chain = []
        return gen_chain
    def find_wrong_comparativ(self, sent, word, i, s):
        if i <len(sent):
            next = sent[i + 1]
            if word['form'] in MORE_LESS and 'comp' in next['feats']:
                self.found['comparatives'].append((word['form'], next['form'], s, i))

    def find_wrong_coordinate_NPs(self, sent, i, s, word, model):
        if i < len(sent):
            if word['form'] == 'и':
                t = i
                pair = []
                while 'S' not in sent[t]['feats'] and 'V' not in sent[t]['feats'] and t > 0:
                    t -= 1
                if 'S' in sent[t]['feats']:
                    pair.append(sent[t]['form'])
                t = i
                while 'S' not in sent[t]['feats'] and 'V' not in sent[t]['feats'] and t < len(sent):
                    t += 1
                if 'S' in sent[t]['feats']:
                    pair.append(sent[t]['form'])
                if len(pair) > 1:
                    if pair[0] in model.wv.vocab and pair[1] in model.wv.vocab:
                        self.found['coordinate_NPs'].append(pair + [s,i, model.similarity(pair[0], pair[1])])
                    else:
                        self.found['coordinate_NPs'].append(pair + [s,i, float('-inf')])

    def not_in_vocabulary(self,ad,word,i, model, s):
            if word['form'].isalpha() and ad.only_alphabet_chars(word['form'], "CYRILLIC") and word['form'].lower() not in model.wv.vocab:
                self.found['not in vocabulary'].append((word['form'],s, i))

    def i_vs_we(self, i, word, s):
        if word['lemma']=='Я' and not self.flag_i_vs_we:
            self.flag_i_vs_we ='i'
            self.found['i vs we'].append((word['form'],s, i))
        elif (word['lemma']=='Я' and self.flag_i_vs_we=='we') or (word['lemma']=='МЫ' and self.flag_i_vs_we=='i'):
            self.found['i vs we'].append((word['form'],s, i))
        elif word['lemma']=='МЫ' and not self.flag_i_vs_we:
            self.flag_i_vs_we ='we'
            self.found['i vs we'].append((word['form'],s, i))

    def check_mood(self,sent, i, word,s):
        if word['form'] == 'бы' and i>0:
            self.found['subjunctive mood'].append((sent[i-1]['form'], word['form'],s, i))
        if 'imper' in word['feats']:
            self.found['imperative mood'].append((word['form'],s,i))


    def check_sentence_length(self,sent,s,threshold):
        if len(sent) > threshold:
            self.found['lengths'].append(s)

    def check_all(self,tree):
        logging.basicConfig(level=logging.INFO, filename='found.log')
        model = Word2Vec.load('../../collocation_frequences/Models/LinguisticModel')
        ad = AlphabetDetector()
        sent_threshold = load_from_json(SENTENCE_LENGTHS_THRESHOLDS)[STATISTICS][args.domain]
        for s, sent in enumerate(tqdm(tree)):
            gen_chain = []
            for i, word in enumerate(sent):
                self.check_mood(sent, i,word,s)
                self.i_vs_we(i, word, s)
                self.not_in_vocabulary(ad,word,i, model,s)
                gen_chain = self.find_genitives(gen_chain, word, s, i, args.threshold_genitives)
                self.find_wrong_comparativ(sent, word, i, s)
                self.find_wrong_coordinate_NPs(sent, i, s, word, model)
                self.check_sentence_length(sent,s,sent_threshold)
        logging.info("")








