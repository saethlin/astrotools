#!/usr/bin/env python
"""
This module (or script) provides tools for aligning images. The general
technique is to pick an image in a set (the template) and shift every
other image to match up features.

shift_int -- Quickly shifts two images and compute a similarity parameter,
lower is better
align_int -- Brute-force integer alignment of two images within bounds
make_pretty -- Apply median-based sky removal and white threshold
align -- Align an image to a template
"""

import os
import operator
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import numba
from scipy.ndimage.interpolation import shift


def median_downsample(image, factor):
    """
    Simultaneously downsample and median filter an image.
    Each pixel at [y,x] in the returned image is the median of
    the region [y*factor:(y+1)*factor, x*factor:(x+1)*factor].

    This can result in some significant loss of data but will preserve
    most of the large features in an image.
    """
    stack = np.empty((factor, image.shape[0]//factor, image.shape[1]//factor))

    subimage = image[:image.shape[0]//factor * factor, :image.shape[1]//factor * factor]

    for i in range(factor):
        stack[i] = subimage[i::factor, i::factor]

    return np.median(stack, axis=0)


@numba.jit(nopython=True, cache=True, nogil=True)
def shift_int(template, image, y, x):
    """
    Quickly shift an image with respect to a template and return a parameter
    that is minimized when the images are well aligned. The sum of squres is
    not applicable here because that favors reducing the number of pixels
    in the image, which is the effect of applying a large shift.

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    y -- Integer offset along axis 0
    x -- Integer offset along axis 1
    """
    y, x = int(y), int(x)
    h, w = image.shape

    shifted_template = template[max(0, y):min(h, h+y), max(0, x):min(w, w+x)]
    shifted_image = image[max(0, -y):min(h, h-y), max(0, -x):min(w, w-x)]

    output = 0.0
    for row in range(shifted_image.shape[0]):
        for col in range(shifted_image.shape[1]):
            output += (shifted_template[row, col] - shifted_image[row, col])**2

    return output/shifted_image.size


def align_int(template, image, span=None, y_init=0, x_init=0):
    """
    Find integer offsets along axes 0 and 1 that align image to template. If
    the image is not aligned between guess-span and guess+span, this will
    produce an erroneous result.

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    span -- The size of the coordinate search space
    y0 -- A guess at the offset along axis 0
    x0 -- A guess at the offset along axis 1
    """
    offsets = np.arange(-span, span)

    results = []
    coords = []
    with ThreadPoolExecutor() as executor:
        for y_offset in offsets:
            for x_offset in offsets:
                args = (template, image, y_init+y_offset, x_init+x_offset)
                results.append(executor.submit(shift_int, *args))
                coords.append([y_init + y_offset, x_init + x_offset])

    results = [x.result() for x in results]
    results = zip(results, coords)
    best_result = min(results, key=operator.itemgetter(0))
    return best_result[1]


def make_pretty(image, white_level=50):
    """Rescale and clip an astronomical image to make features more obvious.

    This rescaling massively improves the sensitivity of alignment by
    removing background and decreases the impact of hot pixels and cosmic
    rays by introducing a white clipping level that should be set so that
    most of a star's psf is clipped.

    Arguments:
    white_level -- the clipping level as a multiple of the median-subtracted
    image's mean. For most images, 50 is good enough.
    """
    pretty = (image - np.median(image)).clip(0)
    pretty /= np.mean(pretty)
    pretty = pretty.clip(0, white_level)

    return pretty


def align(template, image):
    """Find the coordinate offsets that align an image to a template

    The image is first downsampled with a median filter and aligned,
    then resampled with a smaller factor and aligned using the previous
    offset. The median filter is critical for aligning images with a lot
    of small artifacts such as hot pixels or cosmic rays but may erase
    small features

    Arguments:
    template -- The image to match
    image -- The input image that is shifted
    """
    clipped_template = make_pretty(template)
    clipped_image = make_pretty(image)

    small_template = median_downsample(clipped_template, 10)
    small_image = median_downsample(clipped_image, 10)
    span = min(small_image.shape) // 4
    y, x = align_int(small_template, small_image, span)

    y, x = y*5, x*5
    small_template = median_downsample(clipped_template, 2)
    small_image = median_downsample(clipped_image, 2)
    span = 10
    y, x = align_int(small_template, small_image, span, y, x)

    y, x = y*2, x*2
    span = 4
    y, x = align_int(clipped_template, clipped_image, span, y, x)

    return (y, x), shift(image, [y, x], order=0, prefilter=False)


if __name__ == '__main__':
    from astropy.io import fits

    data_dir = '/home/ben/Downloads/yzboo/'
    paths = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.fits')]
    paths.sort()
    template = fits.getdata(paths[0])

    for path in paths[1:]:
        hdulist = fits.open(path)
        image = hdulist[0].data

        offset, aligned = align(template, image)

        save_name = path.replace('.fits', '_aligned.fits')
        hdulist[0].data = aligned
        hdulist.writeto(save_name, clobber=True)