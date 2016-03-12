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

#Future imports
from __future__ import division,print_function

#Standard library imports
import os
from datetime import datetime

#Non-standard imports
import numpy as np
from astropy.io import fits


def abspath_in_dir(directory):
    '''Return a list of absolute file paths to all fits files in directory'''
    extensions = ['FIT','FITS','fit','fits']
    if directory.startswith('/'):
        root = directory
    else:
        root = os.getcwd()+'/'+directory
    
    if root[-1] != '/':
        root = root+'/'
    
    rel_files = next(os.walk(directory))[2]

    return [root+f for f in rel_files if f.rsplit('.',1)[-1] in extensions]


def median_combine(filenames,bias=None,dark=None,flat=None,normalize=False):
    '''
    Use median to combine a set of fits files primaryHDU image data.
    
    Keyword arguments:
    bias -- a numpy ndarray to be subtracted from the final result
    dark -- a numpy ndarray multiplied by each image's EXPTIME and subtracted.
            This allows combining images of unequal exposure time.
    flat -- a numpy ndarray to divide each image by before combining
    normalize -- if true, divide each image by its exposure time
    
    '''
    filenames = np.array(filenames)
    
    imshape = fits.open(filenames[0])[0].data.shape
    stack = np.empty((imshape+(len(filenames),)))
    
    for f,fname in enumerate(filenames):
        hdu = fits.open(fname)[0]
        image = hdu.data
        if bias is not None:
            image -= bias
        if dark is not None:
            image -= hdu.header['EXPTIME']*dark
        if flat is not None:
            image /= flat
        if normalize:
            image /= hdu.header['EXPTIME']
        
        stack[:,:,f] = image
    
    return np.median(stack,2,overwrite_input=True)


def MaximDL_dataproc(directory):

    filenames = abspath_in_dir(directory)
    dark = []
    bias = []
    flats = dict()
    science = dict()

    for filename in filenames:
        head = fits.open(filename)[0].header
        
        imtype = head['IMAGETYP'].split()[0]
        
        if imtype == 'Bias':
            bias.append(filename)
        elif imtype == 'Dark':
            dark.append(filename)
        elif imtype == 'Flat':
            filt = head['FILTER']
            if filt not in flats:
                flats[filt] = []
            flats[filt].append(filename)
        elif imtype == 'Light':
            filt = head['FILTER']
            if filt not in science:
                science[filt] = []
            science[filt].append(filename)

    bias = median_combine(bias)

    dark = median_combine(dark,bias=bias,normalize=True)

    for filt in flats:
        flats[filt] = median_combine(flats[filt],bias=bias,dark=dark,normalize=True).clip(1)
        flats[filt] /= np.median(flats[filt])

    for filt in science:
        for i in range(len(science[filt])):
            hdu = fits.open(science[filt][i])[0]
            image = hdu.data
            
            image -= bias
            image -= dark*hdu.header['EXPTIME']
            image /= flats[filt]
            
            name = science[filt][i].rsplit('/',1)[-1]
            name = name.rsplit('.',1)[0]
            
            head = hdu.header
            head.append(('PROCESSD',str(datetime.now()),'date+time processed'))
            
            hdu = fits.PrimaryHDU(data=image,header=head)
            hdu.add_checksum()
            
            hdulist = fits.HDUList(hdus=[hdu])

            if not os.path.isdir('processed'):
                os.mkdir('processed')
            hdulist.writeto('processed/'+name+'_proc.fits')
