import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import mysql.connector as mysql


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def connect_to_db(self):
        con = mysql.connect(host='127.0.0.1', database='cat_scheme', user='root', password='')
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM meta_cat LIMIT 0, 1")
        data = cur.fetchall()
        for item in list(data[0].values()):
            self.textBox.append(str(item))

    def handleButton(self):
        self.connect_to_db()

    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')

        self.textBox = QTextEdit(self)
        self.textBox.move(0, 30)

        btn = QPushButton('Show article metadata', self)
        btn.setToolTip('This is a <b>QPushButton</b> widget')
        btn.resize(btn.sizeHint())
        btn.clicked.connect(self.handleButton)

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('CAT')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
