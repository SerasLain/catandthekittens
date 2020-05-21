import logging
import mysql.connector
import os
from mysql.connector.errors import IntegrityError, DataError, InternalError, ProgrammingError
import csv
from collections import Counter
from colloc import t_score, logDice, pmi, c_value

from k import USER, PASS


logging.basicConfig(filename="CAT_database.log",
                    level=logging.DEBUG,
                    format='%(levelname)s %(name)s %(asctime)s : %(message)s')
log = logging.getLogger("database")


cnx = mysql.connector.connect(user=USER, password=PASS,
                              host='127.0.0.1',
                              database='cat')

cursor = cnx.cursor()


def sql(scriptname):
    """
    Reads the file with query from scripts directory
    :param scriptname: str, filename
    :return: str, an SQL-query for MySQL DB
    """
    with open(os.path.join('MySQL Scripts', scriptname), 'r', encoding='utf-8') as f:
        command = f.read()
    return command


def delete_text(text_id):
    # TODO: переделать обновление подсчета при удалении текста - одно слово может и несколько раз встретиться
    c = cnx.cursor()
    c.execute(
        "UPDATE cat.unigrams AS `temp`, (SELECT id_unigram FROM cat.words WHERE id_text = (%s)) AS `cond` SET `temp`.`freq` = `temp`.`freq` - 1 WHERE `temp`.`id_unigram` = `cond`.`id_unigram`;",
        (text_id,))
    cnx.commit()
    c.execute("DELETE FROM cat.unigrams WHERE freq=0")
    cnx.commit()
    command = "DELETE FROM cat.metadata WHERE id_text = (%s)"
    c.execute(command, (text_id,))
    cnx.commit()
    c.close()


def count_bigrams(domain, minimum=3):
    """
    Extracts all 2-grams from the texts of the domain and counts frequency in this domain for them.
    :param domain: int, domain_id from which you want extract n-grams.
    :param minimum: int, frequency threshold
    :return:
    """
    log.info('Counting bigrams in domain %s', domain)
    assert type(domain) is int

    cursor.execute("""    (SELECT 
            w1, w2
        FROM
            (SELECT 
            cat.words.id_unigram AS w1, word2.id_unigram AS w2
        FROM
            cat.words, metadata
        JOIN (cat.words AS word2)
        WHERE
            words.id_text = word2.id_text
                AND words.id_sent = word2.id_sent
                AND words.id_position + 1 = word2.id_position
                AND words.id_text = metadata.id_text
                AND word2.id_text = metadata.id_text
                AND metadata.id_domain = %s) AS result)""", (domain,))
    log.debug('Selected!')
    bigrams_counted = Counter(cursor.fetchall())
    log.debug('Counted!')

    for ngram in bigrams_counted:
        wf1, wf2 = ngram
        freq = bigrams_counted[ngram]
        if freq >= minimum:
            try:
                cursor.execute(
                    "INSERT INTO cat.2grams (wordform_1, wordform_2, d{}_freq) VALUE (%s, %s, %s)".format(domain),
                    (wf1, wf2, freq))
            except IntegrityError:
                cursor.execute(
                    """
                    UPDATE cat.2grams
                    SET d{}_freq = d{}_freq + %s 
                    WHERE wordform_1 = %s 
                        AND wordform_2 = %s
                    """.format(domain, domain), (freq, wf1, wf2))
    log.debug('Inserted!')

    # cnx.commit()
    log.info('Bigrams commited!')


def count_2metrics(domain, minimum=3):
    """
    Counts all metrics for already extracted 2-grams with counted frequency.
    :param domain: int, domain_id, which size will be used to calculate related metrics.
    :param minimum: int, frequency threshold.
    :return:
    """

    log.info('Counting metrics!')
    cursor.execute(
        """
        SELECT 
            COUNT(*)
        FROM
            (SELECT 
                id_word
            FROM
                words, metadata
            WHERE
                words.id_text = metadata.id_text
                AND 
                    metadata.id_domain = (%s)
                    )
            AS sd
            """, (domain,))
    n = cursor.fetchone()[0]
    log.info('Domain size %s', n)

    cursor.execute(
        """
        SELECT 
            id_bigram AS id,
            d{}_freq AS freq,
            w1.freq{} AS w1_freq,
            w2.freq{} AS w2_freq
        FROM
            2grams,
            unigrams AS w1,
            unigrams AS w2
        WHERE
            2grams.wordform_1 = w1.id_unigram
            AND 
                2grams.wordform_2 = w2.id_unigram
                """.format(domain, domain, domain))
    log.debug('Selected!')
    data = set()
    for _id, colloc_freq, pattern_freq, lw_freq in cursor:
        if colloc_freq >= minimum:
            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)
            data.add((logdsc, pmisc, tsc, _id))
        # log.debug('Counted %s', _id)
    log.info('Ready to insert22')
    for i in data:
        if i[-1] % 1000 == 0:
            print(i)
        cursor.execute("""
            UPDATE 2grams 
            SET 
                d{}_logdice = %s,
                d{}_pmi = %s,
                d{}_tsc = %s
            WHERE
                id_bigram = %s 
                """.format(domain, domain, domain), i)

    # cnx.commit()
    log.info('Commited!')


def fetch_bigrams(domain):
    # TODO: дописать, а то оно ж не запишет ничего))) Выкинуть?
    """
    Writes a tab-separated
    :param domain:
    :return:
    """
    command = """SELECT 
    id_bigram,
    word1,
    pos_1,
    word2,
    pos_2,
    d{}_logdice,
    d{}_pmi,
    d{}_tsc
FROM
    (SELECT 
        id_bigram,
            unigram word1,
            lemma,
            wordform_2,
            d{}_logdice,
            d{}_pmi,
            d{}_tsc
    FROM
        2grams, unigrams
    WHERE
        d{}_tsc > 2.55
            AND wordform_1 = id_unigram
    ORDER BY logdice DESC
    LIMIT 5000) AS wf1
        INNER JOIN
    (SELECT 
        id_lemmas, pos AS pos_1
    FROM
        lemmas
    INNER JOIN pos ON lemmas.id_pos = pos.id_pos) AS ttt ON lemma = id_lemmas
        INNER JOIN
    (SELECT 
        id_unigram, unigram AS word2, pos AS pos_2
    FROM
        unigrams, (SELECT 
        id_lemmas, pos
    FROM
        lemmas
    INNER JOIN pos ON lemmas.id_pos = pos.id_pos) AS ttt
    WHERE
        unigrams.lemma = ttt.id_lemmas) AS ttt1 ON wordform_2 = id_unigram""".format(*[domain] * 6)
    cursor.execute(command)
    a = cursor.fetchall()
    with open('domain_{}_bigrams.csv'.format(domain), 'w') as f:
        cc = csv.writer(f)


def get_n_count_3grams(domain, minimum=3):
    """
    Extracts all 3-grams from the texts of the domain and counts frequency and all metrics in this domain for them.
    :param domain: int, domain_id from which you want extract n-grams.
    :param minimum: int, frequency threshold
    :return:
    """

    log.info('Counting trigrams for domain %s', domain)

    command = sql('getting_3grams.sql')

    cursor.execute(command, (domain,))
    data = Counter(cursor.fetchall())
    log.debug('Counted!')
    n = get_domain_size(domain)
    verbose = True
    for trigram in data:
        if data[trigram] >= minimum:
            w1, w2, w3 = trigram
            if verbose:
                log.debug("Started! %s", trigram)
            if w1 % 100 == 0:
                log.debug("working with %s", w1)
            cursor.execute(
                """
                SELECT id_bigram, d{}_freq 
                FROM 2grams WHERE wordform_1 = %s AND wordform_2 = %s
                """.format(domain), (w1, w2))

            id_bigram, pattern_freq = cursor.fetchone()
            if pattern_freq == 0:
                print(w1, ' ', w2)
                print(trigram, data[trigram])

            cursor.execute("SELECT freq{} FROM unigrams WHERE id_unigram = %s".format(domain), (w3, ))
            lw_freq = cursor.fetchone()[0]
            if lw_freq == 0:
                print(w3)
            colloc_freq = data[trigram]

            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)

            try:
                cursor.execute("""
                INSERT INTO 3grams (bigram, token, d{}_freq, d{}_logdice, d{}_pmi, d{}_tsc) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """.format(*[domain]*4), (id_bigram, w3, colloc_freq, logdsc, pmisc, tsc))
            except IntegrityError:
                cursor.execute("""
                UPDATE 3grams 
                SET d{}_freq = %s, 
                    d{}_logdice = %s, 
                    d{}_pmi = %s, 
                    d{}_tsc = %s 
                WHERE bigram = %s 
                    AND token = %s
                    """.format(*[domain]*4), (colloc_freq, logdsc, pmisc, tsc, id_bigram, w3))
    if verbose:
        log.debug('3-grams are counted and inserted!')


def fetch_6grams():
    # TODO: унифицировать для всех доменов
    # C:\Users\Eiko\PycharmProjects\cat\MySQL Scripts\fetching_6grams(no_cval).sql
    pass


def get_n_count_4grams(domain, minimum=3):
    """
    Extracts all 4-grams from the texts of the domain and counts frequency and all metrics in this domain for them.
    :param domain: int, domain_id from which you want extract n-grams.
    :param minimum: int, frequency threshold
    :return:
    """
    command = sql('getting_4grams.sql')
    cursor.execute(command, (domain, ))
    data = Counter(cursor.fetchall())
    log.debug('Counted!')

    n = get_domain_size(domain)
    verbose = True

    for ngram in data:
        colloc_freq = data[ngram]
        if colloc_freq >= minimum:
            w1, w2, w3, w4 = ngram
            if verbose:
                log.debug("Started! %s", ngram)

            command = sql('select_to_count_4grams.sql')

            cursor.execute(command.format(domain), (w1, w2, w3))
            id_trigram, pattern_freq = cursor.fetchone()

            cursor.execute("SELECT freq{} FROM unigrams WHERE id_unigram = %s".format(domain), (w4,))
            lw_freq = cursor.fetchone()[0]
            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)
            try:
                cursor.execute(
                    """INSERT INTO 4grams (trigram, token, d{}_freq, d{}_logdice, d{}_pmi, d{}_tsc)
                    VALUES
                    (%s, %s, %s, %s, %s, %s)""".format(*[domain] * 4),
                    (id_trigram, w4, colloc_freq, logdsc, pmisc, tsc))
            except IntegrityError:
                cursor.execute("""UPDATE 4grams SET
                                                d{}_freq = %s, d{}_logdice = %s,
                                                d{}_pmi = %s, d{}_tsc = %s 
                                                WHERE trigram = %s 
                                                    AND token = %s
                                """.format(*[domain] * 4),
                               (
                                colloc_freq,
                                logdsc,
                                pmisc,
                                tsc,
                                id_trigram,
                                w4
                            ))
        if verbose:
            log.debug('Counted and inserted!')
            verbose = False

    log.info('4grams commited!')


def get_n_count_5grams(domain, minimum=3):
    """
    Extracts all 5-grams from the texts of the domain and counts frequency and all metrics in this domain for them.
    :param domain: int, domain_id from which you want extract n-grams.
    :param minimum: int, frequency threshold
    :return:
    """
    command = sql('getting_5grams.sql')
    cursor.execute(command, (domain,))
    data = Counter(cursor.fetchall())
    log.debug('5-grams counted')

    n = get_domain_size(domain)
    for ngram in data:
        colloc_freq = data[ngram]
        if colloc_freq >= minimum:
            w1, w2, w3, w4, w5 = ngram
            log.debug("Started! %s", ngram)

            command = sql('select_to_count_5grams.sql')
            cursor.execute(command.format(domain), (w1, w2, w3, w4))
            id_4gram, pattern_freq = cursor.fetchone()

            cursor.execute("SELECT freq{} FROM unigrams WHERE id_unigram = %s".format(domain), (w5,))
            lw_freq = cursor.fetchone()[0]
            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)
            # print(id_4gram, w5, colloc_freq, logdsc, pmisc, tsc)
            try:
                cursor.execute(
                    """
                    INSERT INTO 5grams (4gram, token, d{}_freq, d{}_logdice, d{}_pmi, d{}_tsc)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """.format(*[domain] * 4), (id_4gram, w5, colloc_freq, logdsc, pmisc, tsc))
            except IntegrityError:
                cursor.execute(
                    """UPDATE 5grams 
                    SET d{}_freq = %s, 
                        d{}_logdice = %s, 
                        d{}_pmi = %s, 
                        d{}_tsc = %s 
                    WHERE 4gram = %s AND token = %s
                    """.format(*[domain] * 4),
                    (colloc_freq, logdsc, pmisc, tsc, id_4gram, w5)
                )

    log.debug('5-grams are counted and inserted!')


def get_n_count_6grams(domain, minimum=3):
    """
    Extracts all 6-grams from the texts of the domain and counts frequency and all metrics in this domain for them.
    :param domain: int, domain_id from which you want extract n-grams.
    :param minimum: int, frequency threshold
    :return:
    """
    command = sql('getting_6grams.sql')
    cursor.execute(command, (domain,))
    data = Counter(cursor.fetchall())
    log.debug('Counted!')

    n = get_domain_size(domain)
    verbose = True

    for ngram in data:
        colloc_freq = data[ngram]
        if colloc_freq >= minimum:
            w1, w2, w3, w4, w5, w6 = ngram
            if verbose:
                log.debug("Started! %s", ngram)

            command = sql('select_to_count_6grams.sql')
            cursor.execute(command.format(domain), (w1, w2, w3, w4, w5))
            id_5gram, pattern_freq = cursor.fetchone()

            cursor.execute("SELECT freq{} FROM unigrams WHERE id_unigram = %s".format(domain), (w6,))
            lw_freq = cursor.fetchone()[0]
            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)

            # print(id_4gram, w5, colloc_freq, logdsc, pmisc, tsc)
            try:
                cursor.execute(
                    """
                    INSERT INTO 6grams (5gram, token, d{}_freq, d{}_logdice, d{}_pmi, d{}_tsc)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """.format(*[domain] * 4), (id_5gram, w6, colloc_freq, logdsc, pmisc, tsc))

            except IntegrityError:
                cursor.execute(
                    """
                    UPDATE 6grams 
                        SET d{}_freq = %s, 
                            d{}_logdice = %s, 
                            d{}_pmi = %s, 
                            d{}_tsc = %s 
                        WHERE 5gram = %s 
                            AND token = %s
                    """.format(*[domain] * 4), (colloc_freq, logdsc, pmisc, tsc, id_5gram, w6))
        if verbose:
            log.debug('Counted and inserted!')
            verbose = False

    # log.info('6grams commited!')


def search_bigr_by_lemma(lemma, morph=None, pos=None):
    # TODO: переделать для скорости и новой структуры или выкинуть
    command = """SELECT unigram, morph, raw_frequency, lemmas.lemma, pos FROM (SELECT * FROM (SELECT wordform_2, raw_frequency FROM 2grams, unigrams, lemmas WHERE wordform_1 = unigrams.id_unigram
            AND unigrams.lemma = lemmas.id_lemmas
            AND lemmas.lemma = (%s)) AS bigr
    JOIN unigrams
    HAVING id_unigram = wordform_2) AS res,
    lemmas, pos WHERE
    res.lemma = lemmas.id_lemmas
        AND lemmas.id_pos = pos.id_pos
ORDER BY raw_frequency DESC LIMIT 0 , 1000
"""
    if morph and pos:
        morph = '%{}%'.format(morph)
        command = """SELECT unigram, morph, raw_frequency, pos FROM ({}) AS result WHERE pos LIKE (%s) AND morph LIKE (%s)""".format(
            command)
        print(command)
        cursor.execute(command, (lemma, pos, morph))
    else:
        cursor.execute(command, (lemma,))
    result = cursor.fetchall()
    return result


def get_domain_size(domain):
    """
    Counts all tokens (including symbols, punctuation and digits) in the domain.
    :param domain: int, id of domain
    :return:
    """
    cursor.execute(
        """
        SELECT COUNT(*)
            FROM
                (SELECT id_word
                    FROM
                        words, metadata
                    WHERE
                        words.id_text = metadata.id_text
                        AND metadata.id_domain = (%s)
                ) AS sd
        """, (domain,))

    n = cursor.fetchone()[0]

    log.info('Domain %s size %s', domain, n)
    return n


def fetch_3grams(domain):
    command = sql('fetching_3grams.sql')
    cursor.execute(command.format(*[domain]*7))
    data = cursor.fetchall()
    with open('trigrams_d{}.csv'.format(domain), 'a', encoding='utf-8') as f:
       for line in data:
           line = [str(i) for i in line]
           f.write('\t'.join(line) + '\n')


def create_token_tables():
    """
    Creates tables like w1, w2, ... wN).
    If you need to work with tokens in a collocation and it is not about (last word) and (other words),
     you might need a table, which contains all collocations in token by token format. So, here it is.

     Frequency threshold for bigrams is 10, minimum t-score value is 2.576.

    :return:
    """
    commands = ["drop tables if exists 3grams_tokens, 4grams_tokens, 5grams_tokens, 6grams_tokens"]
    for i in range(3, 7):
        with open(os.path.join('MySQL Scripts', 'create_{}grams_tokens.sql'.format(str(i))),
                  'r',
                  encoding='utf-8') as f:
            command = f.read()
        commands.append(command)

    for command in commands:
        cursor.execute(command)


def c_val_5grams(domain):
    """
    Counts c-value for all 5-grams in the domain.
    :param domain: int, id of domain
    :return:
    """

    log.info('cvaluation started')
    command = sql('cval_5grams.sql').format(*[domain]*3)
    cursor.execute(command)
    data = cursor.fetchall()
    log.info('fetched!')

    for line in data:
        log.debug('Start counting for one')
        if line[-1]:
            c_val = c_value(5, *line[1:])
            # print(line, c_val)
            cursor.execute("UPDATE 5grams SET d{}_cval = (%s) WHERE id_5gram = (%s)".format(domain), (c_val, line[0]))

    log.info('5grams updated: c-value scored')


def c_val_4grams(domain):
    """
    Counts c-value for all 4-grams in the domain.
    :param domain: int, id of domain
    :return:
    """

    command = sql('cval_4grams.sql').format(*[domain]*5)
    cursor.execute(command)
    data = cursor.fetchall()
    log.info('fetched!')

    for line in data:
        c_val = c_value(4, *line[1:])
        cursor.execute("UPDATE 4grams SET d{}_cval = (%s) WHERE id_4gram = (%s)".format(domain), (c_val, line[0]))

    log.info('4grams updated: c-value scored')


def c_val_3grams(domain):
    """
    Counts c-value for all 3-grams in the domain.
    :param domain: int, id of domain
    :return:
    """

    log.info('Start calculating c-value for trigrams')

    command = sql('cval_3grams.sql').format(*[domain]*8)
    cursor.execute(command)

    data = cursor.fetchall()
    log.info('fetched!')

    for line in data:

        if line[-1]:
            c_val = c_value(3, *line[1:])
            # print(line, c_val)
            cursor.execute("UPDATE 3grams SET d{}_cval = (%s) WHERE id_trigram = (%s)".format(domain), (c_val, line[0]))

    log.info('3grams updated: c-value scored')


def c_val_2grams(domain):
    """
    Counts c-value for all 2-grams in the domain.
    :param domain: int, id of domain
    :return:
    """

    command = sql('cval_2grams.sql').format(*[domain]*15)
    cursor.execute(command)

    data = cursor.fetchall()
    log.info('fetched!')
    for line in data:
        if line and line[-1]:
            c_val = c_value(2, *line[1:])
            # print(line, c_val)
            cursor.execute("UPDATE 2grams SET d{}_cval = (%s) WHERE id_bigram = (%s)".format(domain), (c_val, line[0]))

    log.info('2grams updated: c-value scored')


def fetch_cvalued_3grams(domain):
    """
    Returns a tab-separated .csv with all 3grams in the domain with all scores and POS-tags of the collocates.
    :param domain: int, the id of the domain
    :return:
    """
    try:
        cursor.execute("""ALTER TABLE `cat`.`3grams` 
                            ADD INDEX `d{}_logdice_desc` (`d{}_logdice` DESC) VISIBLE""".format(*[domain]*2))
    except ProgrammingError:
        pass

    cursor.execute(sql('fetching_cvalued_3grams.sql').format(*[domain]*11))
    with open('d{}_3grams_cvalued.csv'.format(domain), 'a', encoding='utf-8') as f:
        f.write('\t'.join(
            ['id_trigram',
             'w1', 'pos1',
             'w2', 'pos2',
             'w3', 'pos3',
             'd{}_freq'.format(domain),
             'd{}_pmi'.format(domain),
             'd{}_logdice'.format(domain),
             'd{}_t-score'.format(domain),
             'd{}_c-value'.format(domain)]) + '\n')
        for line in cursor:
            value = [str(i) for i in line]
            f.write('\t'.join(value) + '\n')


def fetch_cvalued_2grams(domain):
    """
    Returns a tab-separated .csv with all bigrams in the domain with all scores and POS-tags of the collocates.
    :param domain: int, the id of the domain
    :return:
    """

    cursor.execute(sql('fetching_cvalued_2grams.sql').format(*[domain]*17))
    with open('d{}_2grams_cvalued.csv'.format(domain), 'a', encoding='utf-8') as f:
        f.write('\t'.join(
            ['id_bigram',
             'w1', 'pos1',
             'w2', 'pos2',
             'd{}_freq'.format(domain),
             'd{}_pmi'.format(domain),
             'd{}_logdice'.format(domain),
             'd{}_t-score'.format(domain),
             'd{}_c-value'.format(domain)]) + '\n')

        for line in cursor:
            value = [str(i) for i in line]
            f.write('\t'.join(value) + '\n')


def fetch_cvalued_2grams_which_in_3grams():
    """
    A function which extracts bigrams which are parts of 3-grams to create a list for students to annotate.
    The main purpose of this list and annotation is to find an optimal c-value threshold
    :return:
    """

    cursor.execute(sql('fetching_cvalued_2grams_in_3grams.sql'))

    with open('Law_2grams_in_trigrams.csv', 'a', encoding='utf-8') as f:
        f.write('\t'.join(
            ['id_bigram',
             'w1', 'pos1',
             'w2', 'pos2',
             '3w1', '3w1_pos',
             '3w2', '3w2_pos',
             '3w3', '3w3_pos',
             'id_trigram',
             'd2_freq',
             'd2_pmi',
             'd2_logdice',
             'd2_t-score',
             'd2_c-value']) + '\n')
        for line in cursor:
            value = [str(i) for i in line]
            f.write('\t'.join(value) + '\n')


def fetch_cvalued_4grams(domain):
    try:
        cursor.execute("""ALTER TABLE `cat`.`4grams` 
                            ADD INDEX `d{}_logdice_desc` (`d{}_logdice` DESC) VISIBLE""".format(*[domain]*2))
    except ProgrammingError:
        pass
    cursor.execute(sql('fetching_cvalued_4grams.sql').format(*[domain]*11))
    with open('d{}_4grams_cvalued.csv'.format(domain), 'a', encoding='utf-8') as f:
        f.write('\t'.join(
            ['id_4gram',
             'w1', 'pos1',
             'w2', 'pos2',
             'w3', 'pos3',
             'w4', 'pos4',
             'd{}_freq'.format(domain),
             'd{}_pmi'.format(domain),
             'd{}_logdice'.format(domain),
             'd{}_t-score'.format(domain),
             'd{}_c-value'.format(domain)]) + '\n')
        for line in cursor:
            row = [str(i) for i in line]
            f.write('\t'.join(row) + '\n')


def count_all_domains_bigr(minimum=1):
    """

    :param minimum: n occurences per million
    :return:
    """

    log.info('Counting metrics!')
    cursor.execute(
        """
        SELECT 
            COUNT(*)
        FROM
            (SELECT 
                id_word
            FROM
                words) 
            as a
        """)
    n = cursor.fetchone()[0]
    log.info('Total corpus size %s', n)

    cursor.execute(sql('selecting_all_2grams.sql'))
    log.debug('Selected!')
    data = set()
    for _id, colloc_freq, pattern_freq, lw_freq in cursor:

        if colloc_freq/(n/1000000) >= minimum:
            pmisc = pmi(colloc_freq, pattern_freq, lw_freq, n)
            tsc = t_score(colloc_freq, pattern_freq, lw_freq, n)
            logdsc = logDice(colloc_freq, pattern_freq, lw_freq)

            data.add((logdsc, pmisc, tsc, _id))
        # log.debug('Counted %s', _id)
    log.info('Ready to insert')
    for i in data:
        cursor.execute(
            """
            UPDATE 2grams 
                SET 
                    logdice = %s,
                    pmi = %s,
                    tscore = %s
                WHERE
                    id_bigram = %s 
            """, i)
    cnx.commit()
    log.info('Metrics for bigram in all corpus are commited!')


def change_date():
    cursor.execute("insert into lemmas value (0, '<DATE>', 528, 0,0,0,0,0,0, 0)")


def main():
    # write_meta('Meta_Law.csv', 2)
    # write_meta('4', cursor)
    # cnx.commit()
    # conlls = [os.path.join('3', i) for i in os.listdir('3') if i.endswith('conllu')] + [os.path.join('4', i) for i in os.listdir('4') if i.endswith('conllu')]
    # for i in conlls:
    #   write_text(i)
    # delete_text(38)
    # count_bigrams()

    # print(search_bigr_by_lemma('в', morph='Acc', pos='NOUN'))
    # print(get_lemma_id('примерпримерпримерлеммы', '1'))
    # for text in os.listdir('Law_parsed'):
    #        write_text(os.path.join('Law_parsed', text), 2)
    # write_text(os.path.join('Law_parsed', '123.conllu'), 2)
    # count_bigrams(2)
    #count_2metrics(2)
    # get_n_count_6grams(2)
    #c_val_2grams()

    #fetch_cvalued_2grams()
    #for root, dirs, files in os.walk('corpus'):
     #   for d in dirs:
      #      for fn in os.listdir(os.path.join(root, d)):
       #         if fn.endswith('conllu'):
        #            if d == '1' and fn[:-7] < '54':
         #               continue
          #          else:
           #             write_text(os.path.join(root, d, fn), d, cursor, cnx)
    #count_bigrams(1, 3)
    #count_bigrams(1, 3)
    #fetch_cvalued_2grams_which_in_3grams()
    for i in [1, 3, 4, 5, 6]:
        if i:
            print(i)
            fetch_cvalued_4grams(i)
    #    count_2metrics(i)
    #    get_n_count_3grams(i)
    #    get_n_count_4grams(i)
    #    get_n_count_5grams(i)
    #    get_n_count_6grams(i)
    #create_token_tables()
    #count_all_domains_bigr()

    cnx.commit()




if __name__ == "__main__":
    main()

cursor.close()
cnx.close()
