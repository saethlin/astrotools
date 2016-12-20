import argparse
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt


def fit_continuum(wavelength, flux, order=4, upper_sigma=5, lower_sigma=3):
    # Manually mask the Ca H and K lines
    mask = (abs(wavelength - 3968.5) > 6) & (abs(wavelength - 3933.7) > 6)

    while True:
        p = np.polyfit(wavelength[mask], flux[mask], order)
        continuum = np.polyval(p, wavelength[mask])

        separation = abs(flux[mask] - continuum)
        sigma = np.std(separation)
        new_mask = ((flux[mask] > continuum) & (separation < upper_sigma * sigma)) | ((flux[mask] < continuum) & (separation < lower_sigma * sigma))

        if np.all(new_mask) or np.sum(new_mask) <= order:
            break
        else:
            mask[mask] = new_mask

    continuum = np.polyval(p, wavelength)

    return continuum


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Continuum-fit some spectra.')
    parser.add_argument('wavelength_file')
    parser.add_argument('flux_file')
    parser.add_argument('--order', type=float, default=4)
    parser.add_argument('--upper_sigma', type=float, default=5)
    parser.add_argument('--lower_sigma', type=float, default=2)
    args = parser.parse_args()

    wavelength = fits.getdata(args.wavelength_file, hdu=0)[0]
    flux_hdulist = fits.open(args.flux_file)

    sample = flux_hdulist[0].data[0].copy()

    for spectrum in flux_hdulist[0].data:
        nanmask = np.invert(np.isnan(spectrum))
        spectrum[nanmask] = spectrum[nanmask]/fit_continuum(wavelength[nanmask], spectrum[nanmask], args.order, args.upper_sigma, args.lower_sigma)

    flux_hdulist.writeto(args.flux_file.replace('.fits', '_normalized.fits'), clobber=True)

    nanmask = np.invert(np.isnan(sample))
    sample /= np.max(sample)
    wavelength = wavelength[nanmask]
    sample = sample[nanmask]
    continuum = fit_continuum(wavelength, spectrum, args.order, args.upper_sigma, args.lower_sigma)

    original, = plt.plot(wavelength, sample, label='Original', fmt='k-')
    normalized, = plt.plot(wavelength, sample/continuum, label='Normalized', fmt='b-')
    continuum, = plt.plot(wavelength, continuum , label='Continuum', fmt='r-')

    plt.legend(handles=[original, normalized, continuum], loc='lower right')
    plt.showw()