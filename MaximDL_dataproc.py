#!/usr/bin/env python
""""
MaximDL_dataproc makes astronomical data reduction easy, provided it is all
collected with MaximDL and has correctly identified image types. MaximDL
provides sufficient header information to identify all images based only on
header information, except maybe for flats. If a file has "flat" in the
filename (not case-sensitive), it will be used as a flat in the appropriate
filter.

For help on command line arguments:
> python MaximDL_dataproc.py -h
"""

# Future imports
from __future__ import division, print_function

# Standard library imports
import os
from collections import defaultdict
import argparse
from datetime import datetime
import warnings

# Non-standard imports
import numpy as np
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning
warnings.simplefilter('ignore', category=AstropyWarning)


def genfiles(path, file_extension='.fits'):
    for entry in os.scandir(path):
        if entry.is_file() and entry.name.endswith(file_extension):
            yield entry.path


def median_combine(filenames, bias=None, dark=None, flat=None, normalize=False, hdu_num=0):
    """median-combine a collection of fits images.
    
    Keyword arguments:
    bias -- a numpy ndarray to be subtracted from the final result
    dark -- a numpy ndarray multiplied by each image's EXPTIME and subtracted.
    flat -- a numpy ndarray to divide each image by before combining
    normalize -- divide each image by its exposure time
    """

    imshape = fits.open(filenames[0])[hdu_num].data.shape
    try:
        stack = np.empty((len(filenames),)+imshape)
    except MemoryError:
        print('Too many files to combine')
        if bias is None:
            print('file type: bias')
        elif dark is None:
            print('file type: dark')
        else:
            print('file type: flat')
        exit()

    for f, fname in enumerate(filenames):
        hdu = fits.open(fname)[hdu_num]
        image = hdu.data.astype(float)
        if bias:
            image -= bias
        if dark:
            image -= hdu.header['EXPTIME']*dark
        if flat:
            image /= flat
        if normalize:
            image /= hdu.header['EXPTIME']
        
        stack[f] = image
    
    return np.median(stack, axis=0, overwrite_input=True)


def maximdl_dataproc(input_directory, output_directory=None, hdu_num=0):

    if output_directory is None:
        output_directory = os.path.join(os.path.dirname(input_directory), 'processed')
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)

    filenames = genfiles(input_directory)
    dark_names = []
    bias_names = []
    flat_names = defaultdict(list)
    science_names = defaultdict(list)

    for filename in filenames:
        head = fits.open(filename)[0].header
        
        imtype = head['IMAGETYP'].split()[0]
        
        if imtype == 'Bias':
            bias_names.append(filename)
        elif imtype == 'Dark':
            dark_names.append(filename)
        elif (imtype == 'Flat') or ('flat' in filename.lower()):
            filt = head['FILTER']
            flat_names[filt].append(filename)
        elif imtype == 'Light':
            filt = head['FILTER']
            science_names[filt].append(filename)

    bias = median_combine(bias_names, hdu_num=hdu_num)

    dark = median_combine(dark_names, bias=bias, normalize=True, hdu_num=hdu_num)

    flats = dict()
    for filt in flat_names:
        flats[filt] = median_combine(flat_names[filt], bias=bias, dark=dark, normalize=True, hdu_num=hdu_num).clip(1)
        flats[filt] /= np.median(flats[filt])

    for filt in science_names:
        for science_name in science_names[filt]:
            input_hdu = fits.open(science_name)[0]
            image = input_hdu.data.astype(float)
            
            image -= bias
            image -= dark*input_hdu.header['EXPTIME']
            image /= flats[filt]

            output_path = os.path.join(output_directory, os.path.basename(science_name)).replace('.fits', '_proc.fits')

            head = input_hdu.header
            head.append(('PROCESSD', str(datetime.now()), 'date+time processed'))
            
            output_hdu = fits.PrimaryHDU(data=image, header=head)
            output_hdu.add_checksum()
            
            hdulist = fits.HDUList(hdus=[output_hdu])

            hdulist.writeto(output_path, clobber=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory', help='relative or absolute path to directory of all the data to process')
    parser.add_argument('-out', '--output_directory', default=None, help='relative or absolute path to a directory to place all processed data. Will be created if needed. If none is given, an output directory is created next to the input directory.')
    parser.add_argument('-hdu', '--image_hdu', type=int, default=0, help='0-based index of the image HDU to process')
    args = parser.parse_args()

    maximdl_dataproc(args.input_directory, args.output_directory, args.image_hdu)
