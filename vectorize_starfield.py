#!/usr/bin/env python
"""
This is a demonstration script, mostly intended to showcase the power and
ease-of-use that comes from using Python for astronomy.
Yes, it is mostly comments.
"""
# Standard libarary imports first
import os

# Downloaded packages second, I like to arrange them by how often they're used.
import numpy as np
from astropy.io import fits
import scipy.ndimage
import scipy.signal
import scipy.optimize
from scipy.misc import imsave


def gaussian(coordinates, height, *centroid_and_width):
    """
    The n-dimensional symmetric Gaussian distribution
    Expects coordinates x that look like [y0,y1,x0,x1] where y0 and y1 bound the
    y-values of the output, or x looks like [y1,y2,y3,...,x1,x2,x3,...]
    gaussian Integral = height*2*np.pi*np.sqrt(width)
    """
    
    width = centroid_and_width[-1]
    centroids = centroid_and_width[:-1]
    
    pos = coordinates.reshape((len(centroids),-1)).copy()
    
    for i in range(len(centroids)):
        pos[i] -= centroids[i]
     
    dst = np.sum(pos**2,0)
    
    return height*np.exp(-dst/(2*width**2))


def genfiles(path, file_extension='fits'):
    """Produce a generator that yields files ending with file_extension in directory path"""
    for entry in os.scandir(path):
        if entry.is_file() and entry.name.endswith(file_extension):
            yield entry.path


if __name__ == "__main__":
    # Define "constants." These are anything that could be changed between usage
    # of the code, along with any time you need to pick a value to pass a function,
    # it should be defined here to avoid any confusion later about what the number
    # is or why it was chosen.
    # all caps are sometimes used to indicate that the varible should not be changed during runtime
    EXTENSIONS = ['fits','fit']
    INPUT_DIR = "../sample_data"
    OUTPUT_DIR = "."
    FILTER_WIDTH = 1.5
    APERTURE_RADIUS = 5

    files = genfiles(INPUT_DIR)

    # Open up the first file to figure out how big the images are so we can know the shape of the array to allocate
    image = fits.open(files[0])[0].data
    stack = np.empty((len(files),)+image.shape)
    stack[0] = image.copy()

    for f, fname in enumerate(files[1:]):
        stack[f] = fits.open(fname)[0].data

    # Median-combine all the images
    # The option to do median operations in-place is not always something you want
    # to do as it kind of obliterates the original data in the stack, but since we don't care
    # about the individual images, this saves time and memory, otherwise np.median will copy the array before sorting.
    stacked = np.median(stack, axis=0, overwrite_input=True)

    # Now we have an image with much better signal-to-noise, but it's still a bit
    # grainy which will really throw off the estimation of the second derivative.
    # Smoothers to the rescue!
    smooth = scipy.ndimage.gaussian_filter(stacked, FILTER_WIDTH)

    #Estimate the laplacian at each point:s
    laplace = scipy.ndimage.laplace(smooth)

    # Now we can start building our star mask, which will be a boolean array that
    # indicates points that are at the approximate centroids of stellar PSFs.
    stars = laplace < 0

    # Now we want to find where there are local mins in the derivative, as the first pass at finding stars
    # scipy.signal has a nice function for this, but it returns indices instead of a boolean array.
    # I personally prefer to use boolean arrays over indices but they're technically interchangeable
    stars_inds = scipy.signal.argrelmin(laplace)
    stars = np.zeros(stacked.shape, bool)
    stars[stars_inds] = True

    # Now we have some idea of where the tops of stars are, but if you were to take
    # a look at this array, you'd notice that it does indeed have an isolated
    # true value where the centers of star images are. Now we need to indicate
    # regions where there is enough brightness for there to be a star. The exact
    # value of this threshold is somewhat arbitrary.
    sky_value = np.median(stacked)
    signal = stacked > (sky_value + 2*np.sqrt(sky_value))

    stars = stars & signal

    # Now that we have all our stars, we need to figure out how to fit all them,
    # both what to fit them with and what data to fit. There are MANY ways to do
    # both of those things, but we can take some of the more interesting options
    # because the goal here isn't to do accurate PSF photometry, but instead to
    # recreate the general look of the image.

    # np.mgrid is a cool trick that returns two arrays that each indicate row
    # and column coordinates.
    coordinates = np.mgrid[:stacked.shape[0], :stacked.shape[1]]

    # Make an aperture mask
    coord = np.mgrid[:2*APERTURE_RADIUS+1, :2*APERTURE_RADIUS+1]
    dst = np.sum(coord**2,0)
    ap = dst <= APERTURE_RADIUS**2

    # Pull the coordinates where stars were detected, and reshape into an array
    # with two columns and whatever number of rows is needed.
    star_coordinates = np.where(stars)

    # We need an array to hold the output, which can be initalized with np.empty(),
    # because we know that if the program works everything in it will be
    # overwritten, where with output_test, that may not be the case
    star_vectors = np.empty((star_coordinates.shape[0], ))
    output_test = np.zeros(stacked.shape)

    for i, (y,x) in enumerate(star_coordinates):
        # Pull image coordinates and data necessary for the fit
        star_coordinates = coordinates[y-APERTURE_RADIUS:y+APERTURE_RADIUS+1,
                                       x-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]
        star_data = stacked[y-APERTURE_RADIUS:x+APERTURE_RADIUS+1][ap]
        
        #Make some educated guesses for the fit parameters
        guesses = [stacked[y,x]-sky_value, y, x, 1., sky_value]
        p,cov = scipy.optimize.curve_fit(star_gauss, star_coordinates, star_data, p0=guesses)
        
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
