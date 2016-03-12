from __future__ import division, print_function

import os
import Tkinter as tk
import time
from datetime import datetime
import ctypes

import numpy as np
import ephem
import matplotlib.pyplot as plt

from scipy.misc import imsave

# Use tkinter to get screen dimensions
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
screen_radius = np.sqrt(screen_height**2 + screen_width**2)/2

# Initialize image
image = np.zeros((screen_height+20, screen_width+20))

# Initialize star template
size = 11
psf = 2
dst = np.sqrt((np.arange(size)[:,None]-size/2+.5)**2 + (np.arange(size)-size/2+.5)**2)
template = np.exp(-dst**2/psf**2)

# Load star locations
star_data = np.loadtxt('star_list.txt')

right_ascension = star_data[:,0]*np.pi/180
declination = star_data[:,1]*np.pi/180
b_mag = star_data[:,2]
v_mag = star_data[:,3]

altitude = np.empty_like(right_ascension)
azimuth = np.empty_like(declination)

while True:
    start = datetime.now()
    # Set up observer so get correct time
    location = ephem.Observer()
    location.lat = '29.6652'
    location.lon = '-82.325'

    # Compute alt and az for each star
    for i in range(declination.size):
        star = ephem.readdb('star,f|S,'+str(ephem.hours(right_ascension[i]))+','+str(ephem.degrees(declination[i]))+',0')
        star.compute(location)
        altitude[i] = star.alt
        azimuth[i] = star.az

    # Convert to rectangular screen coordinates
    screen_x = screen_radius * np.cos(azimuth) * np.sin(np.pi/2-altitude)
    screen_y = screen_radius * np.sin(azimuth) * np.sin(np.pi/2-altitude)

    # Filter stars that fit on the screen
    mask = (screen_x > -screen_width/2) & (screen_x < screen_width/2) & (screen_y < screen_height/2) & (screen_y > -screen_height/2) & (altitude > 0)
    screen_x = (screen_x[mask] + screen_width/2).astype(int)
    screen_y = (screen_y[mask] + screen_height/2).astype(int)

    part_v_mag = v_mag[mask]
    part_v_mag -= part_v_mag.max()
    part_v_mag *= -1
    part_v_mag = part_v_mag.clip(0,3)

    # Draw the image
    image *= 0
    for i in range(screen_y.size):
        y,x = screen_y[i]+10, screen_x[i]+10
        image[y-5:y+6, x-5:x+6] += part_v_mag[i]*template

    image = image.clip(0,part_v_mag.max())
    imsave('test.png', image[10:-10,10:-10])

    SPI_SETDESKWALLPAPER = 20
    path = os.path.join(os.getcwd(), 'test.png')
    ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, path, 2)
    print(datetime.now()-start)

    time.sleep(1)

