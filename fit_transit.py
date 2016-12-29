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
    import matplotlib.pyplot as plt

    # Fold data
    if period is None:
        time_range = time.max()-time.min()
        avg_spacing = time_range/time.size
        start = avg_spacing
        stop = time_range

        periods = np.arange(start, stop, avg_spacing)

        import time as timer
        start = timer.time()
        res = []
        for period in periods:
            res.append(pdm(time, flux, period))
        print(timer.time()-start)

        start = timer.time()
        output = ctools.phase_dispersion(time, flux, periods)
        print(timer.time()-start)

        start = timer.time()
        power = periodogram(time, flux, periods)
        print(timer.time()-start)

        plt.plot(periods, output)
        plt.plot(periods, power)
        plt.show()

        exit()

        res = np.array(res)
        print(periods[res.argmin()])

        start = timer.time()
        periods, power = periodogram(time, flux, start=avg_spacing*10, stop=time_range, N=1e4)
        print(timer.time()-start)
        print(periods[power.argmax()])
        exit()
        plt.plot(periods, res)
        plt.show()
        exit()
        period = periods[power.argmax()]
        print(period)

    time %= period
    inds = np.argsort(time)
    time = time[inds]
    flux = flux[inds]

    period = 25.0

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

    planet_radius = 0.1
    # Fit everything, given the parameter guesses
    p0 = [planet_radius, 15.0, 89.0, 0.0, 90.0, 0.1, 0.3]
    import matplotlib.pyplot as plt
    plt.plot(time, flux, 'ko')
    plt.plot(time, transit_model_partial(time, *p0))

    p, cov = scipy.optimize.curve_fit(transit_model_partial, time, flux, p0=p0)

    plt.plot(time, transit_model_partial(time, *p))
    plt.show()


    p0 = [period, t0] + list(p)
    p, cov = scipy.optimize.curve_fit(transit_model, time, flux, p0=p0)

    return p

'''
def periodogram(time, data, start, stop, N=1e4):
    """
    Use scipy's lombscargle algorithm, faster on small data sets and produces
    same results as matlab's lomb()
    """
    freq = 1/(10**np.linspace(np.log10(start), np.log10(stop), N))
    nfactor = 2/(data.size * np.var(data))

    power = nfactor * lombscargle(time, data-np.mean(data), freq*2*np.pi)
    return 1/freq, power
'''

def transit_model(time, period, t0, planet_radius, semi_major_axis,
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
