import re
import os
from mysql.connector.errors import IntegrityError, DataError, InternalError
from k import USER, PASS
import logging
import mysql.connector
import csv

logging.basicConfig(filename="CAT_database.log",
                    level=logging.DEBUG,
                    format='%(levelname)s %(name)s %(asctime)s : %(message)s')
log = logging.getLogger("database_adding")

# cnx = mysql.connector.connect(user=USER, password=PASS,
#                              host='127.0.0.1',
#                             database='cat')

# cursor = cnx.cursor()


def load_pos(cnx):
    """
    Fetch pos-tags from db into dictionary
    :param cnx: db connection
    :return: dict of pos, {pos_tag:id_pos}
    """
    c = cnx.cursor()
    c.execute("SELECT * FROM pos")
    pos_dict = {}
    for t in c.fetchall():
        pos_dict[t[1]] = t[0]
    c.close()
    return pos_dict


def get_pos_id(pos, pos_dict, cnx):
    """

    :param pos: str, pos-tag
    :param pos_dict: dictionary of pos, {pos_tag:id_pos}
    :param cnx: db connection
    :return: pos_id
    """
    c = cnx.cursor()
    try:
        pos_id = pos_dict[pos]
    except KeyError:
        c.execute("INSERT INTO `cat`.`pos` (`pos`) VALUE (%s)", (pos,))
        cnx.commit()
        pos_id = c.lastrowid
        pos_dict[pos] = pos_id
    c.close()
    return pos_id


def get_lemma_id(lemma, pos_id, cnx):
    """
    Gets an id of existing lemma or writes a new one
    :param lemma: str
    :param pos_id: int
    :param cnx: db connection
    :return: int, lemma id
    """
    if pos_id == 36:
        lemma_id = 36224
    else:
        c = cnx.cursor()
        c.execute("INSERT IGNORE INTO `cat`.`lemmas` (`lemma`, `id_pos`) VALUES (%s, %s)", (lemma, pos_id,))
        #    cnx.commit()
        if c.lastrowid:
            lemma_id = c.lastrowid
        else:
            c.execute("SELECT id_lemmas FROM cat.lemmas WHERE `id_pos` = (%s) AND `lemma` = (%s)", (pos_id, lemma))
            lemma_id = c.fetchone()[0]
        c.close()
    return lemma_id


def get_wordform_id(wordform, lemma_id, feats, domain_id, cnx):
    """

    :param wordform: str
    :param lemma_id: int
    :param feats: str, morph tagset of the wordform (unigram)
    :param domain_id:
    :param cnx: db connection
    :return: id unigram, int
    """
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`unigrams` (`unigram`, `lemma`, `morph`) VALUES (%s, %s, %s)",
              (wordform, lemma_id, feats))
    #    cnx.commit()
    if c.lastrowid:
        unigram_id = c.lastrowid
    else:
        c.execute("SELECT id_unigram FROM cat.unigrams WHERE `lemma` = (%s) AND `morph` = (%s) AND `unigram` = (%s)",
                  (lemma_id, feats, wordform))
        unigram_id = c.fetchone()[0]

    c.execute("UPDATE `cat`.`unigrams` SET `freq_all` = `freq_all` + 1 WHERE `id_unigram`=(%s)", (unigram_id,))
    c.execute("UPDATE `cat`.`unigrams` SET freq{} = freq{} + 1 WHERE `id_unigram`=(%s)".format(domain_id, domain_id),
              (unigram_id,))
    #    cnx.commit()
    c.close()
    return unigram_id


def get_syntrel_id(rel, cnx):
    """

    :param rel: str
    :param cnx: db connection
    :return: id of syntactic relation, int
    """
    c = cnx.cursor()
    c.execute("INSERT IGNORE INTO `cat`.`syntroles` (`syntrole`) VALUES (%s)",
              (rel,))
    #    cnx.commit()
    c.execute("SELECT id_synt_role FROM cat.syntroles WHERE `syntrole` = (%s)",
              (rel,))
    syntrole_id = c.fetchone()[0]

    c.close()
    return syntrole_id


def write_meta(meta, cursor, cnx):
    """
    :param meta: str, path to file with metadata: comma-separated, " as quotechar.
    :param cursor: db cursor
    :param cnx: db connection
    Format: id in domain, domain_name, genre_name, title, author, source, year
    """
    log.info('Writing meta')
    cursor.execute("SELECT * FROM cat.domains")
    domain_map = {i[1]: i[0] for i in cursor}
    cursor.execute("SELECT * FROM cat.genres")
    genres_map = {i[1]: i[0] for i in cursor}

    with open(os.path.join(meta), 'r', encoding='utf-8') as f:
        print(meta)
        meta = csv.reader(f, delimiter=';', quotechar='"')
        meta_p = []
        for _id, line in enumerate(meta):
            print(line)
            if line and _id != 0:
                id_in_dom, domain, genre, title, author, source, year = line
                if id_in_dom == '':
                    continue
                domain = domain_map[domain]
                genre = genres_map[genre]
                meta_p.append([domain, id_in_dom, title, author, source, year, genre])

    for article in meta_p:
        command = (
            "INSERT IGNORE INTO `cat`.`metadata` (`id_domain`, `id_in_domain`, `title`, `author`, `source`,"
            " `year`, `genre`) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(command, article)
    cnx.commit()
    log.info("Meta commited")


def write_relations(pairs, text_id, c):
    #c = cnx.cursor()
    for sent_id, head_position, dependent_position, rel in pairs:
        word_by_position = "SELECT `id_word` FROM `cat`.`words` WHERE `id_text`=(%s) AND `id_sent`=(%s) AND `id_position`=(%s)"
        c.execute(word_by_position, (text_id, sent_id, head_position))
        head_id = c.fetchone()[0]
        try:
            c.execute(word_by_position, (text_id, sent_id, dependent_position))
        except InternalError:
            print(c.fetchall(), (text_id, sent_id, dependent_position))
            break
        try:
            dependent_id = c.fetchone()[0]
        except TypeError:
            print((text_id, sent_id, dependent_position))
            break

        c.execute("INSERT INTO `cat`.`wordpairs` (`head_id`, `dependent_id`, `synt_role_id`) VALUES (%s, %s, %s)",
                  (head_id, dependent_id, rel))
    #cnx.commit()
    #c.close()


def parsing_conllu(path, domain_id, pos_dict, cursor, cnx):
    with open(path, 'r', encoding='utf-8') as f:
        conl = f.read().split('\n\n')
    log.debug("%s sentences in the text", len(conl))
    data = []
    pairs = []
    for _, sent in enumerate(conl):
        # log.debug("Writing %s", _)
        s = [i for i in sent.split('\n') if i and ((not i.startswith('#')) or i.startswith('# sent_id'))]
        print(len(s))
        sent_id = 0
        for tokenline in s:
            if tokenline.startswith('#'):
                sent_id = tokenline.split(' ')[-1]
            else:
                position, wordform, lemma, pos, _, feats, head_position, rel, misc, comm = tokenline.split('\t')
                if pos == 'NUM':
                    unigram_id = 36215
                    cursor.execute("UPDATE `cat`.`unigrams` SET `freq_all` = `freq_all` + 1 WHERE `id_unigram`=(%s)",
                                   (unigram_id,))
                    cursor.execute(
                        "UPDATE `cat`.`unigrams` SET freq{} = freq{} + 1 WHERE `id_unigram`=(%s)".format(domain_id,
                                                                                                         domain_id),
                        (unigram_id,))
                elif re.search('[a-zA-Z]+\.[a-z]+/', wordform):
                    log.warning('URL found! %s', wordform)
                    unigram_id = 47683
                    cursor.execute("UPDATE `cat`.`unigrams` SET `freq_all` = `freq_all` + 1 WHERE `id_unigram`=(%s)",
                                   (unigram_id,))
                    cursor.execute(
                        "UPDATE `cat`.`unigrams` SET freq{} = freq{} + 1 WHERE `id_unigram`=(%s)".format(domain_id,
                                                                                                         domain_id),
                        (unigram_id,))
                    wordform = '<URL>'
                elif len(wordform) > 45:
                    log.warning('Long word! %s', wordform)
                    wordform = '<URL>'
                    unigram_id = 47683

                else:
                    unigram = wordform.strip('.*>?!»«-')
                    pos_id = get_pos_id(pos, pos_dict, cnx)
                    lemma_id = get_lemma_id(lemma, pos_id, cnx)
                    unigram_id = get_wordform_id(unigram, lemma_id, feats, domain_id, cnx)

                token_data = [sent_id, position, wordform, unigram_id]
                if head_position == '0':
                    rel = 'root'
                    rel_id = get_syntrel_id(rel, cnx)
                    pairs.append([sent_id, position, position, rel_id])
                else:
                    rel_id = get_syntrel_id(rel, cnx)

                    pairs.append([sent_id, head_position, position, rel_id])
                data.append(token_data)
    # cnx.commit()
    log.info('wordforms commited')
    return data, pairs


def write_text(path, domain, cursor, cnx):
    """

    :param path: directory with conllu of domain, str
    :param domain: id domain, int
    :param cursor: db cursor
    :param cnx: db connection
    :return:
    """
    pos_dict = load_pos(cnx)
    id_in_domain = os.path.split(path)[-1][:-7]
    log.info('start!')
    cursor.execute("SELECT id_text FROM cat.metadata WHERE id_domain = (%s) AND id_in_domain = (%s)",
                   (domain, id_in_domain))
    log.info('Writing text number %s in domain %s', id_in_domain, domain)
    try:
        text_id = cursor.fetchone()[0]
    except TypeError:
        log.info('No meta in DB for this text')
        cursor.execute("INSERT INTO `cat`.`metadata` (`id_domain`, `id_in_domain`) VALUES (%s, %s)",
                       (str(domain), str(id_in_domain)))
        # cnx.commit()
        text_id = cursor.lastrowid
    log.info('Text id %s', text_id)
    data, pairs = parsing_conllu(path, domain, pos_dict, cursor, cnx)
    log.debug('Data length %s', len(data))
    for token in data:
        token.append(text_id)
        try:
            command = "INSERT INTO `cat`.`words` (`id_sent`, `id_position`, `word`, `id_unigram`, `id_text`) VALUES (%s, %s, %s, %s, %s);"
            cursor.execute(command, token)
            # cnx.commit()
        except IntegrityError as e:
            log.debug("Fail! %s while handling %s", e, token)
            pass
        except DataError as e:
            log.debug("Fail! %s while handling %s", e, token)
            pass
    write_relations(pairs, text_id, cursor)
    cnx.commit()
    log.info('Relations added')


def main():
    print('smth')
    # meta = os.listdir('meta')
    # for name in meta:
    #     if not name.startswith('Meta_Law'):
    #         write_meta(os.path.join('meta', name), cursor, cnx)


if __name__ == "__main__":
    main()

#cnx.commit()
#cursor.close()
#cnx.close()
