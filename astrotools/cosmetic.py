#!/usr/bin/env python
"""
TODO:
Construct a mask at each temperature range that has a unique color from the map
"""
import os

import numpy as np
from astropy.io import fits
from scipy.optimize import curve_fit
from scipy.ndimage import zoom
from scipy.misc import imread,imsave


'''
Linear rescaling of an image, usually okay
'''
def linear_rescale(img):
    black_level = np.percentile(img,10.)
    white_level = np.percentile(img,80.)
    return (img-black_level).clip(0,white_level)


def find_nearest(array,value):
    return np.abs(array-value).argmin()

def cosmeticRGB(blu_name,vis_name):
    
    SMOOTHING_WIDTH = 1.5
    WHITE_LEVEL = 4000
    
    blu = fits.open(blu_name)[0].data
    vis = fits.open(vis_name)[0].data
    vis = (vis-np.median(vis)).clip(1)
    blu = (blu-np.median(blu)).clip(1)

    B = -2.5*np.log10(blu)
    V = -2.5*np.log10(vis)

    #Ballesteros' formula
    T = 4600*(1/(0.92*(B-V)+1.7) + 1/(0.92*(B-V)+0.62))

    #Produce a temp-color lookup table from an image
    colors = imread('blackbody.png')[:,0,:3].astype(float)
    temps = np.linspace(1e3,1e4,len(colors))
    
    print(colors.size)
    exit()

    #Use a mask to only replace the bright pixels
    mask = blu > np.percentile(blu,70)
    image_temps = T[mask]
    normalize = vis[mask]

    out = np.zeros((image_temps.size,3))

    for t in range(image_temps.size):
        ind = find_nearest(image_temps[t],temps)
        out[t] = colors[ind] * normalize[t]

    #Convert out to uint 8
    out = out.clip(0,WHITE_LEVEL*255)

    out = (out/out.max()*255).astype(np.uint8)

    final = np.zeros((blu.shape[0],blu.shape[1],3),np.uint8)

    final[mask] = out
    imsave('modified.png',final)
    os.system('modified.png')

#cosmeticRGB('test.fits','test.fits')
