"""
These functions don't fit elsewhere and are useful on their own. misc.
"""
import os
from collections import defaultdict
from astropy.io import fits


def absolute_files(directory):
    return map(os.path.abspath, next(os.walk(directory))[2])


def filenames_by_filter(directory):
    """
    Return a dict that sorts images by filter and type

    Return a useful categorization of fits files in a directory, based on the
    FILTER keyword, and if not availble it is likely that the image is instead
    filter-independent, so use IMAGETYP instead. Intended primarily for use
    with MaxIm DL-style headers. The dict that is returned has filters or image
    types as its keys, and a list of absolute file paths to matching images
    as the value. Images do not appear twice, and categorization by filter
    is preferred.
    """
    EXTENSIONS = ['fits', 'fit', 'FITS', 'FIT']

    files = absolute_files(directory)
    files = [f for f in files if f.rsplit('.', 1)[1] in EXTENSIONS]
    filedict = defaultdict([])

    for filename in files:
        head = fits.open(filename)[0].header
        if 'FILTER' in head:
            label = head['FILTER']
        else:
            label = head['IMAGETYP'].split()[0]

        filedict[label].append(filename)

    return filedict
