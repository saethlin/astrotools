#!/usr/bin/env python
"""
A lightweight python-based FITS viewer.

The controls should be self-explatory. If they are not, press ctrl+h for a 
stop-gap and submit an issue. Controls ought to be obvious, help me make them.
This is a program for looking at images, not for doing analysis.

TODO:
Add automatic dependency installation?
Investigate source of pointy histogram
Async histogram?
Sliders and lines don't quite line up with edges of the plot
Clean
"""
from __future__ import division, print_function

import os
import argparse
import bisect

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    import Tkinter as tk
    import tkFileDialog as filedialog

import numpy as np
from PIL import Image
from PIL import ImageTk
from astropy.io import fits

MYNAME = 'viewfits 0.9.1'
EXTENSIONS = ['fit', 'fits', 'FIT', 'FITS']
THUMBSIZE = 200
HEIGHT = 500
WIDTH = 800
HISTOGRAM_HEIGHT = 50


class Viewer(tk.Frame):
    """
    SAMPLE TEXT
    """
    def __init__(self, parent, open_file=None):
        """
        Initalize everything
        """
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.title(MYNAME)

        # Initalize a master frame that holds everything
        self.frame = tk.Frame(self.parent, bg='')
        self.frame.pack(fill=tk.BOTH, expand=1)

        self.imgframe = tk.Frame(self.frame)
        self.imgframe.pack(fill=tk.BOTH, expand=1, side=tk.LEFT, anchor='nw')

        # Label for the main image display
        self.main_image = tk.Canvas(self.imgframe, bg='black', cursor='tcross')
        self.main_image.pack(fill=tk.BOTH, expand=1, anchor='nw')
        self.main_image.image = None
        self.main_image.photo = None

        # Initialize a canvas to hold the histogram image
        self.histogram = tk.Canvas(self.imgframe, bg='black',
                                   height=HISTOGRAM_HEIGHT, highlightthickness=0)
        self.histogram.pack(fill=tk.X)
        self.histogram.image = None
        self.histogram.photo = None

        # Sliders for white/black clipping
        self.sliders = tk.Canvas(self.imgframe, bg='gray', height=10,
                                 highlightthickness=0)
        self.sliders.pack(fill=tk.X)

        # Initalize a frame to the right of the canvas that holds the minimap,
        # and the directory navigation (dirlist)
        self.sideframe = tk.Frame(self.frame, width=THUMBSIZE)
        self.sideframe.pack(fill=tk.Y, side=tk.RIGHT, anchor='ne')

        # Initalize the minimap that shows the entire image, zoomed out
        self.mini_label = tk.Label(self.sideframe, width=THUMBSIZE,
                                   height=THUMBSIZE, bg='black')
        self.mini_label.pack(side=tk.TOP)
        self.mini_label.photo = None

        # Add a label to display the cursor location and value:
        self.cursor_info = tk.Frame(self.sideframe)
        self.cursor_info.pack(fill=tk.X)
        self.cursor_position = tk.Label(self.cursor_info, text='Cursor: ?,?')
        self.cursor_position.pack(side=tk.LEFT)
        self.cursor_value = tk.Label(self.cursor_info, text='Val: ?')
        self.cursor_value.pack(side=tk.RIGHT)

        # Initalize the directory navigation setup with a listbox and scrollbar
        self.scrollbar = tk.Scrollbar(self.sideframe, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dirlist = tk.Listbox(self.sideframe, selectmode=tk.SINGLE,
                                  activestyle='none', borderwidth=0,
                                  highlightthickness=0,
                                  yscrollcommand=self.scrollbar.set)
        self.dirlist.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.config(command=self.dirlist.yview)

        self.bind_all('<Control-o>', self.open_dialog)

        # Controls for navigating the list of current directory contents
        self.bind_all('<Right>', self.open_item)
        self.bind_all('<Return>', self.open_item)
        self.bind_all('<BackSpace>', self.back)
        self.bind_all('<Left>', self.back)
        self.bind_all('<Up>', self.up)
        self.bind_all('<Down>', self.down)
        self.bind_all('<Key>', self.move_to_key)

        self.dirlist.bind('<<ListboxSelect>>', self.click_list)
        self.dirlist.bind('<Double-Button-1>', self.open_item)

        self.bind_all('<Escape>', quit)
        self.parent.protocol("WM_DELETE_WINDOW", self.parent.quit)

        self.bind_all('<Control-h>', self.show_help)

        # Defaults
        self.save_dir = os.getcwd()
        self.savename = ''
        self.filename = ''
        self.files = []
        self.fileindex = 0
        self.selection = 0
        self.imagedata = None
        self.fitted = False
        self.zoom = 1.
        self.ypos, self.xpos = 0., 0.
        self.last_y, self.last_x = 0., 0.
        self.last_dims = 0., 0.
        self.last_width = 0
        self.black_level = 0
        self.white_level = 0
        self.help_window = None
        self.h, self.w = 0, 0
        self.updating = False

        self.mini_label.photo = ImageTk.PhotoImage(Image.fromarray(np.zeros((THUMBSIZE, THUMBSIZE))))
        self.mini_label.config(image=self.mini_label.photo)

        self.main_image.photo = ImageTk.PhotoImage(Image.fromarray(np.zeros((HEIGHT-HISTOGRAM_HEIGHT, WIDTH-THUMBSIZE))))
        self.main_image.itemconfig(self.main_image.image,
                                   image=self.main_image.photo)

        self.main_image.config(bg='#f4f4f4')
        self.mini_label.config(bg='#f4f4f4')

        self.refresh_dirlist(repeat=True)

        if open_file is not None:
            self.load_image(open_file)

    def keybindings(self):
        """
        Assign all keybindings that cause exceptions without an image
        """
        self.bind_all('<Configure>', self.on_resize)

        self.bind_all('<Control-r>', self.renew_scaling)
        self.bind_all('<Control-f>', self.zoom_to_fit)

        self.bind_all('<Control-s>', self.save_image)

        self.bind_all('<MouseWheel>', self.mousewheel_windows)

        self.bind_all('<Button-4>', self.mousewheelup_linux)
        self.bind_all('<Button-4>', self.mousewheelup_linux)
        self.bind_all('<Button-5>', self.mousewheeldown_linux)
        self.bind_all('<Button-5>', self.mousewheeldown_linux)

        self.mini_label.bind('<Button-1>', self.click_thumbnail)
        self.mini_label.bind('<B1-Motion>', self.click_thumbnail)

        self.main_image.bind('<Button-1>', self.click_image)
        self.main_image.bind('<B1-Motion>', self.move_image)
        self.main_image.bind('<ButtonRelease-1>', self.release_image)

        self.main_image.bind('<Motion>', self.update_cursor_info)

        self.sliders.bind('<Button-1>', self.click_slider)
        self.sliders.bind('<B1-Motion>', self.move_slider)

    def update_cursor_info(self, event):
        """
        Display the cursor location and image value at that location
        """
        y = int(round(self.ypos + event.y/self.zoom - 1))
        x = int(round(self.xpos + event.x/self.zoom - 1))

        if y < self.imagedata.shape[0] and x < self.imagedata.shape[1]:
            self.cursor_position.configure(text='Cursor: '+str(y)+', '+str(x))
            self.cursor_value.configure(text='Val: ' +
                                        str(round(self.imagedata[y, x], 1)))

    # This needs a rework to accomodate full name typing
    def move_to_key(self, event):
        """
        Select the first entry in dirlist that matches a key press
        """
        if self.selection < len(self.files)-1 and (
                    self.files[self.selection][0].lower() == event.char) and (
                        self.files[self.selection+1][0].lower() == event.char):
            self.down(None)
        else:
            for f in range(len(self.files)):
                if self.files[f][0].lower() == event.char:
                    self.selection = f
                    self.dirlist.selection_clear(0, tk.END)
                    self.dirlist.selection_set(self.selection)
                    self.dirlist.see(self.selection)
                    return
                if f == len(self.files)-1:
                    return

    def mousewheel_windows(self, event):
        """
        Zoom in or out on a windows os, if possible
        """
        if self.fitted:
            if event.delta < 0:
                self.zoom = 2.**np.floor(np.log2(self.zoom))
            else:
                self.zoom = 2.**np.ceil(np.log2(self.zoom))
            self.fitted = False
        elif event.delta < 0 and self.zoom > 1/8:
            self.zoom /= 2
            self.ypos -= self.h/2
            self.xpos -= self.w/2
        elif event.delta > 0 and self.zoom < 8:
            self.zoom *= 2
            self.ypos += self.h/4
            self.xpos += self.w/4

        self.redraw_image()
        self.redraw_minimap()

    def mousewheelup_linux(self, event):
        """
        Zoom in, if possible
        """
        if self.zoom < 16:
            if self.fitted:
                self.fitted = False
                self.zoom = 2.**np.floor(np.log2(self.zoom))
            self.zoom *= 2
            self.ypos += self.h/4
            self.xpos += self.w/4

            self.redraw_image()
            self.redraw_minimap()

    def mousewheeldown_linux(self, event):
        """
        Zoom out, if possible
        """
        if self.zoom > 1/16:
            if self.fitted:
                self.fitted = False
                self.zoom = 2.**np.ceil(np.log2(self.zoom))
            self.zoom /= 2
            self.xpos -= self.h/2
            self.ypos -= self.w/2

            self.redraw_image()
            self.redraw_minimap()

    def zoom_to_fit(self, event):
        """
        Adjust zoom to fit the entire image in the current window
        """
        self.zoom = min(self.main_image.winfo_height()/self.imagedata.shape[0],
                        self.main_image.winfo_width()/self.imagedata.shape[1])
        self.fitted = True
        self.redraw_image()
        self.redraw_minimap()

    def click_thumbnail(self, event):
        """
        Center view on a location clicked in the minimap
        """
        self.ypos = event.y / self.minidata.shape[0] * \
            self.imagedata.shape[0]-self.h/2
        self.xpos = event.x / self.minidata.shape[1] * \
            self.imagedata.shape[1]-self.w/2

        self.redraw_image()
        self.redraw_minimap()

    # These three functions enable click-and-drag motion of an image
    def click_image(self, event):
        """
        Keep track of the current cursor position
        """
        self.last_y = event.y
        self.last_x = event.x

    def move_image(self, event):
        """
        Move the image view position
        """
        last_ypos = self.ypos
        last_xpos = self.xpos
        self.ypos += (self.last_y-event.y)/self.zoom
        self.xpos += (self.last_x-event.x)/self.zoom
        self.last_y = event.y
        self.last_x = event.x

        self.check_view()
        moved = (last_ypos != self.ypos) or (last_xpos != self.xpos)
        if moved:
            self.redraw_image()
            self.redraw_minimap()

    def release_image(self, event):
        """
        Keep track of the image view position for next click-and-drag
        """
        self.last_y = self.ypos+self.h/2
        self.last_x = self.xpos+self.w/2

    # open_item, up, down, back, click_list handle interaction with dirlist
    def open_item(self, event):
        """
        Handle opening an entry in the dirlist, display image and cd for dirs
        """
        fil = self.files[self.selection]
        if fil.rsplit('.', 1)[-1] in EXTENSIONS:
            self.load_image(fil)
        elif os.path.isdir(fil):
            os.chdir(fil)
            self.refresh_dirlist()

    def up(self, event):
        """
        Select the item above the current selection in the dirlist
        """
        if self.selection > 0:
            self.selection -= 1
            self.dirlist.selection_clear(0, tk.END)
            self.dirlist.selection_set(self.selection)
            self.dirlist.see(self.selection)

    def down(self, event):
        """
        Select the item below the current selection in the dirlist
        """
        if self.selection < len(self.files)-1:
            self.selection += 1
            self.dirlist.selection_clear(0, tk.END)
            self.dirlist.selection_set(self.selection)
            self.dirlist.see(self.selection)

    def back(self, event):
        """
        Back up a directory
        """
        os.chdir('..')
        self.refresh_dirlist()

    def click_list(self, event):
        """
        Highlight the currently selected item in the directory list
        """
        self.selection = self.dirlist.curselection()[0]
        self.dirlist.selection_clear(0, tk.END)
        self.dirlist.selection_set(self.selection)
        self.dirlist.activate(self.selection)

    def reload_dirlist(self):
        """
        Update the dirlist to the contents of the current directory
        """
        try:
            new_files = [f for f in os.listdir('.') if (
                f.rsplit('.', 1)[-1] in EXTENSIONS) or (
                    os.path.isdir(f) and os.access(f, os.R_OK)) and
                         not f.startswith('.')]

            new_files.sort(key=str.lower)

            new_files.append('..')

            removals = [f for f in self.files if f not in new_files]
            additions = [f for f in new_files if f not in self.files]

            for fil in removals:
                remove_index = self.files.index(fil)
                self.dirlist.delete(remove_index)
                self.files.remove(fil)

            for fil in additions:
                insert_index = bisect.bisect(self.files, fil)
                if insert_index == len(self.files):
                    insert_index -= 1
                self.files.insert(insert_index, fil)
                self.dirlist.insert(insert_index, fil)

        except WindowsError:
            pass

        finally:
            self.parent.after(500, self.reload_dirlist)

    def refresh_dirlist(self, repeat=False):
        """
        Display entries in the current directory in the directory list
        """
        self.dirlist.delete(0, tk.END)

        self.files = [f for f in os.listdir('.') if (
            f.rsplit('.', 1)[-1] in EXTENSIONS) or (
                os.path.isdir(f) and os.access(f, os.R_OK)) and
                      not f.startswith('.')]

        self.files.sort(key=str.lower)

        self.files.append('..')

        for f in self.files:
            self.dirlist.insert(tk.END, f)

        self.selection = 0
        self.dirlist.selection_clear(0, tk.END)
        self.dirlist.selection_set(0)

        if repeat:
            self.parent.after(500, self.reload_dirlist)

    def open_dialog(self, event):
        self.filename = filedialog.askopenfilename(
            filetypes=[('FITS files', '*.fit;*.fits;*.FIT;*.FITS'),
                       ('all files', '*')],
            initialdir=os.getcwd())

        if self.filename not in ('', ()):
            os.chdir(os.path.dirname(self.filename))
            self.load_image(self.filename)
        else:
            return

    def load_image(self, filename):
        """
        Read an image and make sure the display and interface are initalized
        """
        if not os.path.isabs(filename):
            self.filename = os.path.join(os.getcwd(), filename)
        else:
            self.filename = filename

        # Set backgrounds to the same gray as the default frame background
        self.main_image.config(bg='#f4f4f4')
        self.mini_label.config(bg='#f4f4f4')

        # Load image data and set defaults
        temp_data = fits.open(self.filename)[0].data.astype(np.float64)
        if temp_data is None or temp_data.ndim != 2:
            raise IOError('Invalid fits file')

        self.imagedata = temp_data

        self.black_level = np.percentile(self.imagedata.ravel()[::100], 10.)
        self.white_level = np.percentile(self.imagedata.ravel()[::100], 99.9)
        self.zoom = 1.

        self.ypos = 0
        self.xpos = 0
        self.check_view()
        self.last_dims = (self.w, self.h)
        self.last_width = self.w
        self.last_y = self.ypos+self.h//2
        self.last_x = self.xpos+self.w//2

        # Generate a default save name
        self.savename = os.path.basename(self.filename).rsplit('.', 1)[0]+'.png'

        # Display the filename of the current image in the title bar
        self.parent.title(MYNAME+' ('+self.filename+')')

        # Build the histogram image
        self.make_histogram_fig()

        # Configure the image display frame and canvases
        if self.histogram.image is None:
            self.histogram.image = self.histogram.create_image(0, 0, image=None, anchor='nw')
            self.main_image.image = self.main_image.create_image(0, 0, image=None, anchor='nw')

        self.xpos = (self.imagedata.shape[1]-self.w)//2
        self.ypos = (self.imagedata.shape[0]-self.h)//2

        self.clip_image()
        self.redraw_image()
        self.redraw_minimap()
        self.redraw_histogram()

        # Make sure keybindings are initalized
        self.keybindings()

    def renew_scaling(self, event):
        """
        Set a reasonable white and black clipping level based on percentile
        """
        self.black_level = np.percentile(self.imagedata, 10.)
        self.white_level = np.percentile(self.imagedata, 99.9)
        
        self.clip_image()
        self.redraw_image()
        self.redraw_minimap()
        self.redraw_histogram()

    def check_view(self):
        """
        Check bounds on view position and compute the view height and width
        """

        # Compute view height and width
        self.h = int((self.main_image.winfo_height()-2)/self.zoom)
        self.w = int((self.main_image.winfo_width()-2)/self.zoom)

        # Prevent overscrolling
        if self.ypos < 0:
            self.ypos = 0

        if self.ypos + self.h > self.imagedata.shape[0]:
            self.ypos = self.imagedata.shape[0]-self.h

        if self.xpos < 0:
            self.xpos = 0

        if self.xpos + self.w > self.imagedata.shape[1]:
            self.xpos = self.imagedata.shape[1]-self.w

        # Check for oversized window
        if self.h >= self.imagedata.shape[0]:
            self.ypos = 0
            self.h = self.imagedata.shape[0]
        if self.w >= self.imagedata.shape[1]:
            self.xpos = 0
            self.w = self.imagedata.shape[1]

    def on_resize(self, event):
        """
        Recompute the image and minimap display.
        """
        self.check_view()
        # If triggered by a configure event, make sure to only redraw what
        # needs to be redrawn
        if (self.last_dims[0] != self.w) or (self.last_dims[1] != self.h):
            self.redraw_image()
            self.redraw_minimap()
            self.redraw_histogram()

        elif self.last_width != self.histogram.winfo_width():
            self.redraw_histogram()

        self.last_pos = self.ypos, self.xpos
        self.last_dims = self.w, self.h
        self.last_width = self.histogram.winfo_width()

    def clip_image(self):
        """
        Re-clip the currently displayed image
        """
        self.clipped = self.imagedata.clip(self.black_level, self.white_level)
        self.clipped -= self.black_level

        self.clipped *= 255/(self.white_level-self.black_level)
        self.clipped = self.clipped.astype(np.uint8, copy=True)

        # Rebuild the data used to draw the minimap
        mini_zoom = min(THUMBSIZE/self.clipped.shape[0],
                        THUMBSIZE/self.clipped.shape[1])
        mini_shape = (np.array(self.clipped.shape[::-1]) * mini_zoom
                     ).astype(int)
        self.clipped = Image.fromarray(self.clipped)
        mini = self.clipped.resize(mini_shape, Image.NEAREST)

        self.minidata = np.dstack(3*(mini,))

    def redraw_image(self):
        """
        Re-render only the currently displayed image for canvas
        """
        self.check_view()

        # Crop the image to the displayed section
        crop_region = (int(self.xpos), int(self.ypos), int(self.xpos+self.w),
                       int(self.ypos+self.h))
        imgslice = self.clipped.crop(crop_region)
        imgslice.load()

        newsize = tuple([int(self.zoom*x) for x in imgslice.size])
        resized = imgslice.resize(newsize, Image.NEAREST)

        self.main_image.photo = ImageTk.PhotoImage(resized)
        self.main_image.itemconfig(self.main_image.image,
                                   image=self.main_image.photo)

    def redraw_minimap(self):
        """
        Re-render only the minimap
        """
        mod = self.minidata.copy()
        # Draw the minimap with a green square at the bounds of the view
        top = int(self.ypos/self.imagedata.shape[0]*self.minidata.shape[0])
        if top < 0:
            top = 0
        bot = int((self.ypos-1+self.h) / self.imagedata.shape[0] *
                  self.minidata.shape[0])
        if bot > THUMBSIZE-2:
            bot = THUMBSIZE-2
        lef = int(self.xpos/self.imagedata.shape[1]*self.minidata.shape[1])
        if lef < 0:
            lef = 0
        rig = int((self.xpos-1+self.w) / self.imagedata.shape[1] *
                  self.minidata.shape[1])
        if rig > THUMBSIZE-2:
            rig = THUMBSIZE-2
        mod[top, lef:rig+1, 1] = 255
        mod[bot, lef:rig+1, 1] = 255
        mod[top:bot+1, lef, 1] = 255
        mod[top:bot+1, rig, 1] = 255

        self.mini_label.photo = ImageTk.PhotoImage(Image.fromarray(mod))
        self.mini_label.config(image=self.mini_label.photo)

    def click_slider(self, event):
        """
        Note the current slider position and which was grabbed, prefer white
        """
        if abs(self.white_x - event.x) < 5:
            self.start_white_x = event.x
            self.grabbed = 'white'
        elif abs(self.black_x - event.x) < 5:
            self.start_black_x = event.x
            self.grabbed = 'black'
        else:
            self.grabbed = None

    def move_slider(self, event):
        """
        Change clipping based on cursor x position change, update live
        """
        xmin, xmax = self.databounds

        # Convert shift to a value in pixel brightness
        if self.grabbed == 'white':
            shift = self.start_white_x - event.x
            self.white_level += shift/self.histogram.winfo_width()*(xmin-xmax)
            self.start_white_x = event.x

            # Prevent slider overlap
            if self.white_level <= self.black_level:
                self.white_level = self.black_level+1
                self.start_white_x = self.black_x

            # Prevent slider running off display
            if self.white_level > xmax:
                self.white_level = xmax
                self.start_white_x = self.histogram.winfo_width()

        elif self.grabbed == 'black':
            shift = self.start_black_x - event.x
            self.black_level += shift/self.histogram.winfo_width()*(xmin-xmax)
            self.start_black_x = event.x

            if self.black_level >= self.white_level:
                self.black_level = self.white_level-1
                self.start_black_x = self.white_x

            if self.black_level < xmin:
                self.black_level = xmin
                self.start_black_x = 0

        self.clip_image()
        self.redraw_histogram()
        self.redraw_image()
        self.redraw_minimap()

    def redraw_histogram(self):
        """
        Re-render the histogram and the white/black clipping lines
        """
        xmin, xmax = self.databounds

        hist_resized = self.hist_full.resize((self.main_image.winfo_width(),
                                              HISTOGRAM_HEIGHT), Image.NEAREST)

        self.histogram.photo = ImageTk.PhotoImage(hist_resized)
        self.histogram.itemconfig(self.histogram.image,
                                  image=self.histogram.photo)

        # Draw sliders
        self.sliders.delete('all')

        self.black_x = (self.black_level-xmin)/(xmax-xmin) * \
                                 self.histogram.winfo_width()
        self.sliders.create_line(self.black_x, -1, self.black_x, 12,
                                 arrow=tk.FIRST, arrowshape=(11, 10, 4))

        self.white_x = (self.white_level-xmin)/(xmax-xmin) * \
                                 self.histogram.winfo_width()
        self.sliders.create_line(self.white_x, -1, self.white_x, 10,
                                 arrow=tk.FIRST, arrowshape=(11, 10, 4),
                                 fill='white')

        # Slider lines
        self.histogram.delete('bline','wline')
        self.histogram.create_line(self.black_x, 0, self.black_x, 50,
                                   fill='blue', tag='bline')
        self.histogram.create_line(self.white_x, 0, self.white_x, 50,
                                   fill='blue', tag='wline')

    def make_histogram_fig(self):
        """
        Plot a histogram of the image data with axes scaled to enhance features
        """
        data = self.imagedata.ravel()

        # Clipping data makes the histogram look nice but the sliders useless, so just clip the histogram
        lower_bound, upper_bound = np.percentile(data[::100], [0.01, 99.95])

        self.databounds = lower_bound, upper_bound

        mask = (data > lower_bound) & (data < upper_bound)
        data = data[mask]

        # Rescale data
        data -= data.min()
        data /= data.max()
        data *= self.parent.winfo_screenwidth()

        histogram = np.bincount(data.astype(int))[:-1]
        histogram = histogram / histogram.max() * HISTOGRAM_HEIGHT

        # Manual plotting
        coords = np.arange(0, HISTOGRAM_HEIGHT)[::-1]
        coords = np.repeat(coords[:, np.newaxis], self.parent.winfo_screenwidth(), axis=1)

        histogram = coords > histogram[np.newaxis, :]

        histogram = (histogram * 255).astype(np.uint8)
        histogram = np.repeat(histogram[:, :, np.newaxis], 3, axis=2)

        self.hist_full = Image.fromarray(histogram)

    def save_image(self, event):
        """
        Open a file dialog and save the image as currently displayed.
        """
        path = filedialog.asksaveasfilename(defaultextension='.png',
                                            initialdir=self.save_dir,
                                            initialfile=self.savename)
        # Update defaults if a selection was made
        if path != '':
            self.savename = os.path.basename(path)
            self.save_dir = os.path.dirname(path)

            self.main_image.photo.save(path)

    def close_help(self, *args):
        """
        Remove the help window
        """
        self.parent.bind_all('<Escape>', quit)
        self.help_window.destroy()
        self.help_window = None

    # Add a scrollbar and allow resize
    def show_help(self, event):
        """
        Display a help window with all keybindings
        """
        if self.help_window is None:
            self.help_window = tk.Toplevel()
            self.help_window.title('viewfits help')
            self.help_window.resizable(0, 0)

            commands = ['open a file with open file dialog',
                        'save the currently displayed image',
                        'auto-adjust white and black levels for current image',
                        'zoom to fit current window size',
                        'display the help/commands dialog',
                        'adjust zoom level',
                        'nagivate current directory',
                        'open file or change directory to current selection',
                        'back up to parent directory',
                        'quit']
            keys = ['ctrl + o', 'ctrl + s', 'ctrl + r', 'ctrl + f', 'ctrl + h',
                    'mousewheel', 'up/down', 'right/enter',
                    'left/backspace', 'Esc']

            self.keys = tk.Message(self.help_window, text='\n\n'.join(keys))
            self.keys.pack(side=tk.RIGHT)
            self.commands = tk.Message(self.help_window,
                                       text='\n\n'.join(commands), width=400)
            self.commands.pack(side=tk.LEFT)

            self.parent.bind_all('<Escape>', self.close_help)
            self.help_window.protocol("WM_DELETE_WINDOW", self.close_help)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?',
                        help='filename or path to file to display')
    args = parser.parse_args()

    root = tk.Tk()
    root.geometry(str(WIDTH)+'x'+str(HEIGHT))

    Viewer(root, args.filename)

    root.mainloop()

if __name__ == "__main__":
    main()

