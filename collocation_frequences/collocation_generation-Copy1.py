import pandas as pd

new_df = pd.read_csv('suggestions.csv')

from pymystem3 import Mystem

m = Mystem()

from gensim.models import Word2Vec

import operator

model = Word2Vec.load('Models/LinguisticModel')


def suggest(input_string, collocations, model):
    c_max = max(collocations.pmi)
    suggestions = {}
    w1 = input_string.split()[0]
    w2 = input_string.split()[1]
    if w1 not in list(collocations.first_word) and w2 not in list(collocations.second_word):
        pass
    else:
        tags = []
        if w1 not in list(collocations.first_word):
            w2_ind = list(collocations.second_word).index(w2)
            tags.append(m.analyze(w1)[0]['analysis'][0]['gr'].split(',')[0])
            tags.append(collocations.second_tag[w2_ind])
            for i in range(len(collocations) - 1):
                if collocations.second_word[i] == w2 and collocations.first_tag[i] == tags[0]:
                    suggestions[collocations.first_word[i] + ' ' + w2] = collocations.pmi[i] / c_max
                    try:
                        sim = model.wv.similarity(collocations.first_word[i], w2)
                    except KeyError:
                        sim = -float('inf')
                    first_word_w2 = collocations.first_word[i] + ' ' + w2
                    suggestions[first_word_w2] += sim
        elif w2 not in list(collocations.second_word):
            w1_ind = list(collocations.first_word).index(w1)
            tags.append(collocations.first_tag[w1_ind])
            tags.append(m.analyze(w2)[0]['analysis'][0]['gr'].split(',')[0])
            for i in range(len(collocations) - 1):
                if collocations.first_word[i] == w1 and collocations.second_tag[i] == tags[1]:
                    suggestions[w1 + ' ' + collocations.second_word[i]] = collocations.pmi[i] / c_max
                    first_word_w2 = suggestions.get(collocations.first_word[i] + ' ' + w2)
                    try:
                        sim = model.wv.similarity(w1, collocations.second_word[i])
                    except KeyError:
                        sim = -float('inf')
                    if first_word_w2:
                        suggestions[first_word_w2] += sim
        else:
            w1_sub = []
            w2_sub = []
            w1_ind = list(collocations.first_word).index(w1)
            w2_ind = list(collocations.second_word).index(w2)
            tags.append(collocations.first_tag[w1_ind])
            tags.append(collocations.second_tag[w2_ind])
            for i in range(len(collocations) - 1):
                if collocations.first_word[i] == w1 and collocations.second_tag[i] == tags[1]:
                    suggestions[w1 + ' ' + collocations.second_word[i]] = collocations.pmi[i] / c_max
                    try:
                        sim = model.wv.similarity(w1, collocations.second_word[i])
                    except KeyError:
                        sim = -float('inf')
                    first_word_w2 = [collocations.first_word[i] + ' ' + w2]
                    if first_word_w2:
                        suggestions[collocations.first_word[i] + ' ' + w2] += sim
                    w2_sub.append(collocations.second_word[i])
                if collocations.second_word[i] == w2 and collocations.first_tag[i] == tags[0]:
                    suggestions[collocations.first_word[i] + ' ' + w2] = collocations.pmi[i] / c_max
                    try:
                        sim = model.wv.similaritymodel.wv.similarity(collocations.first_word[i], w2)
                    except KeyError:
                        sim = -float('inf')
                    first_word_w2 = [collocations.first_word[i] + ' ' + w2]
                    if first_word_w2:
                        suggestions[first_word_w2] += sim
                    w1_sub.append(collocations.first_word[i])
            for w in w1_sub:
                for j in range(len(collocations) - 1):
                    if collocations.first_word[j] == w and collocations.second_word[j] in w2_sub:
                        suggestions[w + ' ' + w2] += 1.0 / len(w2_sub)
            for k in w2_sub:
                for j in range(len(collocations) - 1):
                    if collocations.second_word[j] == k and collocations.first_word[j] in w1_sub:
                        suggestions[w1 + ' ' + k] += 1.0 / len(w1_sub)
    if len(suggestions) > 10:
        return sorted(suggestions.items(), key=operator.itemgetter(1))[-10:]
    else:
        return sorted(suggestions.items(), key=operator.itemgetter(1))


print(suggest('автор думает', new_df, model))

print(suggest('автор котик', new_df, model))

print(suggest('котик предлагает', new_df, model))
