import os
from math import log10, sqrt, log2
import logging


def filter_by_tsc(path):
    with open(path, 'r', encoding='utf-8') as s:
        print(path)
        with open(path[:-4]+'_filtered.csv', 'a', encoding='utf-8') as t:
            for line in s.readlines():
                if line.startswith("coll"):
                    t.write(line)
                elif float(line.split('\t')[4]) > 1.00:
                    t.write(line)
                else:
                    pass


def count_567(domain_path):
    # Just script to get ngrams from the corpus
    unigrams = read_ngrams(os.path.join(domain_path, '1.csv'))
    corpus_size = sum([int(i) for i in unigrams.values()])

    quadrigrams = {}
    with open(os.path.join(domain_path, '4_scored_ranked_logDice.csv'), 'r', encoding='utf-8') as f:
        # collocation_tags	raw_frequency	log_Dice	PMI	tscore	logDice rank	pmi_rank	tsc_rank	summary pmi and tsc	summary logDice and pmi
        for line in f.readlines():
            line_arr = line.strip('\n').split('\t')
            collocation_tags, word_freq = line_arr[0], line_arr[1]
            quadrigrams[collocation_tags] = word_freq

    n1grams = quadrigrams
    for i in range(5, 8):
        if i == 5:
            count_ngram(domain_path, str(i) + '.csv', str(i)+'_scored.csv', n1grams, unigrams, corpus_size)
        else:
            count_ngram(domain_path, str(i) + '.csv', str(i)+'_scored.csv', str(i-1)+'.csv', unigrams, corpus_size)




def count_ngram(domain_path, ngram_raw, ngram_scored, n1grams, unigrams, corpus_size):
    # One more script to count all metrics for 5,6,7-grams
    if type(n1grams) is str:
        n1grams = read_ngrams(os.path.join(domain_path, n1grams))
    else:
        pass
    print(ngram_raw)
    print(list(n1grams.keys())[:3])
    quingrams = read_ngrams(os.path.join(domain_path, ngram_raw))
    quingrams_scored = open(os.path.join(domain_path, ngram_scored), 'a', encoding='utf-8')
    print('head')
    quingrams_scored.write('\t'.join(['collocation and tags', 'raw frequency', 'log-Dice', 'PMI', 't-score']) + '\n')
    for colloc_tag in quingrams:
        try:
            logdsc, pmisc, tsc = measure(colloc_tag, quingrams[colloc_tag],
                                         n1grams, unigrams, corpus_size)
            quingrams_scored.write('\t'.join([str(i) for i in [colloc_tag, quingrams[colloc_tag], logdsc, pmisc, tsc]])
                                   + '\n')
        except KeyError:
            print(colloc_tag)
    quingrams_scored.close()
    print('done')
    return quingrams




def domain_counts(domain_path):
    """

    :param domain_path: str, path to the domain folder with unigrams tsv
    :return: creates tab-separated csv for bigrams, trigrams and quadrigrams
    """
    unigrams = read_ngrams(os.path.join(domain_path, '1.csv'))
    corpus_size = sum([int(i) for i in unigrams.values()])
    bigrams = read_ngrams(os.path.join(domain_path, '2.csv'))
    bigrams_scored = open(os.path.join(domain_path, '2_scored.csv'), 'a', encoding='utf-8')
    print('bigrams')
    bigrams_scored.write('\t'.join(['collocation and tags', 'raw frequency', 'log-Dice', 'PMI', 't-score']) + '\n')
    for colloc_tag in bigrams:
        logdsc, pmisc, tsc = measure(colloc_tag, bigrams[colloc_tag],
                                     unigrams, unigrams, corpus_size)
        bigrams_scored.write('\t'.join([str(i) for i in [colloc_tag, bigrams[colloc_tag], logdsc, pmisc, tsc]]) + '\n')
    bigrams_scored.close()
    print('trigrams')
    trigrams = read_ngrams(os.path.join(domain_path, '3.csv'))
    trigrams_scored = open(os.path.join(domain_path, '3_scored.csv'), 'a', encoding='utf-8')
    trigrams_scored.write('\t'.join(['collocation and tags', 'raw frequency', 'log-Dice', 'PMI', 't-score']) + '\n')
    for colloc_tag in trigrams:
        logdsc, pmisc, tsc = measure(colloc_tag, trigrams[colloc_tag], bigrams,
                                     unigrams, corpus_size)
        trigrams_scored.write('\t'.join([str(i) for i in [colloc_tag, trigrams[colloc_tag], logdsc, pmisc, tsc]])
                              + '\n')
    trigrams_scored.close()
    del bigrams
    print('quadrigrams')
    quadrigrams = read_ngrams(os.path.join(domain_path, '4.csv'))
    quadrigrams_scored = open(os.path.join(domain_path, '4_scored.csv'), 'a', encoding='utf-8')
    quadrigrams_scored.write('\t'.join(['collocation and tags', 'raw frequency', 'log-Dice', 'PMI', 't-score']) + '\n')
    for colloc_tag in quadrigrams:
        logdsc, pmisc, tsc = measure(colloc_tag,
                                     quadrigrams[colloc_tag],
                                     trigrams,
                                     unigrams,
                                     corpus_size)
        quadrigrams_scored.write('\t'.join([str(i) for i in [colloc_tag, quadrigrams[colloc_tag], logdsc,
                                                             pmisc, tsc]]) + '\n')
    quadrigrams_scored.close()
    del trigrams


def read_ngrams(path):
    """
    Loads ngrams from csv
    :param path: str, path to the tab-separated csv-file with ngrams
    :return: container: dict, dictionary of mwe with its frequencies.
    """

    file = open(path, 'r', encoding='utf-8')
    container = {}
    for line in file:
        collocation_tags, freq = line.strip('\n').split('\t')
        container[collocation_tags] = freq
    return container


def measure(colloc_tag, colloc_count, n1grams, unigrams, n):
    """
    counts scores for all measures

    :param colloc_tag:str key from dictionary of ngrams like 'word word/tag tag'
    :param colloc_count: int, how many times collocation appears
    :param n1grams: dict, a dict of MWE n-1-grams, like bigrams
    :param unigrams: dict, a dict of words with its count in the corpus
    :param n: int, len of corpus
    """
    collocation_words, collocation_tags = colloc_tag.split('/')
    collocation_words = collocation_words.split(' ')
    collocation_tags = collocation_tags.split(' ')
    pattern_words = ' '.join(collocation_words[:-1])
    pattern_tags = ' '.join(collocation_tags[:-1])

    pattern = pattern_words + '/' + pattern_tags
    last_word = collocation_words[-1] + '/' + collocation_tags[-1]
    c_pattern = int(n1grams[pattern])
    c_lw = int(unigrams[last_word])
    colloc_count = int(colloc_count)

    tsc = t_score(colloc_count, c_pattern, c_lw, n)
    pmisc = pmi(colloc_count, c_pattern, c_lw, n)
    logdsc = logDice(colloc_count, c_pattern, c_lw)
    return logdsc, pmisc, tsc


def t_score(colloc_count, c_pattern, c_lw, n):
    """
    t-score measure for collocation based on the t-test. [Church, Using statistics in lexical analysis]
    t-score = (colloc_count - (c_pattern * c_lw) / n) / (sqrt(colloc_count))
    :param colloc_count:int how many times colloc appears in corpus
    :param c_pattern:int how many times all words but last appear in corpus
    :param c_lw:int how many times last word appears in corpus
    :param n:int corpus size

    :return: t-score for the collocation
    """
    score = (colloc_count - (c_pattern * c_lw) / n) / (sqrt(colloc_count))
    return score


def pmi(colloc_count, c_pattern, c_lw, n):
    """
    PMI-measure for collocation. PMI = log10((N*c(w1, w2, w3)/(c(pattern)*c(last_word)))
    [Foundations of Statistical Natural Language Processing]
    c(w) is how many times this word (or these words) appears in corpus
    pattern is a collocation without a last word
    N is a number of tokens in corpus
    :param colloc_count:int how many times collocation appears in corpus
    :param c_pattern:int how many times all words but last appear in corpus
    :param c_lw:int how many times last word appears in corpus
    :param n:int the number of tokens in corpus

    :return: float, pmi score for the collocation
    """
    score = log10((n * colloc_count / (c_pattern * c_lw)))
    return score


def logDice(colloc_count, c_pattern, c_lw):
    """
    Log-Dice measure.
    [Rychly, A Lexicographer-Friendly Association Score]
    :param colloc_count:int how many times collocation appears in corpus
    :param c_pattern:int how many times all words but last appear in corpus
    :param c_lw:int how many times last word appears in corpus
    :return: float
    """
    score = 14 + log2(2*colloc_count / (c_lw + c_pattern))
    return score


def read_ngrams_scored(path):
    # This func exists because and only because I forgot to count logDice ranking
    """
    reads the file with scored ngrams
    :param path: str
    :return: set of tuples with collocation_tags, raw_frequency, log-Dice, PMI, t-score
    """
    ngrams = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('coll'):
                pass
            else:
                ngram_info = tuple(line.strip('\n').split('\t'))
                ngrams.add(ngram_info)
    return ngrams


def ranked(pmi_ranking, tscore_ranking, logdice_ranking, tscore, PMI, logdice):
    """
    counts ranks for the collocation
    :param pmi_ranking: list of all pmi scores, sorted from more to less
    :param tscore_ranking: list of all t-scores in from more to less
    :param logdice_ranking: list of all logDice scores, sorted from more to less
    :param tscore: float, t-score
    :param PMI: float, PMI score
    :param logdice: float, logDice score
    :return: tuple of floats
    """
    tsc_rank = tscore_ranking[(float(tscore))]
    pmi_rank = pmi_ranking[float(PMI)]
    logdice_rank = logdice_ranking[float(logdice)]
    summary_tscpmi = tsc_rank + pmi_rank
    summary_logdpmi = logdice_rank + pmi_rank
    return tsc_rank, pmi_rank, logdice_rank, summary_tscpmi, summary_logdpmi

def get_rank(ngrams_set, path):
    """
    gives rank to every collocation in two measures and gives the sum of them
    :param ngrams_set: set of n-grams tuples
    :param path: str, path
    :return:
    """
    pmi_sorted = sorted(set([float(tup[3]) for tup in ngrams_set]), reverse=True)
    pmi_ranking = {}
    for i in range(len(pmi_sorted)):
        pmi_ranking[pmi_sorted[i]] = i + 1

    tscore_sorted = sorted(set([float(tup[4]) for tup in ngrams_set]), reverse=True)
    tscore_ranking = {}
    for i in range(len(tscore_sorted)):
        tscore_ranking[tscore_sorted[i]] = i + 1

    logDice_sorted = sorted(set([float(tup[2]) for tup in ngrams_set]), reverse=True)
    logDice_ranking = {}
    for i in range(len(logDice_sorted)):
        logDice_ranking[logDice_sorted[i]] = i + 1

    with open(path[:-4] + '_ranked.csv', 'a', encoding='utf-8') as f:
        f.write('\t'.join(['collocation_tags', 'raw_frequency', 'log_Dice', 'PMI', 'tscore',
                           'pmi_rank', 'tsc_rank', 'logD_rank', 'summary t-sc + pmi', 'summary logD + pmi']) + '\n')
        for collocation_scored in ngrams_set:
            collocation_tags, raw_frequency, log_Dice, PMI, tscore = collocation_scored
            tsc_rank, pmi_rank, logd_rank, summarytscpmi, summarylogdpmi = ranked(pmi_ranking, tscore_ranking,
                                                                                  logDice_ranking, tscore, PMI, log_Dice)
            f.write('\t'.join([collocation_tags, raw_frequency,
                               log_Dice, PMI, tscore, str(pmi_rank), str(tsc_rank), str(logd_rank),
                               str(summarytscpmi), str(summarylogdpmi)]) + '\n')


# These two functions added into the previous one

def logD_ranked(logDice_ranking, logD, pmi_rank):
    """
    counts logDice rank and sums it with pmi-rank
    :param logDice_ranking: dict of all logDice scores with rank
    :param logD: float, logDice score
    :param pmi_rank float, PMI score
    :return: sum of logDice rank and PMI rank, float
    """
    logDice_rank = logDice_ranking[logD]
    summary = logDice_rank + pmi_rank
    return logDice_rank, summary


def get_logd_rank(ngrams_set, path):
    """

    :param ngrams_set: set of n-grams tuples
    :param path: str, path
    :return: none, makes tsv-files with all ranks and measures
    """
    logDice_sorted = sorted(set([float(tup[2]) for tup in ngrams_set]), reverse=True)
    logDice_ranking = {}
    for i in range(len(logDice_sorted)):
        logDice_ranking[logDice_sorted[i]] = i + 1
    with open(path[:-4] + '_logDice.csv', 'a', encoding='utf-8') as f:
        f.write('\t'.join(['collocation_tags', 'raw_frequency', 'log_Dice', 'PMI', 'tscore',
                           'logDice rank', 'pmi_rank', 'tsc_rank', 'summary pmi and tsc',
                           'summary logDice and pmi']) + '\n')
        for collocation_scored in ngrams_set:
            collocation_tags, raw_frequency, logDice, PMI, tscore, pmi_rank, tsc_rank, pmi_tsc = collocation_scored
            logDice_rank, logD_pmi = logD_ranked(logDice_ranking, float(logDice), int(pmi_rank))
            f.write('\t'.join([collocation_tags, raw_frequency,
                               logDice, PMI, tscore, str(logDice_rank), pmi_rank,
                               tsc_rank, pmi_tsc, str(logD_pmi)]) + '\n')



def main():
    root = r'C:\Users\Eiko\Documents\Domains_collocations\Domains_collocations'
    #domains = os.listdir(root)
    #for name in domains:
    for name in ["Sociology and History"]:
        content = tuple(os.listdir(os.path.join(root, name)))
        fls = [tsv for tsv in content if ("ranked" in tsv and "filtered" not in tsv)]
        for tsv in fls:
            filter_by_tsc(os.path.join(os.path.join(root, name, tsv)))

        # count_567(os.path.join(root, name))


    #     domain_counts(os.path.join(r"C:\Users\Eiko\Documents\Domains_collocations\Domains_collocations\\", name))
    #     domain = os.path.join(r"C:\Users\Eiko\Documents\Domains_collocations\Domains_collocations\\", name)
    #     print(domain)
    #     scored = os.listdir(domain)
    #     fls = [fl for fl in scored if ('scored.csv' in fl)]
    # #     # Here should be the code for ranks
    #     #     d without logDice, but I hope if it would be really necessary to do it again,
    # #     # I will write a func, which counts all rankings
    #
    # #     # Yep I did it
    #
    #     for f in fls:
    #         path = os.path.join(domain, f)
    #         print(path)
    #         ngrams = read_ngrams_scored(path)
    #         get_rank(ngrams, path)


if __name__ == "__main__":
    main()
