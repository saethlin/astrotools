#!/usr/bin/env python

import numpy as np
from astropy.io import fits
import scipy.ndimage
import scipy.fftpack
import scipy.optimize


def getcentroid(pos,im):
    '''
    Image centroid from image points im that match with a 2-d array pos, which
    contains the locations of each point in an all-positive coordinate system.
    '''
    return np.sum(im*pos[0])/np.sum(im),np.sum(im*pos[1])/np.sum(im)



def flatfunc(centroid,p0,p1,p2):
    '''
    Intended only for use with detrend().
    '''
    return p0*centroid[:,0] + p1*centroid[:,1] + p2



def detrend(flux,centroid):
    '''
    Detrend flux against centroid points. Returns normalized flux.
    '''
    for f in range(flux.shape[0]):
        p,cov = scipy.optimize.curve_fit(flatfunc,centroid[f],flux[f])
        flux[f] /= flatfunc(centroid[f],*p)
        flux[f] /= np.median(flux[f])
    return flux


def photometer(files,coords,obj,sky=None):
    '''
    Aperture photometery on images contained in files at initial star positions
    near coords. Returns flux of each star with corresponding centroid locations.
    '''
    centroid = np.zeros((coords.shape[0],len(files),2))
    flux = np.zeros((coords.shape[0],len(files)))
    
    centroid[:,-1] = coords
    
    if sky == None:
        sky = obj
    has_sky = sky != None
    
    pos = np.mgrid[-sky:sky+1,-sky:sky+1]
    dst = np.sqrt(np.sum(pos,0))
    
    objap = dst <= obj
    skyap = dst <= sky
    
    objsize = np.sum(objap)
    
    for f in range(len(files)):
        im = fits.open(files[f])[0].data
        
        if not has_sky:
            skyval = np.median(im)*objsize
        
        for c in range(coords.shape[0]):
            #Could start new subprocess here
            y,x = centroid[c,f-1]
            
            if y > 0 and x > 0 and y < im.shape[0] and x < im.shape[1]:
                
                y,x = seekmax(im,y,x)
                
                y,x = getcentroid(*getstar(im,y,x))

            if y > sky and x > sky and y < im.shape[0]-sky-1 and x < im.shape[1]-sky-1:
                
                if has_sky:
                    skyval = np.median(im[y-sky:y+sky+1,x-sky:x+sky+1][skyap]) * objsize
                
                flux[c,f] = np.sum(im[y-sky:y+sky+1,x-sky:x+sky+1][objap]) - skyval
                
                centroid[c,f] = y,x
    
    return flux,centroid


def find_stars(data):
    #If passed a list, stack and median-combine first
    if isinstance(data,list):
        warps,aligned = astt.align(data)
        aligned = np.asarray(aligned)
        im = np.median(aligned,0)
    else:
        im = data
    
    
    #Denoise the image with a fourier filter
    fourier = np.fft.fft2(im)
    fourier = np.fft.fftshift(fourier)
    print(fourier.max())
    fits.writeto('fourier.fits',abs(fourier),clobber=True)
    exit()
    
    #Compute the second derivative at every point
    laplace = ndimage.laplace(smoothed)
    
    #Image should be concave down where there are stars
    stars = derivative < 0
    
    #Stars should also be a local min in the laplacian
    row_buffer = np.zeros(laplace.shape[0])
    col_buffer = row_buffer[None,:]
    above = np.vstack((laplace[1:],row_buffer[:]))
    below = np.vstack((row_buffer[:,:],laplace[:-1]))
    right = np.hstack((laplace[1:],row_buffer[:,:]))

    stars = stars & (laplace < above) & (laplace < below) & (laplace < right)
    
    #Denoise the image with a fourier filter
    print(np.std(im))
    fourier = scipy.fftpack.rfft(im)
    fits.writeto('fft.fits',fourier,clobber=True)
    fourier[0] = 0
    fourier[-1] = 0
    fourier[:,0] = 0
    fourier[:,-1] = 0
    test = scipy.fftpack.ifft(fourier).real
    fits.writeto('ifft.fits',test,clobber=True)
    print(np.std(test))
    exit()
    
    #Compute the second derivative at every point
    laplace = ndimage.laplace(smoothed)
    
    #Image should be concave down where there are stars
    stars = derivative < 0
    
    #Stars should also be a local min in the laplacian
    row_buffer = np.zeros(laplace.shape[0])
    col_buffer = np.zeros(laplace.shape[1][None,:])
    above = np.vstack((laplace[1:],row_buffer[:]))
    below = np.vstack((row_buffer[:,:],laplace[:-1]))
    right = np.hstack((laplace[1:],row_buffer[:,:]))

    stars = stars & (laplace < above) & (laplace < below) & (laplace < right) & (laplace < left)

    #Pick a sky value
    sky = np.median(im)

    #Sigma threshold for sky level
    signal = im > (sky + sky_sigma*np.sqrt(sky))
    
    #Use binary erosion and propagation to remove isolated points of signal
    eroded_signal = binary_erosion(signal)
    signal = binary_propagation(eroded_signal,mask=signal)
    
    #Stars are only where signal is significant
    stars = stars & signal
    
    return stars

'''
image = fits.open('test.fits')[0].data
find_stars(image)


from astropy.io import fits
im = fits.open('sample_data/test_data0.fits')[0].data
find_stars(im)
'''

'''
Simple aperture photometry on image files
'''
def do_photometry(files, program_stars):
    #Find stars
    
    #Remove program stars from list
    
    #Determine optimal aperture (s)
    
    #Photometer everything
    
    #Detrend against position
    
    #Detrend against temperature, maybe other things
    
    #Find good standards and correct
    
    #Return flux and time arrays
    pass
