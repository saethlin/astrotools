"""
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer

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

        self.timer = QTimer(self)
        self.timer.setInterval(int(1/60*1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh_display)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self._image = new
        self._black = np.median(new)
        self._white = np.percentile(self._image, 99.7)
        self.refresh_display(ImageDisplay.CLIP)

    @property
    def black(self):
        return self._black

    @black.setter
    def black(self, new):
        self._black = new
        self.refresh_display(ImageDisplay.CLIP)

    @property
    def white(self):
        return self._white

    @white.setter
    def white(self, new):
        self._white = new
        self.refresh_display(ImageDisplay.CLIP)

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, new):
        self._zoom = new
        self.refresh_display(ImageDisplay.ZOOM)

    def increase_zoom(self):
        if self.zoom < 4:
            self.zoom *= 2

    def decrease_zoom(self):
        if self.zoom > 0.125:
            self.zoom /= 2

    def refresh_display(self, stage=-1):
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

    def keyPressEvent(self, event):
        self.parent.keyPressEvent(event)


class DirList(QListWidget):

    def __init__(self, parent, directory):
        super(DirList, self).__init__()
        self.parent = parent
        self.setFixedWidth(200)

        self.directory = directory
        self.reload_entries()
        self.setCurrentRow(0)

    def reload_entries(self):
        entries = [entry.name for entry in os.scandir(self.directory)
                   if entry.is_dir() or (
                entry.is_file() and entry.name.endswith('.fits')
                   )]

        self.clear()
        self.addItems(entries)
        self.addItem('..')

    def selection_up(self):
        index = self.currentRow() - 1
        if index < 0:
            index = len(self) - 1
        self.setCurrentRow(index)

    def selection_down(self):
        index = self.currentRow() + 1
        if index > len(self) - 1:
            index = 0
        self.setCurrentRow(index)

    def select(self):
        new_path = os.path.join(self.directory, str(self.currentItem().text()))
        if os.path.isdir(new_path):
            self.directory = new_path
            self.reload_entries()
        elif os.path.isfile(new_path):
            self.parent.open(new_path)

    def back(self):
        new_path = os.path.dirname(self.directory)
        if os.path.isdir(new_path):
            self.directory = new_path
            self.reload_entries()

    def keyPressEvent(self, event):
        self.parent.keyPressEvent(event)


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

        self.box = DirList(self, os.getcwd())
        grid.addWidget(self.box, 0, 1)

        self.setFocus()

        self.handlers = dict()
        self.handlers[Qt.Key_Escape] = self.close
        self.handlers[Qt.Key_Equal] = self.main.increase_zoom
        self.handlers[Qt.Key_Minus] = self.main.decrease_zoom
        self.handlers[Qt.Key_Down] = self.box.selection_down
        self.handlers[Qt.Key_Up] = self.box.selection_up
        self.handlers[Qt.Key_Return] = self.box.select
        self.handlers[Qt.Key_Right] = self.box.select
        self.handlers[Qt.Key_Backspace] = self.box.back
        self.handlers[Qt.Key_Left] = self.box.back


    def open(self, path, hdu=0):
        with Path(path).open('rb') as input_file:
            image = fits.open(input_file)[hdu].data.astype(np.float16)
        self.main.image = image

    def keyPressEvent(self, event):
        handler = self.handlers[event.key()]
        handler()

    def resizeEvent(self, event):
        self.main.refresh_display(ImageDisplay.SLICE)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Viewer()
    window.show()
    app.exec_()
