#!/usr/bin/env python
'''
This is a demonstration script, mostly intended to showcase the power and
ease-of-use that comes from using Python for astronomy.
Yes, it is mostly comments.
'''
#Future imports first- these allow *some* compatiblity across Python versions
#This is the only time PEP 0008 suggests using "from x import y,z"
from __future__ import division,print_function

#Standard libarary imports first
import os

#Downloaded packages second, I like to arrange them by how often they're used.
#Import numpy as np because it's standard and cuts out a few characters
import numpy as np
#One of two common python plotting libraries- note that this statement does
#NOT give access to other functions like matplotlib.rc()
from matplotlib import pyplot as plt
#Also a standard import for fits input/output
from astropy.io import fits
#This does a lot of cool things for images, I encourage you to poke around
#http://docs.scipy.org/doc/scipy/reference/ndimage.html
from scipy import ndimage
#For saving images
from scipy.misc import imsave

#Function definitions- won't be used until later

def gaussian(coordinates, height, *centroid_and_width):
    """
    The n-dimensional symmetric Gaussian distribution
    Expects coordinates x that look like [y0,y1,x0,x1] where y0 and y1 bound the
    y-values of the output, or x looks like [y1,y2,y3,...,x1,x2,x3,...]
    gaussian Integral = height*2*np.pi*np.sqrt(width)
    """
    
    width = centroid_and_width[-1]
    centroid = centroid_and_width[:-1]
    
    pos = coordinates.reshape((len(centroids),-1)).copy()
    
    for i in range(len(centroids)):
        pos[i] -= centroids[i]
     
    dst = np.sum(pos**2,0)
    
    return height*np.exp(-dst/(2*width**2))


if __name__ == "__main__":
    #Define "constants." These are anything that could be changed between usage
    #of the code, along with any time you need to pick a value to pass a function,
    #it should be defined here to avoid any confusion later about what the number
    #is or why it was chosen.
    XTENSIONS = ['fits','fit']
    INPUT_DIR = "../sample_data"
    OUTPUT_DIR = "."
    FILTER_WIDTH = 1.5
    APERTURE_RADIUS = 5

    #Python list comprehension: it pretty much does exactly what it sounds like;
    #a list of all files in the target directory if the characters to the right of
    #the rightmost . are in my list of valid extensions.
    files = [TARGET_DIR+'/'+f for f in os.listdir(TARGET_DIR) if
             f.rsplit('.',1)[-1].lower() in XTENSIONS]

    #Open up the first file to figure out how big the images are so we can
    #quickly allocate an array to store them in, instead of appending.
    #Appending is evil.
    image = fits.open(files[0])[0].data
    stack = np.empty((len(files),)+image.shape)
    stack[0] = image.copy()

    #enumerate() is wonderful and something I only learned about ~1 week before
    #writing this. Instead of having to choose whether you iterate over the
    #actual contents of files and range(len(files)) which would give you an index,
    #you get to do both
    for f,fname in enumerate(files[1:]):
        #Open a file using astropy's fits.open, which returns a hdulist
        #I know that the first hdu (the only) is the one I want, and I want only
        #the data from it, not the header.
        stack[f] = fits.open(fname)[0].data

    #Median-combine all the images
    #The option to do median operations in-place is not always something you want
    #to do as it kind of obliterates the original data, but since we don't care
    #about the individual images, this saves time and memory.
    stacked = np.median(stack, axis=0, overwrite_input=True)

    #Now we have an image with much better signal-to-noise, but it's still a bit
    #grainy which will really throw off the estimation of the second derivative.
    #Smoothers to the rescue!
    smooth = ndimage.gaussian_filter(stacked,FILTER_WIDTH)

    #Estimate the laplacian at each point:s
    laplace = ndimage.laplace(smooth)

    #Now we can start building our star mask, which will be a boolean array that
    #indicates points that are at the approximate centroids of stellar PSFs.
    stars = laplace < 0

    #Now we want to find where there are local mins in the array. There are a few
    #ways to do this, but I'm going to use the one that showcases using numpy
    #memory-intensive processes instead of loops to do fast computation.
    row_buffer = np.zeros(laplace.shape[0])
    col_buffer = np.zeros(laplace.shape[1][None,:])
    above = np.vstack((laplace[1:],row_buffer[:]))
    below = np.vstack((row_buffer[:,:],laplace[:-1]))
    right = np.hstack((laplace[1:],row_buffer[:,:]))

    stars = stars & (laplace < above) & (laplace < below) & (laplace < right) & (
            laplace < left)

    #Now we have some idea of where the tops of stars are, but if you were to take
    #a look at this array, you'd notice that it does indeed have an isolated
    #true value where the centers of star images are. Now we neeed to indicate
    #regions where there is enough brightness for there to be a star. The exact
    #value of this threshold is somewhat arbitrary.
    sky_value = np.median(stacked)
    signal = stacked > (sky_value + 2*np.sqrt(sky_value))

    stars = stars & signal

    #Now that we have all our stars, we need to figure out how to fit all them,
    #both what to fit them with and what data to fit. There are MANY ways to do
    #both of those things, but we can take some of the more interesting options
    #because the goal here isn't to do accurate PSF photometry, but instead to
    #recreate the general look of the image.

    #np.mgrid is a cool trick that returns two arrays that each indicate row
    #and column coordinates.
    coordinates = np.mgrid[:stacked.shape[0],:stacked.shape[1]]

    #Make an aperture mask
    coord = np.mgrid[:2*APERTURE_RADIUS+1,:2*APERTURE_RADIUS+1]
    dst = np.sum(coord**2,0)
    ap = dst <= APERTURE_RADIUS**2

    #Pull the coordinates where stars were detected, and reshape into an array
    #with two columns and whatever number of rows is needed.
    star_coordinates = coordinates[:,stars].reshape((-1,2))

    #We need an array to hold the output, which can be initalized with np.empty(),
    #because we know that if the program works everything in it will be
    #overwritten, where with output_test, that may not be the case
    star_vectors = np.empty((star_coordinates.shape[0], ))
    output_test = np.zeros(stacked.shape)

    for i, (y,x) in enumerate(star_coordinates):
        #Pull image coordinates and data necessary for the fit
        star_coordinates = coordinates[y-APERTURE_RADIUS:y+APERTURE_RADIUS+1,
                                       x-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]
        star_data = stacked[y-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]
        
        #Make some educated guesses for the fit parameters
        guesses = [stacked[y,x]-sky_value, y, x, 1., sky_value]
        p,cov = curve_fit(star_gauss, star_coordinates, star_data, p0=guesses)
        
        star_vectors[i] = p

        output_test[y-APERTURE_RADIUS:y+APERTURE_RADIUS+1,
                    x-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap] += star_gauss(
                    star_coordinates, *p)

    #Save the star fit data, can be read into a numpy array with np.load()
    np.save('vectorized.npy',star_vectors)

    #Save an image preview of the output, scaled
    #Use PNG format, because it is losslessly compressed, and compute the
    #natural log of the data (log10 is log base 10) to make dimmer features
    #more visible
    imsave('vectorized.png',np.log(output_test))
