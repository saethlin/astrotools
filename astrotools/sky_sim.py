"""
TODO:
Set size and image padding based on psf size
Add color based on B-V or temperature
Try adding constellation lines
"""
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

# Star psf size
psf = 1

# Determine size of the region to plot the stellar psf on
size = 2*np.sqrt(2*np.log(255/2))*psf
size = np.ceil(size) // 2 * 2 + 1

# Use tkinter to get screen dimensions
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
screen_radius = np.sqrt(screen_height**2 + screen_width**2)/2

# Initialize image
image = np.zeros((screen_height+size//2*2, screen_width+size//2*2))

# Load star locations
stars = set()
"""
with open('simbad.tsv') as star_data:
    for line in star_data:
        if line[0].isdigit() and '~' not in line:
            _, coordinates, b_mag, v_mag = line.split('\t')
            groups = coordinates.split()
            right_ascension, declination = ':'.join(groups[:3]), ':'.join(groups[3:])
            stars.add(ephem.readdb('star,f|S,{},{},{}'.format(right_ascension, declination, v_mag)))
"""

with open('orion.txt') as star_data:
    for line in star_data:
        right_ascension, declination, mag = line.split()
        stars.add(ephem.readdb('star,f|S,{},{},{}'.format(right_ascension, declination, mag)))

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
    screen_y += size//2
    screen_x += size//2
    for i in range(screen_y.size):
        y,x = int(screen_y[i]), int(screen_x[i])
        y_c,x_c = screen_y[i]-y, screen_x[i]-x
        dst = np.sqrt((np.arange(size)[:,None]-size//2-y_c)**2 + (np.arange(size)-size//2-x_c)**2)
        star_image = np.exp(-dst**2/psf**2)
        star_image *= part_v_mag[i]/np.sum(star_image)
        image[y-size//2:y+size//2+1, x-size//2:x+size//2+1] += star_image

    # Rescale the image
    image = np.log10(3*image+1)

    imsave('test.png', image[size//2:-size//2,size//2:-size//2])

    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, save_path, 2)
    print(datetime.now()-start)

    time.sleep(2)