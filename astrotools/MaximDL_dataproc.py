#!/usr/bin/env python
'''
MaximDL_dataproc makes astronomical data reduction easy, provided it is all
collected with MaximDL and has correctly identified image types. MaximDL
provides sufficient header information to identify all images based only on
header information, so for this script all relevant data files should be
placed in one directory. As an example, consdier the directory data_directory.

Command line usage -- >python MaximDL_dataproc.py data_directory

This script will output all the reduced data it identifies as science images
to a directory it creates, in this example called data_directory_reduced.

This script will NOT function properly if
'''

# Future imports
from __future__ import division,print_function

# Standard library imports
import os
from collections import defaultdict
import argparse
from datetime import datetime

# Non-standard imports
import numpy as np
from astropy.io import fits


def abspath_in_dir(directory):
    '''Return a list of absolute file paths to all fits files in directory'''
    extensions = ['fit', 'fits']
    if os.path.isabs(directory):
        root = directory
    else:
        root = os.path.join(os.getcwd(), directory)

    rel_files = next(os.walk(directory))[2]

    return [os.path.join(root, f) for f in rel_files if f.rsplit('.',1)[-1].lower() in extensions]


def median_combine(filenames, bias=None, dark=None, flat=None, normalize=False, hdu=0):
    '''
    Use median to combine a set of fits files primaryHDU image data.
    
    Keyword arguments:
    bias -- a numpy ndarray to be subtracted from the final result
    dark -- a numpy ndarray multiplied by each image's EXPTIME and subtracted.
            This allows combining images of unequal exposure time.
    flat -- a numpy ndarray to divide each image by before combining
    normalize -- if true, divide each image by its exposure time
    '''

    imshape = fits.open(filenames[0])[hdu].data.shape
    try:
        stack = np.empty((len(filenames),)+imshape)
    except MemoryError:
        print('Too many files')

    for f,fname in enumerate(filenames):
        hdu = fits.open(fname)[hdu]
        image = hdu.data
        if bias is not None:
            image -= bias
        if dark is not None:
            image -= hdu.header['EXPTIME']*dark
        if flat is not None:
            image /= flat
        if normalize:
            image /= hdu.header['EXPTIME']
        
        stack[f] = image
    
    return np.median(stack, axis=0, overwrite_input=True)


def MaximDL_dataproc(directory, hdu=0):

    filenames = abspath_in_dir(directory)
    dark_names = []
    bias_names = []
    flat_names = defaultdict([])
    science_names = defaultdict([])

    for filename in filenames:
        head = fits.open(filename)[0].header
        
        imtype = head['IMAGETYP'].split()[0]
        
        if imtype == 'Bias':
            bias_names.append(filename)
        elif imtype == 'Dark':
            dark_names.append(filename)
        elif imtype == 'Flat':
            filt = head['FILTER']
            flat_names[filt].append(filename)
        elif imtype == 'Light':
            filt = head['FILTER']
            science_names[filt].append(filename)

    bias = median_combine(bias_names, hdu=hdu)

    dark = median_combine(dark_names, bias=bias, normalize=True, hdu=hdu)

    flats = dict()
    for filt in flat_names:
        flats[filt] = median_combine(flats[filt], bias=bias, dark=dark, normalize=True, hdu=hdu).clip(1)
        flats[filt] /= np.median(flats[filt], hdu=hdu)

    for filt in science_names:
        for science_name in science_names[filt]:
            image_hdu = fits.open(science_name)[0]
            image = image_hdu.data
            
            image -= bias
            image -= dark*hdu.header['EXPTIME']
            image /= flats[filt]

            new_name = os.path.basename(science_name)
            new_name = new_name.rsplit('.',1)[0]
            
            head = hdu.header
            head.append(('PROCESSD', str(datetime.now()), 'date+time processed'))
            
            hdu = fits.PrimaryHDU(data=image, header=head)
            hdu.add_checksum()
            
            hdulist = fits.HDUList(hdus=[hdu])

            if not os.path.isdir('processed'):
                os.mkdir('processed')
            hdulist.writeto(os.path.join('processed', new_name+'_proce.fits'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory', help='relative or absolute path to directory of all the data to process')
    parser.add_argument('output_directory', help='relative or absolute path to a directory to place all processed data. Will be created if needed.')
    args = parser.parse_args()

    MaximDL_dataproc(args.input_directory, args.output_directory)