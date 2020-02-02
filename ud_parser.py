import ufal.udpipe
import os
import logging

logging.basicConfig(filename="CAT_database.log",
                    level=logging.INFO,
                    format='%(levelname)s %(name)s %(asctime)s : %(message)s')
log = logging.getLogger("parser")

model = "russian-syntagrus-ud-2.4-190531.udpipe"

ud_model = ufal.udpipe.Model.load(model)
pipe = ufal.udpipe.Pipeline(ud_model, "tokenize", "tag", "parse", "conllu")


def parsing_files(source_dir, target_dir):
    log.info('Source directory: %s', source_dir)
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
        log.info('Target directory created!')
    log.info('Target directory: %s', target_dir)

    work_to_do = os.listdir(source_dir)
    for f in work_to_do:
        with open(os.path.join(source_dir, f), 'r', encoding='utf-8') as t:
            text = t.read()
        parsed = pipe.process(text)
        with open(os.path.join(target_dir, f[:-3]+"conllu"), 'w', encoding='utf-8') as nt:
            nt.write(parsed)
            log.info('Text %s parsed', f)

    log.info("Parsing completed")


def main():
    parsing_files("Law_cleaned", "Law_parsed")


if __name__ == "__main__":
    main()