import numpy as np
import scipy.optimize
from scipy.signal import lombscargle
import batman
import ctools
import matplotlib.pyplot as plt


def periodogram(time, data, periods):
    freq = 1/periods
    nfactor = 2/(data.size * np.var(data))

    power = nfactor * lombscargle(time, data-np.mean(data), freq*2*np.pi)
    return power


def pdm(time, data, period):
    mask = time > period
    mtime = time.copy()
    mtime[mask] = time[mask] % period
    inds = np.argsort(mtime, kind='mergesort')
    data = data[inds]
    val = np.sum(np.abs(data[1:] - data[:-1]))
    return val


def fit_transit(time, flux, period=None):

    if period is None:
        time_range = time.max()-time.min()
        avg_spacing = time_range/time.size
        start = avg_spacing
        stop = time_range

        periods = np.arange(start, stop, avg_spacing)
        
        res = []
        for period in periods:
            res.append(pdm(time, flux, period))

        output = ctools.phase_dispersion(time, flux, periods)

        power = periodogram(time, flux, periods)
        
        period = 25.0

    time %= period
    inds = np.argsort(time, kind='mergesort')
    time = time[inds]
    flux = flux[inds]

    flux /= np.median(flux)  # Data must be normalized to use the rp parameter

    planet_radius = np.sqrt(1-flux.min())

    # Estimate the location of the only dip
    t0 = np.mean(time[flux < 1-(1-flux.min())/2])
    
    def transit_model_partial(time, planet_radius, semi_major_axis,
                              inclination, eccentricity, longitude_of_periastron,
                              limb_linear, limb_quadratic):
        params = batman.TransitParams()
        params.per = period
        params.t0 = t0
        params.rp = planet_radius
        params.a = semi_major_axis
        params.inc = inclination
        params.ecc = abs(eccentricity) % 1
        params.w = longitude_of_periastron
        params.u = [limb_linear, limb_quadratic]
        params.limb_dark = 'quadratic'

        return batman.TransitModel(params, time).light_curve(params)

    # Fit everything, given the parameter guesses
    p0 = [planet_radius, 15.0, 89.0, 0.0, 90.0, 0.1, 0.3]

    p, cov = scipy.optimize.curve_fit(transit_model_partial, time, flux, p0=p0)
    
    p0 = [period, t0] + list(p)
    p, cov = scipy.optimize.curve_fit(transit_model, time, flux, p0=p0)

    return p


def transit_model(time, period, t0, planet_radius, semi_major_axis,
                  inclination, eccentricity, longitude_of_periastron,
                  limb_linear, limb_quadratic):

    params = batman.TransitParams()
    
    print(period)

    params.per = period
    params.t0 = t0
    params.rp = planet_radius
    params.a = semi_major_axis
    params.inc = inclination
    params.ecc = abs(eccentricity) % 1
    params.w = longitude_of_periastron
    params.u = [limb_linear, limb_quadratic]
    params.limb_dark = 'quadratic'

    model = batman.TransitModel(params, time)
    return model.light_curve(params)


if __name__ == '__main__':
    np.random.seed(1)
    params = batman.TransitParams()
    params.t0 = 1.0
    params.per = 25.0
    params.rp = 0.1
    params.a = 15.0
    params.inc = 90.0
    params.ecc = 0.0
    params.w = 90.0
    params.u = [0.1, 0.3]
    params.limb_dark = 'quadratic'

    time = np.linspace(0, 100, 10000)
    model = batman.TransitModel(params, time, nthreads=1)
    flux = model.light_curve(params)
    flux += np.random.randn(time.size) * 0.001

    #import matplotlib.pyplot as plt
    #plt.plot(time, flux, 'ko')
    #plt.show()

    print(fit_transit(time, flux))
