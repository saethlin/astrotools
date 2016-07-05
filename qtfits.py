"""
TODO:
Histogram sliders
Header display
Toolbar?
"""

import os
import numpy as np
from astropy.io import fits
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer


def zoom(arr, *factors):
    if len(factors) == 1:
        y_zoom = factors[0]
        x_zoom = factors[0]
    else:
        y_zoom = factors[0]
        x_zoom = factors[1]
    if y_zoom == 1 and x_zoom == 1:
        new = arr
    elif y_zoom > 1 and x_zoom > 1:
        factor = int(y_zoom)
        new = np.empty(tuple(np.array(arr.shape)*factor), arr.dtype)
        for x in range(factor):
            for y in range(factor):
                new[x::factor, y::factor] = arr
    else:
        y = np.around(np.linspace(0, arr.shape[0]-1, arr.shape[0]*y_zoom)).astype(np.int32)
        x = np.around(np.linspace(0, arr.shape[1]-1, arr.shape[1]*x_zoom)).astype(np.int32)
        y.shape = (-1, 1)
        x.shape = (1, -1)
        coords = [y, x]
        new = arr[coords]

    return new


class ImageDisplay(QLabel):

    CLIP = 3
    ZOOM = 2
    SLICE = 1

    def __init__(self, minimap):
        super(ImageDisplay, self).__init__()
        self._refresh_queue = 0

        self._image = None
        self._black = None
        self._white = None
        self.zoom = 1

        self.timer = QTimer(self)
        self.timer.setInterval(int(1/60*1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh_display)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.minimap = minimap

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self._image = new
        self._black = np.median(new)
        self._white = np.percentile(self._image, 99.7)
        self.view_y = 0
        self.view_x = 0
        self.minimap.image = new
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

    def increase_zoom(self):
        if self.zoom < 4:
            self.zoom *= 2
            self.refresh_display(ImageDisplay.ZOOM)

    def decrease_zoom(self):
        if self.zoom > 0.125:
            self.zoom /= 2
            if self.view_y + self.height() > self.image.shape[0] * self.zoom:
                self.view_y = self.image.shape[0] * self.zoom - self.height()
            if self.view_x + self.width() > self.image.shape[1] * self.zoom:
                self.view_x = self.image.shape[1] * self.zoom - self.width()

            if self.view_x < 0:
                self.view_x = 0
            if self.view_y < 0:
                self.view_y = 0

            self.refresh_display(ImageDisplay.ZOOM)

    def refresh_display(self, stage=-1):
        if self.timer.remainingTime() == -1:

            stage = max(stage, self._refresh_queue)

            if stage == -1:
                return

            if stage >= ImageDisplay.CLIP:
                clipped = (self.image - self.black).clip(0, self.white-self.black)
                self.scaled = (clipped/clipped.max()*255).astype(np.uint8)
                self.minimap.reclip(self.black, self.white)
            if stage >= ImageDisplay.ZOOM:
                if self.zoom >= 1:
                    self.zoomed = zoom(self.scaled, self.zoom)
                else:
                    self.zoomed = zoom(self.scaled, self.zoom)
            if stage >= ImageDisplay.SLICE:
                self.sliced = self.zoomed[self.view_y:self.height()+self.view_y, self.view_x:self.width()+self.view_x]

            height, width = self.sliced.shape
            image = QImage(bytes(self.sliced.data), width, height, width, QImage.Format_Grayscale8)
            pixmap = QPixmap(image)
            self.setPixmap(pixmap)

            self.minimap.refresh(self.view_y, self.view_x, self.height(), self.width(), self.zoom)

            self._refresh_queue = -1
            self.timer.start()

        else:
            self._refresh_queue = max(self._refresh_queue, stage)

    def keyPressEvent(self, event):
        self.parent.keyPressEvent(event)

    def mousePressEvent(self, event):
        self.last_x = event.x()
        self.last_y = event.y()

    def mouseMoveEvent(self, event):
        last_ypos = self.view_y
        last_xpos = self.view_x
        self.view_y += (self.last_y-event.y())
        self.view_x += (self.last_x-event.x())
        self.last_y = event.y()
        self.last_x = event.x()

        if self.view_y + self.height() > self.image.shape[0]*self.zoom:
            self.view_y = self.image.shape[0]*self.zoom - self.height()
        if self.image.shape[1]*self.zoom - self.view_x < self.width():
            self.view_x = self.image.shape[1]*self.zoom - self.width()

        if self.view_y < 0:
            self.view_y = 0
        if self.view_x < 0:
            self.view_x = 0

        moved = (last_ypos != self.view_y) or (last_xpos != self.view_x)
        if moved:
            self.refresh_display(ImageDisplay.SLICE)


class MiniMap(QLabel):

    SIZE = 200

    def __init__(self):
        super(MiniMap, self).__init__()
        self.conversion = None
        self._image = None
        self.scaled = None
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self.conversion = MiniMap.SIZE/max(new.shape)
        self._image = zoom(new, self.conversion)

    def reclip(self, black, white):
        clipped = (self.image - black).clip(0, white - black)
        self.scaled = (clipped / clipped.max() * 255).astype(np.uint8)

    def refresh(self, y, x, height, width, zoom):
        stack = np.dstack((self.scaled,) * 3)
        scale = self.conversion / zoom

        top = scale * y
        bot = scale * (y + height)
        if bot > MiniMap.SIZE:
            bot = MiniMap.SIZE
        left = scale * x
        right = scale * (x + width)
        if right > MiniMap.SIZE:
            right = MiniMap.SIZE
        stack[top, left:right, 1] = 255
        stack[bot - 1, left:right, 1] = 255
        stack[top:bot, left, 1] = 255
        stack[top:bot, right - 1, 1] = 255

        height, width, channels = stack.shape
        image = QImage(bytes(stack.data), width, height, 3 * width, QImage.Format_RGB888)
        self.setPixmap(QPixmap(image))


class ImageHistogram(QLabel):

    HEIGHT = 50

    def __init__(self):
        super(ImageHistogram, self).__init__()
        self._image = None
        self.plot = None
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        self._refresh_queue = False
        self.timer = QTimer(self)
        self.timer.setInterval(int(1/60*1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.resizer)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new):
        self._image = new
        screen_width = QDesktopWidget().screenGeometry().width()

        data = new.ravel()
        lower_bound, upper_bound = np.percentile(data[::100], [0.01, 99.95])
        data = data[(data > lower_bound) & (data < upper_bound)]

        # Rescale data
        data -= data.min()
        data *= screen_width/data.max()

        histogram = np.bincount(data.astype(int))[:-1]

        # Smooth out the histogram
        left = np.roll(histogram, -1)
        right = np.roll(histogram, 1)
        peak_mask = (histogram > left) & (histogram > right) & (left > 0) & (right > 0)
        histogram[peak_mask] = ((left + right) / 2)[peak_mask]

        histogram = histogram / histogram.max() * ImageHistogram.HEIGHT

        # Manual plotting
        coords = np.arange(0, ImageHistogram.HEIGHT)[::-1]
        coords = np.repeat(coords[:, np.newaxis], screen_width, axis=1)

        histogram = coords > histogram[np.newaxis, :]

        self.histogram_image = (histogram * 255).astype(np.uint8)

    def resizer(self):
        if self._refresh_queue:
            resized = zoom(self.histogram_image, 1, self.width()/self.histogram_image.shape[1])
            height, width = resized.shape
            image = QImage(bytes(resized), width, height, width, QImage.Format_Grayscale8)
            pixmap = QPixmap(image)
            self.setPixmap(pixmap)
            self._refresh_queue = False

    def resizeEvent(self, event):
        self._refresh_queue = True
        if self.timer.remainingTime() == -1:
            self.resizer()
            self.timer.start()


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


class QtFits(QWidget):

    def __init__(self):
        super(QtFits, self).__init__()

        self.setWindowTitle('QtFits')
        self.resize(800, 500)

        grid = QGridLayout()
        self.setLayout(grid)

        self.mini = MiniMap()
        grid.addWidget(self.mini, 0, 1)

        self.main = ImageDisplay(self.mini)
        grid.addWidget(self.main, 0, 0, 0, 1)

        self.box = DirList(self, os.getcwd())
        grid.addWidget(self.box, 1, 1, 2, 1)

        self.histogram = ImageHistogram()
        grid.addWidget(self.histogram, 2, 0)

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

        self.open('test.fits')

    def open(self, path, hdu=0):
        with open(path, 'rb') as input_file:
            image = fits.open(input_file)[hdu].data.astype(np.float32)
        self.main.image = image
        self.histogram.image = image

    def keyPressEvent(self, event):
        if event.key() in self.handlers:
            handler = self.handlers[event.key()]
            handler()

    def resizeEvent(self, event):
        self.main.refresh_display(ImageDisplay.SLICE)


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    window = QtFits()
    window.show()
    app.exec_()
