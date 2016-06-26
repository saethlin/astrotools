import sys
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap

import numpy as np
from astropy.io import fits


class Viewer(QWidget):

    def __init__(self):
        super(Viewer, self).__init__()

        self.hbox = QHBoxLayout(self)
        self.lbl = QLabel(self)
        self.hbox.addWidget(self.lbl)
        self.setLayout(self.hbox)

        self.data = None
        self.setWindowTitle('Tester')
        self.open('test.fits')


    @profile
    def open(self, path, hdu=0):
        path = Path(path)
        with path.open('rb') as input_file:
            self.data = fits.open(input_file)[hdu].data

        self.clipped = (self.data - np.median(self.data)).clip(0, 1000)
        self.scaled = (self.clipped * 255/self.clipped.max()).astype(np.uint8)

        self.display()

    def display(self):
        stack = np.dstack((self.scaled,)*3)

        height, width, channel = stack.shape
        linebytes = 3*width
        image = QImage(stack.data, width, height, linebytes, QImage.Format_RGB888)
        pixmap = QPixmap(image)

        self.lbl.setPixmap(pixmap)





if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = Viewer()
    w.show()

    sys.exit(app.exec_())
