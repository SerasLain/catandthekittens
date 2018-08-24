import logging

CONTENTS = {'содержание', 'оглавление'}
INTRODUCTION = 'введение'
CONCLUSIONS = {'заключение', 'выводы'}
REFERENCES_FIRST = {'список', 'использованный'}
REFERENCES_LITERATURE = {'литература', 'источник'}
REFERENCES_USED = {'использованный'}


class CheckStructure():
    """
    Проверка наличия введения, содержания, заключения и списка литературы
    """
    def __init__(self):
        self.contents = None
        self.introduction = None
        self.conclusions = None
        self.references = None

    def check_chapter(self, tree):
        for i, x in enumerate(tree):
            for j, word in enumerate(x):
                if not self.contents:
                    if word['form'].lower() in CONTENTS:
                        self.contents = (word['form'], i)
                if not self.introduction:
                    if word['form'].lower() == INTRODUCTION:
                        self.introduction = (word['form'], i)
                if not self.conclusions:
                    if word['form'].lower() in CONCLUSIONS:
                        self.conclusions = (word['form'], i)
                if not self.references:
                    if j > 1:
                        if (x[j - 2]['lemma'] in REFERENCES_FIRST and x[j - 1]['lemma'] in REFERENCES_LITERATURE):
                            self.references = (x[j - 1]['form'], x[j]['form'], i)
                        elif (x[j - 2]['lemma'] in REFERENCES_FIRST and x[j - 1]['lemma'] in REFERENCES_USED
                              and x[j]['lemma'] in REFERENCES_LITERATURE):
                            self.references = (x[j - 2]['form'], x[j - 1]['form'], x[j]['form'], i)

    def check_position(self):
        logging.basicConfig(level=logging.WARNING)
        if self.conclusions[-1] < self.introduction[-1]:
            logging.warning("Заключение раньше введения")
        if self.references[-1] < self.conclusions[-1]:
            logging.warning("Список литературы раньше заключения")
        if self.contents[-1] > self.introduction or self.contents[-1] < self.conclusions:
            logging.warning("Содержание не в начале и не в конце текста")

    def check_existence(self, genre):
        logging.basicConfig(level=logging.WARNING)
        if not self.introduction:
            logging.warning("Нет введения")
        if not self.conclusions:
            logging.warning("Нет заключения")
        if not self.references:
            logging.warning("Нет списка литературы")
        if genre != "статья" and not self.contents:
            logging.warning("Нет оглавления")


