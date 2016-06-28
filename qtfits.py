"""
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore

import numpy as np
from astropy.io import fits
from scipy import ndimage


class ImageDisplay(QLabel):

    def __init__(self, parent, image):
        super(ImageDisplay, self).__init__()

        self._image = image.astype(np.float16)
        self._black = 0
        self._white = image.max()
        self._zoom = 1

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self._image = new
        self._black = np.median(new)
        self._white = 1000
        self.refresh()

    @property
    def black(self):
        return self._black

    @black.setter
    def black(self, new):
        self._black = new
        self.refresh()

    @property
    def white(self):
        return self._white

    @white.setter
    def white(self, new):
        self._white = new
        self.refresh()

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, new):
        self._zoom = new
        self.refresh()

    def refresh(self):
        subsection = self.image[:self.height()//self.zoom, :self.width()//self.zoom]
        clipped = (subsection - self.black).clip(0, self.white)
        scaled = (clipped/clipped.max()*255).astype(np.uint8)

        zoomed = ndimage.zoom(scaled, self.zoom, order=0)

        stack = np.dstack((zoomed,)*3)
        height, width, channel = stack.shape
        linebytes = 3*width
        image = QImage(stack.data, width, height, linebytes, QImage.Format_RGB888)
        pixmap = QPixmap(image)
        self.setPixmap(pixmap)





class Viewer(QWidget):

    def __init__(self):
        super(Viewer, self).__init__()

        self.setWindowTitle('Tester')

        self.hbox = QHBoxLayout(self)
        self.main = ImageDisplay(self, np.ones((500, 500)))
        self.hbox.addWidget(self.main)
        self.setLayout(self.hbox)
        self.resize(800, 500)

        self.open(Path('test.fits'))

    def open(self, path, hdu=0):
        with Path(path).open('rb') as input_file:
            image = fits.open(input_file)[hdu].data.astype(np.float16)
        self.main.image = image

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif event.key() == QtCore.Qt.Key_Equal:
            self.main.zoom *= 2
        elif event.key() == QtCore.Qt.Key_Minus:
            self.main.zoom /= 2

    def resizeEvent(self, event):
        self.main.refresh()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Viewer()
    window.show()
    app.exec_()
