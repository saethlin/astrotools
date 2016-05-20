#!/usr/bin/env python
"""
This module (or script) provides tools for aligning images. The general
technique is to pick an image in a set (call it the base) and shift every other
image to match up features.

shift_int -- Quickly shifts two images and computes an similarity parameter
intalign -- Brute-force integer shift only alignment of two images
imshift -- An wrapper for scipy.ndimage.interpolation.shift for curve_fit
align -- Aligns an image to a base image
"""

from __future__ import division, print_function
import sys
import os
from datetime import datetime
import numpy as np
from astropy.io import fits
from scipy.optimize import curve_fit
from scipy.ndimage.interpolation import zoom
from scipy.ndimage.interpolation import shift


def shift_int(image, base, y, x):
    """
    Quickly shift an image with respect to a base and return a parameter that
    is minimized when the images are well aligned, and not biased towards
    large shifts

    Arguments:
    image -- The input image that is shifted
    base -- The second image to match
    y -- An integer offset along axis 0
    x -- An integer offset along axis 1
    """
    y, x = int(y), int(x)

    h, w = image.shape

    new_image = image[max(0, -y):min(h, h-y), max(0, -x):min(w, w-x)]

    new_base = base[max(0, y):min(h, h+y), max(0, x):min(w, w+x)]

    return np.mean((new_image-new_base)**2)


def align_int(image, base, span=None, y_init=0, x_init=0):
    """
    Quickly find the offsets along axes 0 and 1 that align image to base. If
    the image is not aligned in coordinates between guess-span and guess+span
    this may produce a strange result.

    Arguments:
    image -- The input image that is shifted
    base -- The second image to match
    span -- The size of the coordinate search space
    y0 -- A guess at the offset along axis 0
    x0 -- A guess at the offset along axis 1
    """
    best = shift_int(image, base, y_init, x_init)
    best_coords = y_init, x_init
    offsets = np.arange(-span, span)

    for y_offset in offsets:
        for x_offset in offsets:
            y = y_init + y_offset
            x = x_init + x_offset

            fit_coeff = shift_int(image, base, y, x)

            if fit_coeff < best:
                best = fit_coeff
                best_coords = y, x

    return best_coords


def imshift(image, coords):
    """
    Wrapper for scipy.ndimage.interpolation.shift() that takes and returns
    flattened arrays, to be compatible with scipy.optimize.curve_fit()
    """
    return shift(image.reshape(imshape), coords).ravel()


def make_pretty(image, white_level=50):
    """
    Rescale and clip an astronomical image to make features more obvious.

    Arguments:
    white_level -- the clipping level, as a multiple of the median-subtracted
    image's mean.
    """
    pretty = (image - np.median(image)).clip(0)
    pretty /= np.mean(pretty)
    pretty = pretty.clip(0, white_level)

    return pretty


def align(original_image, original_base, exact=False):
    """
    Shift an image with respect to a base along axes 0 and 1 so that they align

    Arguments:
    original_image -- the image to be shifted
    original_base -- the image to shift original_image with respect to
    exact -- If true, alignment is computed to less than 1 pixel
    """
    image = make_pretty(original_image)
    base = make_pretty(original_base)

    small_image = zoom(image, 0.1)
    small_base = zoom(base, 0.1)
    span = min(small_image.shape)//4
    y, x = align_int(small_image, small_base, span, 0, 0)

    y, x = y*5, x*5
    small_image = zoom(image, 0.5)
    small_base = zoom(base, 0.5)
    span = 10
    y, x = align_int(small_image, small_base, span, y, x)

    y, x = y*2, x*2
    span = 4
    y, x = align_int(image, base, span, y, x)

    if exact:
        (y, x), _ = curve_fit(imshift, image.ravel(), base.ravel(),
                              p0=[y, x])

    return (y, x), shift(image, (y, x))


if __name__ == '__main__':
    image_name, base_name = sys.argv[1:3]
    if len(sys.argv) > 3:
        do_exact = bool(sys.argv[3])
    else:
        do_exact = False
    base = fits.open(base_name)[0].data

    hdu = fits.open(image_name)[0]
    image = hdu.data
    head = hdu.header

    if do_exact:
        imshape = image.shape

    shift, aligned = align(image, base, exact=do_exact)

    head.append(('ALIGNED', str(datetime.now())+', '+base_name,
                 'date+time aligned, base'))

    new_hdu = fits.PrimaryHDU(data=image, header=head)
    hdulist = fits.HDUList(hdus=[new_hdu])

    name = os.path.basename(image_name)
    name = name.rsplit('.', 1)[0]
    name += '_aligned.fits'

    hdulist.writeto(name, clobber=True)
