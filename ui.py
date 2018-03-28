import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import mysql.connector as mysql


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def showDialog(self, flag):
        if flag == 1:
            number, ok = QInputDialog.getInt(self, 'CAT metadata',
                                            'How many metadata to show?')

            if ok:
                return number

        elif flag == 2:
            text, ok = QInputDialog.getText(self, 'CAT articles',
                                            'What author?')

            if ok:
                return text

        elif flag == 3:
            text, ok = QInputDialog.getText(self, 'CAT articles',
                                            'What part of speech?')

            if ok:
                return text

    def connect_to_db(self, flag, cur):

        if flag == 1:
            cur.execute("SELECT * FROM meta_cat LIMIT 0, {0}".format(self.showDialog(flag)))
        elif flag == 2:
            cur.execute("SELECT word FROM words_cat WHERE id_text = (SELECT id_text FROM meta_cat"
                        " WHERE author LIKE '%{0}%')".format(self.showDialog(flag)))
        elif flag == 3:
            cur.execute("SELECT word FROM words_cat WHERE POS_tag LIKE '{0}' LIMIT 10".format(self.showDialog(flag)))
        data = cur.fetchall()
        data_list = list(data[0].values())
        for item in data_list:
            self.textBox.append(str(item))

    def handleButton1(self):
        self.connect_to_db(1,self.cur)

    def handleButton2(self):
        self.connect_to_db(2,self.cur)

    def handleButton3(self):
        self.connect_to_db(3,self.cur)

    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')

        self.textBox = QTextEdit(self)
        self.textBox.move(0, 30)
        self.textBox.resize(355,270)

        con = mysql.connect(host='127.0.0.1', database='cat_scheme', user='root', password='')
        self.cur = con.cursor(dictionary=True)

        btn = QPushButton('Show article metadata', self)
        btn.setToolTip('This is a <b>QPushButton</b> widget')
        btn.resize(btn.sizeHint())
        btn.clicked.connect(self.handleButton1)

        btn1 = QPushButton('Search by author', self)
        btn1.resize(btn.sizeHint())
        btn1.move(120,0)
        btn1.clicked.connect(self.handleButton2)

        btn2 = QPushButton('Search by tag', self)
        btn2.resize(btn.sizeHint())
        btn2.move(240, 0)
        btn2.clicked.connect(self.handleButton3)

        self.setGeometry(300, 300, 355, 300)
        self.setWindowTitle('CAT')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
