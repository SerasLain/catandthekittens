import os
from find_mistakes.search import parse_file
from find_mistakes.search_for_shit import Searcher


# TODO: нормальный тест с ассертами (хотя не верю, что когда-то будет на это время)
def test_i_vs_we():
    for file in os.listdir("../../marked/Лингвистика"):
        tree = parse_file(os.path.join("../../marked/Лингвистика", file))
        searcher = Searcher()
        searcher.i_vs_we(tree, file)
        for key, val in searcher.found['i vs we'].items():
            print(key, val)


if __name__ == '__main__':
    test_i_vs_we()
