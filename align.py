#!/usr/bin/env python
"""
This module (or script) provides tools for aligning images. The general
technique is to pick an image in a set (call it the template) and shift every
other image to match up features.

For scientific data processing do_exact should be False since it doesn't
conserve flux. It can be set to true for cosmetic image processing,
since it will generate better alignment and thus crisper combined images.

shift_int -- Quickly shifts two images and compute a similarity parameter
intalign -- Brute-force integer alignment of two images
imshift -- Wrapper for scipy.ndimage.interpolation.shift for curve_fit
align -- Align an image to a template
"""

import sys
import os
from datetime import datetime
import numpy as np
from astropy.io import fits
from scipy.optimize import curve_fit
import scipy.ndimage


def median_downsample(image, factor):
    stack = np.empty((factor, image.shape[0]//factor, image.shape[1]//factor))

    subimage = image[:image.shape[0]//factor * factor, :image.shape[1]//factor * factor]

    for i in range(factor):
        stack[i] = subimage[i::factor, i::factor]

    return np.median(stack, axis=0)


def shift_int(template, image, y, x):
    """
    Quickly shift an image with respect to a template and return a parameter
    that is minimized when the images are well aligned, and not biased towards
    large shifts as a simple sum of squares would be.

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    y -- Integer offset along axis 0
    x -- Integer offset along axis 1
    """
    y, x = int(y), int(x)

    h, w = image.shape

    new_template = template[max(0, y):min(h, h+y), max(0, x):min(w, w+x)]

    new_image = image[max(0, -y):min(h, h-y), max(0, -x):min(w, w-x)]

    return np.mean((new_template-new_image)**2)


def align_int(template, image, span=None, y_init=0, x_init=0):
    """
    Quickly find the offsets along axes 0 and 1 that align image to template. If
    the image is not aligned in coordinates between guess-span and guess+span
    this will produce an erroneous result.

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    span -- The size of the coordinate search space
    y0 -- A guess at the offset along axis 0
    x0 -- A guess at the offset along axis 1
    """
    best = shift_int(template, image, y_init, x_init)
    best_coords = y_init, x_init
    offsets = np.arange(-span, span)

    for y_offset in offsets:
        for x_offset in offsets:
            y = y_init + y_offset
            x = x_init + x_offset

            fit_coeff = shift_int(template, image, y, x)

            if fit_coeff < best:
                best = fit_coeff
                best_coords = y, x

    return best_coords


def imshift(image, y, x):
    """
    Wrapper for scipy.ndimage.interpolation.shift() that returns a
    flattened array, to be compatible with scipy.optimize.curve_fit
    """
    return scipy.ndimage.interpolation.shift(image, [y, x]).ravel()


def make_pretty(image, white_level=50):
    """Rescale and clip an astronomical image to make features more obvious.

    This rescaling massively improves the sensitivity of alignment by removing
    background and decreases the impact of hot pixels and cosmic rays by
    introducing a white clipping level that should be set so that most of
    a star's psf is clipped.

    Arguments:
    white_level -- the clipping level, as a multiple of the median-subtracted
    image's mean. For most images, 50 is good enough.
    """
    pretty = (image - np.median(image)).clip(0)
    pretty /= np.mean(pretty)
    pretty = pretty.clip(0, white_level)

    return pretty


def align(template, image, exact=False):
    """Find the coordinate offsets that align an image to a template

    The image is first downsampled with a median filter and aligned,
    then resampled with a smaller factor and aligned using the previous offset
    The median filter is critical for aligning images with a lot of small
    artifacts such as hot pixels or cosmic rays but may erase small features

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    exact -- If True, alignment is computed to sub-pixel accuracy
    """

    clipped_template = make_pretty(template)
    clipped_image = make_pretty(image)

    small_template = median_downsample(clipped_template, 10)
    small_image = median_downsample(clipped_image, 10)
    span = min(small_image.shape) // 4
    y, x = align_int(small_template, small_image, span)

    y, x = y*5, x*5
    small_template = median_downsample(template, 2)
    small_image = median_downsample(image, 2)
    span = 10
    y, x = align_int(small_template, small_image, span, y, x)

    y, x = y*2, x*2
    span = 4
    y, x = align_int(template, image, span, y, x)

    if exact:
        (y, x), _ = curve_fit(imshift, image, template.ravel(), p0=[y, x])
        return (y, x), scipy.ndimage.interpolation.shift(image, [y, x])

    else:
        return (y, x), scipy.ndimage.interpolation.shift(image, [y, x], order=0, prefilter=False)


if __name__ == '__main__':
    do_exact = False
    data_dir = '/home/ben/Downloads/yzboo/'
    paths = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.fits')]
    template = fits.getdata(paths[0])

    for path in paths[1:]:
        hdulist = fits.open(path)
        image = hdulist[0].data

        shift, aligned = align(template, image, exact=True)
        shift, aligned = align(template, image, exact=False)

        save_name = path.replace('.fits', '_aligned.fits')
        hdulist.writeto(save_name, clobber=True)
