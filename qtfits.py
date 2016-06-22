import sys
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap


class Viewer(QWidget):

    def __init__(self):
        super(Viewer, self).__init__()

        self.setWindowTitle('Tester')
        self.resize(200, 200)
        self.center()
        self.display()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def display(self):
        #test = (np.random.rand(100,100,3)*255).astype(np.uint8)
        test = np.zeros((200, 200, 3))
        test[...,0] = 1
        test = (test*255).astype(np.uint8)
        print(test)
        height, width, channel = test.shape
        linebytes = 3*width
        self.image = QImage(test.data, width, height, linebytes, QImage.Format_RGB888)
        self.pixmap = QPixmap(self.image)

        hbox = QHBoxLayout(self)

        lbl = QLabel(self)
        lbl.setPixmap(self.pixmap)

        hbox.addWidget(lbl)
        self.setLayout(hbox)




if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = Viewer()
    w.show()

    sys.exit(app.exec_())
