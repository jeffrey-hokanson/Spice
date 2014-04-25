#
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
""" A module for kernel density estimators

 Although there are many existing algorithms, e.g. scikit-learn, 
 (see: http://jakevdp.github.io/blog/2013/12/01/kernel-density-estimation/)
 our objective is exploiting speedups based on the knowledge of which points
 we want to evaluate the density function at.  Namely, that most of the time
 we seek the values on a uniform grid, so we can compute which values need to
 be touched. (This is true when we are plotting.)

 Currently, we implement these as a series of dumb functions, but we may wish to 
 add a class interface at a later date
"""
import _kde
import numpy as np
from math import floor, ceil

def hat_linear(data, bandwidth = 1.0, xmin = None, xmax = None, npoints = 100, code = 'C'):
    """ A Kernel density estimate using a hat (linear) kernel on a linear grid
    Parameters
    ----------
    data : numpy array (one dimensional)
        The data we are building the kernel density estimator from.

    bandwidth : float
        Width of the linear hat function

    xmin : float or None
        Bottom range of grid.  If none, then xmin = np.min(data).

    xmax : float or None
        Top range of grid.  If none, then xmax = np.max(data).

    npoints : positive integer
        Number of grid points inclusive of the end points

    Returns
    -------
    xgrid : numpy array
        Coordinates where the density estimator is evaluated.

    den : numpy array
        Value of the kernel density estimator on xgrid.
    """

    if xmin is None:
        xmin = np.min(data)
    if xmax is None:
        xmax = np.max(data)

    xmax = float(xmax)
    xmin = float(xmin)
    
    if code == 'C':
        try:
            den = _kde.hat_linear(data, bandwidth, xmin, xmax, npoints)
        except:
            # If the C code fails, default to slow python code
            den = hat_linear(data, bandwidth, xmin, xmax, points, code = 'python')
    elif code == 'python':

        h = (xmax - xmin)/(npoints - 1)
        den = np.zeros(npoints)
        for x in data:
            bottom = max(int(ceil((x - bandwidth - xmin)/h)),0)
            top = min(int(floor((x + bandwidth - xmin)/h)), npoints - 1)
            for j in range(bottom, top + 1):
                den[j] += (1 - abs(x - (j*h + xmin))/bandwidth)/bandwidth

        den = den/len(data)
    else:
        raise ValueError('Code type {} not allowed'.format(code))

    return den
