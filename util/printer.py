import sys
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt
from .region import Box, center_box
from threading import Thread
from multiprocessing import Process, Queue


class Canvas(QWidget):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.boxes = []
        t = Thread(target=self.loop)
        t.start()
        self.qp = QPainter()

    def paintEvent(self, event):
        self.qp.begin(self)
        self.qp.setPen(QPen(Qt.red, 8, Qt.SolidLine))
        for b in self.boxes:
            self.qp.drawRect(*b.rect().tuple())
        self.qp.end()

    def loop(self):
        while True:
            self.boxes = self.q.get()
            self.update()


class TransparentWindow(QMainWindow):
    def __init__(self, queue):
        super().__init__()

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self.fullscreen_size = QApplication.desktop().size()
        self.setGeometry(0, 0, self.fullscreen_size.width(), self.fullscreen_size.height())

        self.queue = queue
        self.canvas = Canvas(self.queue)
        self.setCentralWidget(self.canvas)

        self.show()


def draw(q):
    app = QApplication(sys.argv)
    window = TransparentWindow(q)
    window.show()
    app.exec_()


if __name__ == '__main__':
    q = Queue()
    p = Process(target=draw, args=(q, ))
    p.start()

    i = 100
    while True:
        q.put([center_box])
        i += 1
        if i > 1000:
            i = 100
        time.sleep(0.001)

