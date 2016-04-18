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
import warnings

# Non-standard imports
import numpy as np
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning
warnings.simplefilter('ignore', category=AstropyWarning)


def absolute_files(directory):
    root = os.path.abspath(directory)
    return [os.path.join(root, f) for f in next(os.walk(directory))[2]]


def median_combine(filenames, bias=None, dark=None, flat=None, normalize=False, hdu_num=0):
    '''
    Use median to combine a set of fits files primaryHDU image data.
    
    Keyword arguments:
    bias -- a numpy ndarray to be subtracted from the final result
    dark -- a numpy ndarray multiplied by each image's EXPTIME and subtracted.
            This allows combining images of unequal exposure time.
    flat -- a numpy ndarray to divide each image by before combining
    normalize -- if true, divide each image by its exposure time
    '''
    imshape = fits.open(filenames[0])[hdu_num].data.shape
    try:
        stack = np.empty((len(filenames),)+imshape)
    except MemoryError:
        print('Too many files')

    for f,fname in enumerate(filenames):
        hdu = fits.open(fname)[hdu_num]
        image = hdu.data.astype(float)
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


def MaximDL_dataproc(input_directory, output_directory=None, hdu_num=0):

    if output_directory is None:
        output_directory = os.path.join(os.path.dirname(input_directory), 'processed')
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)

    filenames = absolute_files(input_directory)
    dark_names = []
    bias_names = []
    flat_names = defaultdict(list)
    science_names = defaultdict(list)

    for filename in filenames:
        head = fits.open(filename)[0].header
        
        imtype = head['IMAGETYP'].split()[0]
        
        if imtype == 'Bias':
            bias_names.append(filename)
        elif imtype == 'Dark' and head['EXPTIME'] > 1:
            dark_names.append(filename)
        elif imtype == 'Flat' or 'flat' in filename.lower():
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

            new_name = os.path.basename(science_name)
            new_name = new_name.rsplit('.',1)[0]
            
            head = input_hdu.header
            head.append(('PROCESSD', str(datetime.now()), 'date+time processed'))
            
            output_hdu = fits.PrimaryHDU(data=image, header=head)
            output_hdu.add_checksum()
            
            hdulist = fits.HDUList(hdus=[output_hdu])

            hdulist.writeto(os.path.join(output_directory, new_name+'_proc.fits'), clobber=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory', help='relative or absolute path to directory of all the data to process')
    #parser.add_argument('output_directory', help='relative or absolute path to a directory to place all processed data. Will be created if needed.')
    args = parser.parse_args()

    MaximDL_dataproc(args.input_directory)