#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# A package containing a data structure for a single flow cytometry experiment

import numpy as np

import fcs

from kde import kde

class FlowData:
    """ A container class for flow cytometry data.
        
        Our primary design decision is to keep most of the parameters inside 
        the metadata structure, which we expose to the user via alternatively
        named commands (we seek to avoid the FCS standard of 
    """
    def __init__(self, path = None):
        (self._data, self._metadata, self._analysis, self._meta_analysis) = \
            fcs.read(path, True)

    # Raw accessors for critical
    @property
    def data(self):
        """ A numpy matrix where each row is an event (i.e., a cell) and each
            column is a channel (i.e., a detector)
        """
        return self._data
    @property
    def metadata(self):
        return self._metadata
    @property
    def analysis(self):
        return self._analysis
    @property
    def meta_analysis(self):
        return self._meta_analysis

    # Virtual accessors for properties stored in the metadata
    # We do this rather than copy values out into temporary variables
    @property
    def nparameters(self):
        """ Number of measuremen0t/property channels"""
        return self._metadata['$PAR']
    @property
    def nevents(self):
        """ Number of events/cells"""
        return self._metadata['$TOT']


    @property
    def tags(self):
        """ Names of the tag used (e.g., Xe131 for CyTOF; APC or Cy5 for
            flurorescent flow).  This corresponds to the $PnN channel in the
            corresponding FCS file.
        """
        # Cache these values in the vector tags
        try:
            return self._tags
        except AttributeError:
            self._tags = []
            for j in range(self.nparameters):
                self._tags.append(self._metadata['$P{}N'.format(j+1)])
            return self._tags

    @property
    def markers(self):
        """ Name of the corresponding marker to each of the tags; e.g., CD45.
            This corresponds to the $PnS section of the FCS file.
        """
        try:
            return self._markers
        except AttributeError:
            self._markers = []
            for j in range(self.nparameters):
                # add markers
                self._markers.append(self._metadata.get('$P{}S'.format(j+1), ''))
            return self._markers

    
    def histogram(self, channel):
        """ Generate histogram
        """
        npoints = 10001
        
        data = self.data[channel]
        xmin = np.min(data)
        xmax = np.max(data)
        bandwidth = 0.5
        den = kde.hat_linear(data, bandwidth, xmin, xmax, npoints)
        xgrid = np.linspace(xmin, xmax, npoints)
        return (xgrid, den)