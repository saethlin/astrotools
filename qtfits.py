"""
Overview:

Change Viewer coordinates:

"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap

import numpy as np
from astropy.io import fits
import scipy.ndimage


class FitsImage(object):

    def __init__(self, path, hdu=0):
        path = Path(path)
        with path.open('rb') as input_file:
            self.data = fits.open(input_file)[hdu].data.astype(np.float16)

        self.scaled = None
        self.clip_bounds = self.data.max(), self.data.min()

    @property
    def clip_bounds(self):
        return self._clip_bounds

    @clip_bounds.setter
    def clip_bounds(self, bounds):
        self._clip_bounds = bounds
        clipped = np.clip(self.data, *self.clip_bounds)
        self.scaled = (clipped * 255/clipped.max()).astype(np.uint8)


class ImageDisplay(object):

    def __init__(self, image):
        self.image = image
        self._view_coordinates = (0, 0)
        self._zoom = 1.

    @property
    def view_coordinates(self):
        return self._view_coordinates

    @view_coordinates.setter
    def view_coordinates(self, coordinates):
        if coordinates != self._view_coordinates:
            self._view_coordinates = coordinates

            # Re-assign pixmap
            stack = np.dstack((self.scaled,) * 3)

            height, width, channel = stack.shape
            linebytes = 3 * width
            image = QImage(stack.data, width, height, linebytes, QImage.Format_RGB888)
            pixmap = QPixmap(image)

            self.lbl.setPixmap(pixmap)

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, new_zoom):
        if new_zoom != self._zoom:
            self._zoom = new_zoom




class Viewer(QWidget):

    def __init__(self):
        super(Viewer, self).__init__()

        self.hbox = QHBoxLayout(self)
        self.lbl = QLabel(self)
        self.hbox.addWidget(self.lbl)
        self.setLayout(self.hbox)

        self.data = None
        self.setWindowTitle('Tester')
        self.image = FitsImage(Path('test.fits'))

    def open(self, path, hdu=0):
        self.image = FitsImage(path, hdu)
        self.refresh_main()

    def refresh_main(self):
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
    app.exec_()
