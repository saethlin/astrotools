'''
TODO:
Median trimmer
'''
import numpy as np


def mad(arr,axis=None):
    mid = np.median(arr,axis=axis)
    return np.median(abs(arr-mid),axis=axis)


def bin_median(x,y,nbin):
    binsize = (x.max()-x.min()) / (2*nbin)
    bin_centers = np.linspace(x.min()+binsize,x.max()-binsize,nbin)
    
    binned = np.empty(nbin)
    error = np.empty(nbin)    
    for c in range(bin_centers.size):
        mask = (x >= bin_centers[c]-binsize) & (x <= bin_centers[c]+binsize)
        binned[c] = np.median(y[mask])
        error[c] = np.std(y[mask])/np.sqrt(np.sum(mask))
        
    return bin_centers,binned,error


def bin_mean(x,y,nbin):
    binsize = (x.max()-x.min()) / (2*nbin)
    bin_centers = np.linspace(x.min()+binsize,x.max()-binsize,nbin)
    
    binned = np.empty(nbin)
    error = np.empty(nbin)
    for c in range(bin_centers.size):
        mask = (x >= bin_centers[c]-binsize) & (x <= bin_centers[c]+binsize)
        binned[c] = np.mean(y[mask])
        error[c] = np.std(y[mask])/np.sqrt(np.sum(mask))
    
    return bin_centers,binned,error


def bin_sum(data, nbin):
    binsize = (data.max()-data.min()) / (2*nbin)
    bin_centers = np.linspace(data.min()+binsize, data.max()-binsize, nbin)

    binned = np.empty(nbin)
    for c in range(bin_centers.size):
        mask = (data >= bin_centers[c]-binsize) & (data <= bin_centers[c] + binsize)
        binned[c] = np.sum(mask)

    return bin_centers, binned


def csmooth(x, y, interval, eval=None):
    if eval is None:
        eval = x
    n_points = np.zeros(eval.size)
    sums = np.zeros(eval.size)

    for i in range(y.size):
        mask = (x > x[i]) & (x < x[i]+interval)

        if np.sum(mask) > 4:
            p = np.polyfit(x[mask], y[mask], 3)

            eval_mask = (eval > x[i]) & (eval < x[i]+interval)

            sums[eval_mask] += np.polyval(p, eval[eval_mask])
            n_points[eval_mask] += 1

    n_points[n_points == 0] = 1
    return sums/n_points


def jackknife_variance(func,data,N=None,args=()):
    estimate = func(data,*args)
    
    if N is None:
        N = data.size
        omit_points = np.arange(N)
    else:
        omit_points = np.randint(0,data.size,N)
    
    other_estimates = np.empty(N)    
    
    for i in range(N):
        other_estimates[i] = func(np.delete(data,i),*args)
        
    return (data.size-1)/N * np.sum((estimate-other_estimates)**2)

'''
under construction
'''
def median_filter(x,y,width=1):
    lbound = np.zeros(y.size)
    ubound = np.zeros(x.size)
    cen = np.zeros(x.size)
    
    for i in range(y.size):
        lo = max(i-width,0)
        hi = min(i+width,y.size)
        tsec = x[lo:hi]
        fsec = y[lo:hi]
        
        fitmid = np.polyval(np.polyfit(tsec, fsec, 2), tsec)
        normid = np.median(fsec)
        mad = min(np.median(abs(fsec-fitmid)), np.median(abs(fsec-normid)))
        cen[i] = normid
        sigma = 1.4826*mad
        ubound[i] = normid+3*sigma
        lbound[i] = normid-3*sigma
    

    from matplotlib import pyplot as plt
    plt.plot(x,lbound,'g-')
    plt.plot(x,ubound,'g-')
    plt.plot(x,cen,'b-')
    #plt.plot(x,y,'k.')
    plt.ylim(y.min(),y.max())
    plt.show()
    exit()
    

    mask = ((y < ubound) & (y > lbound))
    
    return x[mask],y[mask]

'''
Median filter test code
'''

if __name__ == '__main__':
    import os
    from astropy.io import fits
    os.chdir('/home/ben/research/kepler_llc/007500161')
    files = [f for f in os.listdir('.') if f.endswith('_llc.fits')]

    contents = fits.open(files[0])[1].data
    x = contents['TIME']
    y = contents['PDCSAP_FLUX']
    mask = np.invert(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]


    median_filter(x,y,11)


