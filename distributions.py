"""
All the functions in this module are structured to be compatible with
coordinates generated from np.mgrid and all return flattened numpy ndarrays
to be compatible with scipy.optimize.curve_fit

distance_squared -- computes distances to distribution centroids
gaussian -- n-dimensional symmetric Gaussian distribution
lorentzian -- n-dimensional symmetric Lorentzian distribution
voigt -- n-dimensional symmetric Voigt distribution
planck -- planck function in SI units
"""
import numpy as np
import scipy.special

from constants import c, h, k_b


def distance_squared(coordinates, origin):
    """
    Return the square of distance to coordinates from origin.

    Convert some coordinates and a centroid to the square of distances to each
    point specified by the coordinates. This is indented mostly for use within
    this module.

    Arguments:
    coordinates -- An array-like structured as [y1,y2,y3,...,x1,x2,x3,...]
    origin -- An array-like structured as [y0,x0,z0,...]
    """

    coordinates = np.array(coordinates).ravel()

    if coordinates.size % len(origin) != 0:
        raise ValueError('Incompatible coordinates and origin')

    pos = coordinates.reshape((len(origin),-1)).copy()

    for i in range(len(origin)):
        pos[i] -= origin[i]

    return np.sum(pos**2, axis=0)


def gaussian(coordinates, height, *centroid_and_width):
    """
    Evaluate the Gaussian distribution with given parameters.

    This implements the physics-style Gaussian distribution and is therefore
    not normalized. The integral is given by height*2*np.pi*np.sqrt(width).
    
    Arguments:
    coordinates -- An array-like structured as [y1,y2,y3,...,x1,x2,x3,...],
    which represents the positions to evaluate the distribution

    height -- A normalization factor for the distribution, and the value of the
    distribution at the centroid

    centroid_and_width -- The coordinates of the centroid followed by the width
    parameter. This tuple allows the number of arguments passed to determine
    the dimensionality of the distribution that is evaluated.
    """

    width = centroid_and_width[-1]
    centroid = centroid_and_width[:-1]

    dst = distance_squared(coordinates, centroid)

    return height*np.exp(-dst/(2*width**2))


def lorentzian(coordinates, height, *centroid_and_width):
    """
    Evaluate the Lorentzian distribution with given parameters.

    This implements the physics-style Lorentzian distribution and is therefore
    not normalized. The integral is given by height*2*np.pi*np.sqrt(width).

    Arguments:
    coordinates -- An array-like structured as [y1,y2,y3,...,x1,x2,x3,...],
    which represents the positions to evaluate the distribution

    height -- A normalization factor for the distribution, and the value of the
    distribution at the centroid

    centroid_and_width -- The coordinates of the centroid followed by the width
    parameter. This tuple allows the number of arguments passed to determine
    the dimensionality of the distribution that is evaluated.
    """

    width = centroid_and_width[-1]
    centroid = centroid_and_width[:-1]

    dst = distance_squared(coordinates, centroid)

    return height*width**2/(dst + width**2)


def voigt(coordinates, height, *centroid_and_width):
    """
    Evaluate the Voigt distribution with given parameters.

    This distribution is normalized, so its integral is given by the parameter
    height.

    Arguments:
    coordinates -- An array-like structured as [y1,y2,y3,...,x1,x2,x3,...],
    which represents the positions to evaluate the distribution

    height -- A normalization factor for the distribution, and the value of the
    distribution at the centroid

    centroid_and_width -- The coordinates of the centroid followed by the width
    parameter. This tuple allows the number of arguments passed to determine
    the dimensionality of the distribution that is evaluated.
    """

    Gc, Lc = centroid_and_width[-2:]
    centroid = centroid_and_width[:-2]

    dst = distance_squared(coordinates, centroid)

    z = (dst+(abs(Lc)*1j))/(abs(Gc)*np.sqrt(2))

    return height * scipy.special.wofz(z).real/(abs(Gc)*np.sqrt(2*np.pi))


def planck(wavelength, temp):
    """
    Evaluate Planck's law.

    This function uses SI units so be careful to convert when passing a
    wavelength array in nanometers or Angstroms.

    Arguments:
    wavelength -- Wavelength values in meters
    temperature -- A temperature in kelvins
    """

    wavelength = np.array(wavelength)

    return 2*h*(c**2)/(wavelength**5*(np.expm1(h*c/(wavelength*k_b*temp))))
    total = np.zeros(arrays[0].shape)
    for arr in arrays:
        total += array