import kde
import _kde
import numpy as np
from time import time
import matplotlib.pyplot as plt

data = np.random.rand(1e5)
#data = [.5]

npoints = 101
bandwidth = 0.1
xmin = 0
xmax = 1
t0 = time()
(xgrid, den) = kde.hat_linear(data, bandwidth = bandwidth, xmin=xmin, xmax=xmax, npoints = npoints)
t1 = time()

print "Elapsed time {}".format(t1-t0)

t0 = time()
den2 = _kde.hat_linear(data, 0.1, xmin, xmax, npoints)
t1 = time()
print "Elapsed time {}".format(t1-t0)

print "Error {}".format( np.max(den-den2))

print den
print den2


fig, ax = plt.subplots()
ax.plot(xgrid,den)
ax.plot(xgrid,den2)

plt.show()
