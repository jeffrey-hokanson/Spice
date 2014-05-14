# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# A package containing a data structure for a single flow cytometry experiment

import os
import numpy as np
#import pandas as pd
from functools32 import lru_cache
import fcs
from kde import kde

from tinytree import Tree

class FlowData:
    """ A container class for flow cytometry data.
        
        Our primary design decision is to keep most of the parameters inside 
        the metadata structure, which we expose to the user via alternatively
        named commands (we seek to avoid the FCS standard of 
    """
    _kernel_1D_list = ["hat"]

    def __init__(self, path = None):

        if not path is None:
            (self._data, self._metadata, self._analysis, self._meta_analysis) = \
                fcs.read(path, True)
            self._path = path
            self._filename = os.path.basename(path)
        else:
            self._data = []
            self._metadata = {}
            self._analysis = []
            self._meta_analysis = {}

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
    @property
    def path(self):
        return self._path
    @property
    def filename(self):
        return self._filename

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
        self._tags = []
        for j in range(self.nparameters):
            self._tags.append(self._metadata['$P{}N'.format(j+1)])
        return self._tags

    @property
    def markers(self):
        """ Name of the corresponding marker to each of the tags; e.g., CD45.
            This corresponds to the $PnS section of the FCS file.
        """
        self._markers = []
        for j in range(self.nparameters):
            # add markers
            self._markers.append(self._metadata.get('$P{}S'.format(j+1), ''))
        return self._markers

    @property
    def kernel_1D_list(self):
        return self._kernel_1D_list

    # TODO: Add memoize decorator to reduce computation time, perhaps also add threading option. 
    @lru_cache(maxsize=1000)
    def kde1(self, channel, bandwidth = 0.5, kernel = 'hat', npoints = 1001):
        """ Generate histogram
        """
        data = self.data[channel]
        xmin = np.min(data)
        xmax = np.max(data)
        
        if kernel == 'hat':
            den = kde.hat_linear(data, bandwidth, xmin, xmax, npoints)
        xgrid = np.linspace(xmin, xmax, npoints)
        return (xgrid, den)

    def __getattr__(self, name):
        """ Provides access to the data channels/markers in their original names
            (inspired by pandas)
            e.g.,
            fd = FlowData('test.fcs')
            fd.CD45
            will return the appropreate channel
        """
        # TODO: most tags/markers are not valid property names, use regular expressions
        # to allow these to be called in a normalized fashion
        # i.e., this should do some name mangling
        if name in self.tags:
            return self._data[self.tags.index(name)]
        if name in self.markers:
            return self._data[self.markers.index(name)]
        
        raise AttributeError("Attribute {} not defined".format(name))
    
    def get(self,name):
        """ Similar to __getattr__, but this formulation can parse pure strings,
            rather than
        """
        if name in self.tags:
            return self._data[self.tags.index(name)]
        if name in self.markers:
            return self._data[self.markers.index(name)]
        raise AttributeError("Attribute {} not defined".format(name))
        

    def normalize(self):
        """ Names comming from our lab are not always right, 
            fix these
        """
        raise NotImplementedError

class FlowAnalysis:
    """ A container class for multiple datasets.
        This largely emulates a list, but we are leaving the option open
        for later complexity



        gate_tree - an instance of tinytree, with the following properties
            added to each node

            active = should plot be displayed
            color = RGB255 color of the plot
            gate = data structure for applying gating/masking of data
            title = title to display with the gate
    """
    def __init__(self):
        self._fd = []   # Container for flow data
        self.gate_tree = GateTree()
        # We never display the root node plot
        self.gate_tree.active = False
        self.gate_tree.color = [0, 0, 0]
        self.gate_tree.title = "All Data"

    def load(self, filename):
        """Load an fcs file into the analysis set. """
        self._fd.append(FlowData(filename))
        t = GateTree()
        t.active = True
        t.color = [0, 0, 0]
        t.title = self._fd[-1].filename
        t.gate_index(len(self._fd) - 1)
        self.gate_tree.addChild(t)
    
    def list_files(self):
        lf = []
        for fd in self._fd:
            lf.append(fd.filename)
        return lf

    def __len__(self):
        return len(self._fd)

    def __getitem__(self, key):
        # TODO: Should we allow access by other than index?
        if key < 0 or key >= self.__len__():
            raise IndexError

        return self._fd[key]

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        return self._fd.__iter__()

    @property
    def nparameters(self):
        """ Count the number of distinct parameters."""
        #TOD Fix this
        return self._fd[0].nparameters


    @property
    def flow_data(self):
        return self._fd


class GateTree(Tree):
    """
        Stores information for selecting nested subsets.  Each subset is 
        choosen by a 'gate', either specifying 
            - A particular data set (FlowData)
            - a subset selection rule based on channels
        These are mutually exclusive, and the main function, gate will
        either return a list of FlowData types, gated, or a single FlowData
        type.

        The two basic use cases are global gates, that apply a gate to every
        FlowData in the list (e.g., filtering dead cells), or applying a 
        particular gate to one set of data. 
    """



    def __init__(self, children = None):
        super(GateTree, self).__init__(children)
        self.index = None
    
    def gate(self, flow_data):
        """
            Traverse the tree, applying appropreate gates at each level.

            Returns a FlowData type structure 
        """
        # check if index is a single integer
        if not self.index is None:
            return flow_data[self.index] 

        
    def gate_index(self, index):
        self.index = index


        
