import os
import numpy as np
from astropy.io import fits
import cv2
from scipy.misc import imsave


def prettify(image, white_level=50):
    """
    Rescale an image and convert dtype for comparability with findTransformECC

    Arguments:
    white_level -- clipping level in multiples of the median-subtracted image's mean.
    """
    scaled = (image - np.median(image)).clip(0)
    scaled /= np.mean(scaled)
    scaled.clip(0, white_level, out=scaled)

    return scaled.astype(np.float32)


def align_image(template, image, warp_matrix=None):
    # Clean sky, apply clipping to enhance contrast, and convert to a dtype that cv2 will accept
    clipped_template = prettify(template)
    clipped_image = prettify(image)

    if warp_matrix is None:
        warp_matrix = np.eye(2, 3, dtype=np.float32)  # findTransformECC requires 32-bit float

    warp_mode = cv2.MOTION_TRANSLATION  # No rotation
    iterations = 100
    termination_eps = 1e-3

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iterations, termination_eps)

    cc, warp_matrix = cv2.findTransformECC(clipped_template, clipped_image, warp_matrix, warp_mode, criteria)
    warp_matrix = np.around(warp_matrix)  # Round the warp matrix to remove interpolation and conserve flux

    aligned = cv2.warpAffine(image, warp_matrix, image.shape[::-1], flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)

    return aligned, warp_matrix


if __name__ == '__main__':
    target_path = '/home/ben/Downloads/yzboo/'
    paths = [os.path.join(target_path, entry) for entry in os.listdir(target_path) if entry.endswith('.fits')]

    template = fits.getdata(paths[0])

    warp_matrix = None
    for path in paths[1:]:
        image = fits.getdata(path)
        aligned, warp_matrix = align_image(template, image, warp_matrix)

        diagnostic = np.dstack([prettify(template), prettify(aligned), np.zeros_like(template)])
        imsave(path.replace('.fits', '.png'), diagnostic)
