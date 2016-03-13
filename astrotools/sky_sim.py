from __future__ import division, print_function

import os
import time
import ctypes
import Tkinter as tk
from datetime import datetime

import numpy as np
import ephem
from scipy.misc import imsave

# Image save path
save_path = os.path.join(os.getcwd(), 'test.png')

# Star psf dimensions
size = 11
psf = 2

# Use tkinter to get screen dimensions
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
screen_radius = np.sqrt(screen_height**2 + screen_width**2)/2

# Initialize image
image = np.zeros((screen_height+20, screen_width+20))

# Load star locations
stars = set()
with open('simbad.tsv') as star_data:
    for line in star_data:
        if line[0].isdigit() and '~' not in line:
            _, coordinates, b_mag, v_mag = line.split('\t')
            groups = coordinates.split()
            right_ascension, declination = ':'.join(groups[:3]), ':'.join(groups[3:])
            stars.add(ephem.readdb('star,f|S,{},{},{}'.format(right_ascension, declination, v_mag)))

altitude = np.empty(len(stars))
azimuth = np.empty(len(stars))
v_mag = np.empty(len(stars))

while True:
    start = datetime.now()
    # Set up observer so get correct time
    location = ephem.Observer()
    location.lat = '29.6652'
    location.lon = '-82.325'

    # Compute alt and az for each star
    for s,star in enumerate(stars):
        star.compute(location)
        altitude[s] = star.alt
        azimuth[s] = star.az
        v_mag[s] = star.mag

    # Convert to rectangular screen coordinates
    screen_x = screen_radius * np.cos(azimuth) * np.sin(np.pi/2-altitude)
    screen_y = screen_radius * np.sin(azimuth) * np.sin(np.pi/2-altitude)

    # Filter stars that fit on the screen
    mask = (screen_x > -screen_width/2) & (screen_x < screen_width/2) & (screen_y < screen_height/2) & (screen_y > -screen_height/2) & (altitude > 0)
    screen_x = screen_x[mask] + screen_width/2
    screen_y = screen_y[mask] + screen_height/2

    part_v_mag = v_mag[mask]
    part_v_mag -= part_v_mag.max()
    part_v_mag *= -1

    image *= 0
    screen_y += 10
    screen_x += 10
    for i in range(screen_y.size):
        y,x = int(screen_y[i]), int(screen_x[i])
        y_c,x_c = screen_y[i]-y, screen_x[i]-x
        dst = np.sqrt((np.arange(size)[:,None]-5-y_c)**2 + (np.arange(size)-5-x_c)**2)
        star_image = np.exp(-dst**2/psf**2)
        star_image *= part_v_mag[i]/np.sum(star_image)
        image[y-5:y+6, x-5:x+6] += star_image

    image = np.log10(3*image+1)
    #image = image.clip(0,0.9)

    imsave('test.png', image[10:-10,10:-10])

    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, save_path, 2)
    print(datetime.now()-start)

    time.sleep(2)