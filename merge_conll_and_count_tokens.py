import argparse
import logging
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='directory with conll files')
    parser.add_argument('domain', help='domain name, e.g. sociology_and_history')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    dir, domain = args.dir, args.domain
    logging.basicConfig(level=logging.INFO)
    marked = 'marked'
    if marked not in os.listdir(os.getcwd()):
        os.mkdir(marked)
    old = os.listdir(dir)
    count = 0
    with open(marked + '/' + domain + '.conll', 'w', encoding='utf-8') as fout:
        for file in old:
            logging.info(file)
            lines = open(dir + '/' + file, encoding='utf-8')
            for line in lines:
                if line != '\n' and line != '\r\n' and line != '':
                    fout.write(line)
                    count += 1
    logging.info('Domain {0} contains {1} tokens'.format(domain, count))
