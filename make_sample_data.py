"""
We need some data for vectorize_starfield to work on, better make some
"""
import numpy as np
from astropy.io import fits
from tqdm import tqdm

IMAGE_SHAPE = 1024, 1024
NUM_STARS = 500
PSF_WIDTH = 1.5
STAR_FREQUENCY = 1 / 1000000
READNOISE = 5
BIAS_LEVEL = 200
DARK_CURRENT = 1000
NUM_IMAGES = 1


def gaussian(x, height, centroid, width):
    distances = np.sqrt(np.sum((x - centroid[:, None, None])**2, axis=0))
    return height * np.exp(-distances / (2 * width**2))


def make_sample_data(output_filename):
    noiseless = np.zeros(IMAGE_SHAPE)
    star_pos = np.random.random_sample((NUM_STARS, 2)) * np.array(IMAGE_SHAPE)
    star_max = np.random.exponential(STAR_FREQUENCY, NUM_STARS)

    if NUM_STARS > 0:
        star_max *= 50000/star_max.max()

    coordinates = np.mgrid[:IMAGE_SHAPE[0], :IMAGE_SHAPE[1]]

    for i in tqdm(range(NUM_STARS), desc="generating stars"):
        noiseless += gaussian(coordinates, star_max[i], star_pos[i],
                              PSF_WIDTH).reshape(noiseless.shape)

    for i in range(NUM_IMAGES):
        noise = np.random.randn(*noiseless.shape) * np.sqrt(noiseless)
        noise += np.random.normal(0, READNOISE, noiseless.shape)
        noise += DARK_CURRENT
        noise += np.random.normal(0, np.sqrt(DARK_CURRENT), noiseless.shape)
        noise += BIAS_LEVEL

        name, extension = output_filename.rsplit('.', 1)
        fits.writeto(f'{name}{i :02d}.{extension}',
                     (noiseless+noise).astype(np.int32),
                     overwrite=True)


if __name__ == "__main__":
    make_sample_data('test.fits')
