from PyQt5.QtWidgets import QWidget, QApplication, QPushButton
from PyQt5.QtGui import QPainter, QColor

class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.draw_line = True

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 350, 150)
        self.setWindowTitle('Drawing')

        # Adding button and connecting it to the drawLine function
        self.btn = QPushButton('Delete Line', self)
        self.btn.clicked.connect(self.deleteLine)
        self.btn.resize(self.btn.sizeHint())
        self.btn.move(50, 100)

        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        if self.draw_line:
            self.drawLines(qp)
        qp.end()

    def drawLines(self, qp):
        qp.setPen(QColor(0, 0, 0))
        qp.drawRect(20, 20, 250, 50)

    def deleteLine(self):
        self.draw_line = False
        self.update()  # This will cause a paintEvent and a redraw

def main():
    app = QApplication([])
    ex = Example()
    app.exec_()

if __name__ == '__main__':
    main()