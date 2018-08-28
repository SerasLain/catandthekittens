import pymysql
import pandas as pd
import argparse

"""
Забирает из КРУТа тексты по указанным доменам.
Домены, которые нам интересны: социолог, лингвист, историк, политолог, психолог, экономист, юрист
"""
parser = argparse.ArgumentParser()
parser.add_argument('domain', default=None)
domain = parser.parse_args().domain
connection = pymysql.connect(host='localhost',
                             user='cat',
                             password='12345678',
                             db='learner_corpus_backup',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
sql = (
    "SELECT data, tag, start, end, annotator_sentence.text, annotator_sentence.tagged FROM annotator_annotation INNER JOIN annotator_sentence ON annotator_annotation.document_id = annotator_sentence.id")
if domain:
    sql = (
        "SELECT distinct data, tag, start, end, annotator_sentence.text, annotator_sentence.tagged, annotator_document.id, annotator_sentence.id FROM annotator_annotation INNER JOIN annotator_sentence ON annotator_annotation.document_id = annotator_sentence.id INNER JOIN annotator_token ON annotator_sentence.id = annotator_token.sent_id INNER JOIN annotator_document ON annotator_document.id = annotator_token.doc_id WHERE title LIKE '%{0}%'".format(
            domain))
cs = connection.cursor()
cs.execute(sql)
result = cs.fetchall()
df = pd.DataFrame(result)
if not domain:
    df.to_csv('data.csv')
else:
    df.to_csv('{0}.csv'.format(domain))
