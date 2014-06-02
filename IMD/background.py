#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# (c) Jeffrey M. Hokanson 
# Started 2 June 2014

"""
Produces histograms for each channel of heavy metal tags passing through 
without other tags.

Displays one plot at a time  

Usage:
./background.py <IMD file>

Requirements:
imd.py
clint, matplotlib, numpy

"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import imd
from clint.textui import progress


def background(data, push_distance_threshold = 5):
    """
    Scans for single events and combines those within a threshold distance, and removes events
    if a latter event in the same channel inside the threshold occurs with other markers
    """
    single_counts = [ [] for i in range(data.ncol) ]
    pushes_since_last_count = np.zeros(data.ncol, dtype = np.int32)

    blocksize = 1000
    start = 0
    for a in progress.bar(range(data.nrows/blocksize/1)):
        try:
            x = data[start:(start+blocksize)]
        except:
            break
        if len(x) == 0:
            break
        
        # iterate over each row, if no other signal in anyother channel, apltend value
        for row in x:
            i = row.nonzero()[0]
            pushes_since_last_count += 1
            if len(i) == 1:
                # If there is only one tag present
                if pushes_since_last_count[i] < push_distance_threshold:
                    # If we are close enough in time, add to previous push
                    single_counts[i][-1] += float(row[i])
                else:
                    # Otherwise, we have a new count
                    single_counts[i].append(float(row[i]))
                pushes_since_last_count[i] = 0
            elif len(i) > 1:
                # If we have multiple tags present, and we've previously registered new tags, 
                # we delete the preceeding tags.
                # This corresponds to a single tag, split into two, that overlaped with another
                # tag, indicating we may be looking at a cell like event.
                for ii in i:
                    if pushes_since_last_count[ii] < push_distance_threshold:
                        # We don't want to keep popping items off the list constantly
                        pushes_since_last_count[ii] = push_distance_threshold + 1
                        single_counts[ii].pop()
                        

        start += blocksize

    return single_counts


def background_basic(data):
    """
    Simply scans for single events, does not look forwards or backwards in time.
    """
    single_counts = [ [] for i in range(data.ncol) ]
    
    blocksize = 1000
    start = 0
    for a in progress.bar(range(data.nrows/blocksize/1)):
        try:
            x = data[start:(start+blocksize)]
        except:
            break
        if len(x) == 0:
            break
        
        # iterate over each row, if no other signal in anyother channel, apltend value
        for row in x:
            i = row.nonzero()[0]
            if len(i) == 1:
                single_counts[i].append(float(row[i]))
        
        start += blocksize

    return single_counts



 
if __name__ == "__main__":
    filename = sys.argv[1]
    data = imd.read(filename)
    data.round_dual = False
    single_counts = background(data)
    
    bins = range(100)

    for j in range(data.ncol):
        plt.figure()   
        ax = plt.subplot(111) 
        plt.hist(single_counts[j], bins)
        plt.title(data.markers[j] + ' :: ' + data.tags[j])
        ax.set_yscale('symlog', linthreshy = 1)

    plt.show() 
