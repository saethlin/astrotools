"""
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore

import numpy as np
from astropy.io import fits
from scipy import ndimage


class ImageDisplay(QLabel):

    CLIP = 3
    ZOOM = 2
    SLICE = 1

    def __init__(self, image):
        super(ImageDisplay, self).__init__()
        self._refresh_queue = 0

        self._image = image.astype(np.float16)
        self._black = 0
        self._white = image.max()
        self._zoom = 1

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(int(1/60*1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.renew_display)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self._image = new
        self._black = np.median(new)
        self._white = np.percentile(self._image, 99.7)
        self.renew_display(ImageDisplay.CLIP)

    @property
    def black(self):
        return self._black

    @black.setter
    def black(self, new):
        self._black = new
        self.renew_display(ImageDisplay.CLIP)

    @property
    def white(self):
        return self._white

    @white.setter
    def white(self, new):
        self._white = new
        self.renew_display(ImageDisplay.CLIP)

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, new):
        self._zoom = new
        self.renew_display(ImageDisplay.ZOOM)

    def renew_display(self, stage=-1):
        if self.timer.remainingTime() == -1:

            stage = max(stage, self._refresh_queue)

            if stage == -1:
                return

            if stage >= ImageDisplay.CLIP:
                clipped = (self.image - self.black).clip(0, self.white-self.black)
                self.scaled = (clipped/clipped.max()*255).astype(np.uint8)
            if stage >= ImageDisplay.ZOOM:
                self.zoomed = ndimage.zoom(self.scaled, self.zoom, order=0)
            if stage >= ImageDisplay.SLICE:
                self.sliced = self.zoomed[:self.height(), :self.width()]
                self.resize(*self.sliced.shape[::-1])

            stack = np.dstack((self.sliced,)*3)
            height, width, channel = stack.shape
            linebytes = 3*width
            image = QImage(stack.data, width, height, linebytes, QImage.Format_RGB888)
            pixmap = QPixmap(image)
            self.setPixmap(pixmap)

            self._refresh_queue = -1
            self.timer.start()

        else:
            self._refresh_queue = max(self._refresh_queue, stage)


class DirList(QListWidget):

    def __init__(self, directory):
        super(DirList, self).__init__()
        self.directory = directory
        self.setFixedWidth(200)

    def reload_entries(self):
        entries = [entry.name for entry in os.scandir(self.directory)
                   if entry.is_dir() or (
                entry.is_file() and entry.name.endswith('.fits')
                   )]

        self.clear()
        self.addItems(entries)


class Viewer(QWidget):

    def __init__(self):
        super(Viewer, self).__init__()

        self.setWindowTitle('QFits')
        self.resize(800, 500)

        grid = QGridLayout()
        self.setLayout(grid)

        self.main = ImageDisplay(np.ones((500, 500)))
        grid.addWidget(self.main, 0, 0)
        self.open(Path('test.fits'))

        self.box = DirList(os.getcwd())
        grid.addWidget(self.box, 0, 1)
        self.box.reload_entries()

    def open(self, path, hdu=0):
        with Path(path).open('rb') as input_file:
            image = fits.open(input_file)[hdu].data.astype(np.float16)
        self.main.image = image

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif event.key() == QtCore.Qt.Key_Equal:
            print('zoom')
            self.main.zoom *= 2
        elif event.key() == QtCore.Qt.Key_Minus:
            print('zoom')
            self.main.zoom /= 2

    def resizeEvent(self, event):
        self.main.renew_display(ImageDisplay.SLICE)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Viewer()
    window.show()
    app.exec_()
