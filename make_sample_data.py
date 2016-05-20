#!/usr/bin/env python
'''
We need some data for vectorize_starfield to work on, better make some
'''
from __future__ import division, print_function
import sys

import numpy as np
from distributions import gaussian
from astropy.io import fits


def make_sample_data(output_filename):

    IMAGE_SIZE = 1024
    NUM_STARS = 500
    PSF_WIDTH = 3
    STAR_FREQUENCY = 1/1000000
    READNOISE = 5
    BIAS_LEVEL = 200
    DARK_CURRENT = 1000
    NUM_IMAGES = 1

    noiseless = np.zeros((IMAGE_SIZE,IMAGE_SIZE))
    star_pos = np.random.random_sample((2,NUM_STARS))*IMAGE_SIZE
    star_max = np.random.exponential(STAR_FREQUENCY,NUM_STARS)

    if NUM_STARS > 0:
        star_max *= 50000/star_max.max()

    coordinates = np.mgrid[:IMAGE_SIZE,:IMAGE_SIZE].ravel()

    for i in range(NUM_STARS):
        noiseless += gaussian(coordinates,star_max[i],star_pos[0,i],star_pos[1,i],
                           PSF_WIDTH).reshape(noiseless.shape)
        sys.stdout.write(str(i/NUM_STARS)+'\r')
        sys.stdout.flush()
    sys.stdout.write(' '*78+'\r')
    sys.stdout.flush()

    for i in range(NUM_IMAGES):
        noise = np.random.randn(*noiseless.shape)*np.sqrt(noiseless)
        noise += np.random.normal(0,READNOISE,noiseless.shape)
        noise += DARK_CURRENT
        noise += np.random.normal(0,np.sqrt(DARK_CURRENT),noiseless.shape)
        noise += BIAS_LEVEL

        fits.writeto(output_filename+str(i)+'.fits',(noiseless+noise).astype(np.int32),clobber=True)


if __name__ == "__main__":
    make_sample_data('test')
