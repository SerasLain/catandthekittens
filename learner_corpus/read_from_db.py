import pymysql
import pandas as pd
import argparse

"""
Забирает из КРУТа тексты и теги
"""


def query(sql, cs, name):
    cs.execute(sql)
    result = cs.fetchall()
    df = pd.DataFrame(result)
    df.to_csv(name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', default=None)
    domain = parser.parse_args().domain
    connection = pymysql.connect(host='localhost',
                                 user='cat',
                                 password='12345678',
                                 db='learner_corpus_backup',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    cs = connection.cursor()
    sql = (
        "SELECT data, tag, start, end, annotator_sentence.text, annotator_sentence.tagged FROM annotator_annotation INNER JOIN annotator_sentence ON annotator_annotation.document_id = annotator_sentence.id")

    if domain:
        sql = (
            "SELECT distinct data, tag, start, end, annotator_sentence.text, annotator_sentence.tagged, annotator_document.id, annotator_sentence.id FROM annotator_annotation INNER JOIN annotator_sentence ON annotator_annotation.document_id = annotator_sentence.id INNER JOIN annotator_token ON annotator_sentence.id = annotator_token.sent_id INNER JOIN annotator_document ON annotator_document.id = annotator_token.doc_id WHERE title LIKE '%{0}%'".format(
                domain))

        query(sql, cs, '{0}.csv'.format(domain))
    else:
        query(sql, cs, 'data2.csv')

    sql_0 = (
        "SELECT DISTINCT text, tagged, annotated, annotator_document.id, annotator_sentence.id FROM annotator_sentence INNER JOIN annotator_token ON annotator_sentence.id = annotator_token.sent_id INNER JOIN annotator_document ON annotator_document.id = annotator_token.doc_id")
    query(sql_0, cs, 'data3.csv')
    sql_1 = ("SELECT document_id, tag FROM annotator_annotation;")
    query(sql_1, cs, 'tags.csv')
