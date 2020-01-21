import mysql.connector
import os


cnx = mysql.connector.connect(user='user', password='KMnO4',
                              host='127.0.0.1',
                              database='cat')

cursor = cnx.cursor()


def get_pos_id(pos):
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`pos` (`pos`) VALUE (%s)", (pos,))
    cnx.commit()
    c.execute("SELECT id_pos FROM cat.pos WHERE `pos` = (%s)", (pos,))
    pos_id = c.fetchone()[0]
    c.close()
    return pos_id


def get_lemma_id(lemma, pos_id):
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`lemmas` (`lemma`, `id_pos`) VALUES (%s, %s)", (lemma, pos_id,))
    cnx.commit()
    c.execute("SELECT id_lemmas FROM cat.lemmas WHERE `id_pos` = (%s) AND `lemma` = (%s)", (pos_id, lemma))
    lemma_id = c.fetchone()[0]
    c.close()
    return lemma_id


def get_wordform_id(wordform, lemma_id, feats):
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`unigrams` (`unigram`, `lemma`, `morph`) VALUES (%s, %s, %s)", (wordform, lemma_id, feats))
    cnx.commit()
    c.execute("SELECT id_unigram FROM cat.unigrams WHERE `lemma` = (%s) AND `morph` = (%s) AND `unigram` = (%s)", (lemma_id, feats, wordform))
    unigram_id = c.fetchone()[0]
    c.execute("UPDATE `cat`.`unigrams` SET `freq` = `freq` + 1 WHERE `id_unigram`=(%s)", (unigram_id, ))
    cnx.commit()
    c.close()
    return unigram_id


def get_syntrel_id(rel):
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`syntroles` (`syntrole`) VALUES (%s)",
              (rel, ))
    cnx.commit()
    c.execute("SELECT id_synt_role FROM cat.syntroles WHERE `syntrole` = (%s)",
              (rel, ))
    syntrole_id = c.fetchone()[0]

    c.close()
    return syntrole_id


def write_meta(dir, cursor):
    domain = dir[-1]
    with open(os.path.join(dir, 'meta.csv'), 'r', encoding='utf-8') as f:
        meta = f.read()
    meta_p = [line.split('\t') for line in meta.split('\n') if line]

    for i, title in enumerate(meta_p):
        if i == 0:
            continue
        command = ("INSERT IGNORE INTO `cat`.`metadata` (`id_domain`, `id_in_domain`, `year`, `author`, `source`, `title`, `genre`) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(command, [domain] + title)


def write_relations(pairs, text_id):
    c = cnx.cursor()
    for sent_id, head_position, dependent_position, rel in pairs:
        word_by_position = "SELECT `id_word` FROM `cat`.`words` WHERE `id_text`=(%s) AND `id_sent`=(%s) AND `id_position`=(%s)"
        c.execute(word_by_position, (text_id, sent_id, head_position))
        head_id = c.fetchone()[0]
        c.execute(word_by_position, (text_id, sent_id, dependent_position))
        dependent_id = c.fetchone()[0]
        c.execute("INSERT INTO `cat`.`wordpairs` (`head_id`, `dependent_id`, `synt_role_id`) VALUES (%s, %s, %s)", (head_id, dependent_id, rel))
        cnx.commit()
    c.close()


def parsing_conllu(path):
    with open(path, 'r', encoding='utf-8') as f:
        conl = f.read().split('\n\n')
    data = []
    pairs = []
    for sent in conl:
        s = [i for i in sent.split('\n') if i and ((not i.startswith('#')) or i.startswith('# sent_id'))]
        print(len(s))
        sent_id = 0
        for tokenline in s:
            if tokenline.startswith('#'):
                sent_id = tokenline[-1]
            else:
                position, wordform, lemma, pos, _, feats, head_position, rel, misc, comm = tokenline.split('\t')
                unigram = wordform.strip('.*>?!»«-')
                pos_id = get_pos_id(pos)
                lemma_id = get_lemma_id(lemma, pos_id)
                unigram_id = get_wordform_id(unigram, lemma_id, feats)
                token_data = [sent_id, position, wordform, unigram_id]
                if head_position == '0':
                    rel = 'root'
                    rel_id = get_syntrel_id(rel)
                    pairs.append([sent_id, position, position, rel_id])
                else:
                    rel_id = get_syntrel_id(rel)

                    pairs.append([sent_id, head_position, position, rel_id])
                data.append(token_data)
    return data, pairs


def write_text(path):
    folds = os.path.split(path)
    print(folds)
    domain, id_in_domain = folds[-2], folds[-1][:-7]
    cursor.execute("SELECT id_text FROM cat.metadata WHERE id_domain = (%s) AND id_in_domain = (%s);", (domain, id_in_domain))
    text_id = cursor.fetchone()[0]
    data, pairs = parsing_conllu(path)
    print('Data', len(data))
    for token in data:

        token.append(text_id)
        command = "INSERT IGNORE INTO `cat`.`words` (`id_sent`, `id_position`, `word`, `id_unigram`, `id_text`) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(command, token)
        cnx.commit()
    write_relations(pairs, text_id)


def delete_text(text_id):
    c = cnx.cursor()
    c.execute("UPDATE cat.unigrams AS `temp`, (SELECT id_unigram FROM cat.words WHERE id_text = (%s)) AS `cond` SET `temp`.`freq` = `temp`.`freq` - 1 WHERE `temp`.`id_unigram` = `cond`.`id_unigram`;", (text_id, ))
    cnx.commit()
    c.execute("DELETE FROM cat.unigrams WHERE freq=0")
    cnx.commit()
    command = "DELETE FROM cat.metadata WHERE id_text = (%s)"
    c.execute(command, (text_id,))
    cnx.commit()
    c.close()

def count_bigrams():
    cursor.execute("""INSERT INTO bigrams (wordform_1, wordform_2) 
SELECT w1, w2
FROM (SELECT cat.words.id_unigram as w1, word2.id_unigram as w2 
FROM cat.words JOIN (cat.words AS word2) 
WHERE words.id_text=word2.id_text AND words.id_sent=word2.id_sent AND words.id_position + 1 = word2.id_position) 
AS result 
group by w1, w2
ON DUPLICATE KEY UPDATE raw_frequency = raw_frequency + 1""")
    cnx.commit()


def search_bigr_by_lemma(lemma, morph=None, pos=None):
    command = """SELECT unigram, morph, raw_frequency, lemmas.lemma, pos FROM (SELECT * FROM (SELECT wordform_2, raw_frequency FROM bigrams, unigrams, lemmas WHERE wordform_1 = unigrams.id_unigram
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
        command = """SELECT unigram, morph, raw_frequency, pos FROM ({}) AS result WHERE pos LIKE (%s) AND morph LIKE (%s)""".format(command)
        print(command)
        cursor.execute(command, (lemma, pos, morph))
    else:
        cursor.execute(command, (lemma, ))
    result = cursor.fetchall()
    return result


def main():
    #write_meta('3', cursor)
    #write_meta('4', cursor)
    #cnx.commit()
    #conlls = [os.path.join('3', i) for i in os.listdir('3') if i.endswith('conllu')] + [os.path.join('4', i) for i in os.listdir('4') if i.endswith('conllu')]
    #for i in conlls:
     #   write_text(i)
    # delete_text(38)
    #count_bigrams()
    print(search_bigr_by_lemma('в', morph='Acc', pos='NOUN'))







if __name__ == "__main__":
    main()

cursor.close()
cnx.close()


