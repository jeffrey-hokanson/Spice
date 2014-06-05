#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# (c) Jeffrey M. Hokanson 
# Started 4 June 2014

import imd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import sys

data = imd.read('test.imd')

fig = plt.figure(tight_layout = True)

gs = gridspec.GridSpec(data.ncol,1, wspace = 5.0, hspace = 0.0)
ax = []
for j in range(data.ncol):
    ax.append(plt.subplot(gs[j,0]))

fig.subplots_adjust(left = 0.02, right = 0.98, top = 1, bottom = 0.05)

start = 0
step = 1000
def move(event):
    global start, step, ax, fig, data
    print 'key = {}'.format(event.key)
    if event.key in ['ctrl+c', 'ctrl+C']:
         sys.exit(0)
    
    if event.key == 'right':
        start += step
    if event.key == 'left':
        start -= step
        start = max(0, start)
    
    if event.key in ['left', 'right']:
        x = data[start:start+step]
        tot = x.sum(axis = 1)
        time = np.arange(start, start+step)
        for j in range(data.ncol):
            ax[j].cla()
            ax[j].plot(time, x[:,j],'k')
            #ax[j].set_ylim(bottom=0, top=50)
            ax[j].spines['bottom'].set_color('white')
            ax[j].spines['top'].set_color('white')
            ax[j].set_yticklabels([], visible = False)
            ax[j].set_ylabel(data.tags[j])
            if j != data.ncol - 1:
                ax[j].set_xticklabels([], visible = False)
        #plt.tight_layout()
        ax[0].figure.canvas.draw()
    

cid = fig.canvas.mpl_connect('key_press_event', move)
plt.show()

