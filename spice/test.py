import numpy as np
from flowdata import FlowData
import matplotlib.pyplot as plt

fd = FlowData('test.fcs')

print fd.markers
(xgrid,den) = fd.histogram(5)

print xgrid
print den

fig, ax = plt.subplots()

ax.semilogy(xgrid,den)
plt.show()
