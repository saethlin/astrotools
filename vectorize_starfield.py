#!/usr/bin/env python

import os
import numpy as np
from astropy.io import fits
import scipy.optimize
import scipy.signal
from scipy.misc import imsave
import scipy.ndimage


def gaussian(coordinates, height, *centroid_and_width):
    """
    The n-dimensional symmetric Gaussian distribution
    Expects coordinates x that look like [y0,y1,x0,x1] where y0 and y1 bound the
    y-values of the output, or x looks like [y1,y2,y3,...,x1,x2,x3,...]
    gaussian Integral = height*2*np.pi*np.sqrt(width)
    """
    
    width = centroid_and_width[-1]
    centroids = centroid_and_width[:-1]
    
    pos = coordinates.reshape((len(centroids),-1)).copy()
    
    for i in range(len(centroids)):
        pos[i] -= centroids[i]
     
    dst = np.sum(pos**2,0)
    
    return height*np.exp(-dst/(2*width**2))


def genfiles(path, file_extension='fits'):
    """Produce a generator that yields files ending with file_extension in directory path"""
    for entry in os.scandir(path):
        if entry.is_file() and entry.name.endswith(file_extension):
            yield entry.path


if __name__ == "__main__":
    EXTENSIONS = ['fits', 'fit']
    INPUT_DIR = "../sample_data"
    OUTPUT_DIR = "."
    FILTER_WIDTH = 1.5
    APERTURE_RADIUS = 5

    files = genfiles(INPUT_DIR)

    # Open up the first file to figure out how big the images are so we can know the shape of the array to allocate
    image = fits.open(files[0])[0].data
    stack = np.empty((len(files),)+image.shape)
    stack[0] = image.copy()

    for f, fname in enumerate(files[1:]):
        stack[f] = fits.open(fname)[0].data

    stacked = np.median(stack, axis=0, overwrite_input=True)

    smooth = scipy.ndimage.gaussian_filter(stacked, FILTER_WIDTH)

    laplace = scipy.ndimage.laplace(smooth)

    stars = laplace < 0

    stars_inds = scipy.signal.argrelmin(laplace)
    stars = np.zeros(stacked.shape, bool)
    stars[stars_inds] = True

    sky_value = np.median(stacked)
    signal = stacked > (sky_value + 2*np.sqrt(sky_value))

    stars &= signal

    coordinates = np.mgrid[:stacked.shape[0], :stacked.shape[1]]

    coord = np.mgrid[:2*APERTURE_RADIUS+1, :2*APERTURE_RADIUS+1]
    dst = np.sum(coord**2,0)
    ap = dst <= APERTURE_RADIUS**2

    star_coordinates = np.where(stars)

    star_vectors = np.empty((star_coordinates.shape[0], ))
    output_test = np.zeros(stacked.shape)

    for i, (y, x) in enumerate(star_coordinates):
        star_coordinates = coordinates[y-APERTURE_RADIUS:y+APERTURE_RADIUS+1,
                                       x-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]
        star_data = stacked[y-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]

        guesses = [stacked[y, x]-sky_value, y, x, 1., sky_value]
        fit, _ = scipy.optimize.curve_fit(gaussian, star_coordinates, star_data, p0=guesses)
        
        star_vectors[i] = fit

        output_test[y-APERTURE_RADIUS:y+APERTURE_RADIUS+1,
                    x-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap] += gaussian(star_coordinates, *fit)

    np.save('vectorized.npy',star_vectors)
    imsave('vectorized.png',np.log(output_test))
