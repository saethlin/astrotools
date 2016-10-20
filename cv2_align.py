import numpy as np
from astropy.io import fits
import cv2
from scipy.misc import imsave


def make_pretty(image, white_level=50):
    """
    Rescale and clip an astronomical image to make features more obvious.

    Arguments:
    white_level -- the clipping level, as a multiple of the median-subtracted
    image's mean.
    """
    pretty = (image - np.median(image)).clip(0)
    pretty /= np.mean(pretty)
    pretty = pretty.clip(0, white_level)

    return pretty


image1 = fits.getdata('/home/ben/Downloads/yzboo/yzboo.00000030.fits')
image2 = fits.getdata('/home/ben/Downloads/yzboo/yzboo.00000031.fits')

image1 = make_pretty(image1)
image2 = make_pretty(image2)

image1 *= 255/image1.max()
image2 *= 255/image2.max()

image1 = image1.astype(np.uint8)
image2 = image2.astype(np.uint8)


# Here begins the learnopencv.com example script
# Find size of image1
sz = image1.shape

# Define the motion model
warp_mode = cv2.MOTION_TRANSLATION

# Define 2x3 or 3x3 matrices and initialize the matrix to identity
if warp_mode == cv2.MOTION_HOMOGRAPHY:
    warp_matrix = np.eye(3, 3, dtype=np.float32)
else:
    warp_matrix = np.eye(2, 3, dtype=np.float32)

# Specify the number of iterations.
number_of_iterations = 5000

# Specify the threshold of the increment
# in the correlation coefficient between two iterations
termination_eps = 1e-10

# Define termination criteria
criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)

# Run the ECC algorithm. The results are stored in warp_matrix.
(cc, warp_matrix) = cv2.findTransformECC(image1, image2, warp_matrix, warp_mode, criteria)

if warp_mode == cv2.MOTION_HOMOGRAPHY:
    # Use warpPerspective for Homography 
    image2_aligned = cv2.warpPerspective(image2, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
else:
    # Use warpAffine for Translation, Euclidean and Affine
    image2_aligned = cv2.warpAffine(image2, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)


# Ben's nifty way to look at how well two images are aligned
imsave('aligned.png', np.dstack([image1, image2_aligned, np.zeros_like(image1)]))
imsave('images.png', np.dstack([image1, image2, np.zeros_like(image1)]))

