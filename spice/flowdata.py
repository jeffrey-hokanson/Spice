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

        For later compatability with Pandas (but we've avoided due to speed penalties),
        we've added the following functions
            .get
            [ ] - returns slice of matrix based on rows

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

    @nevents.setter
    def nevents(self, n):
        self._metadata['$TOT'] = n

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

            If we provide a boolian vector of length nevents, we generate a new 
            FlowData object, with the selected rows
        """
        # TODO: most tags/markers are not valid property names, use regular expressions
        # to allow these to be called in a normalized fashion
        # i.e., this should do some name mangling
        if name in self.tags:
            return self._data[self.tags.index(name)]
        if name in self.markers:
            return self._data[self.markers.index(name)]
    
        raise AttributeError("Attribute {} not defined".format(name))

    def __getitem__(self, index): 
        # In this case, we return a FlowData object with the selected rows
        if index.__class__ is np.ndarray:
            if len(index) == self.nevents:
                fd = FlowData()
                fd._data = self._data[:,index]
                if self._analysis.__class__ is np.ndarray:
                    fd._analysis = self._analysis[:,index]
                fd._metadata = self._metadata
                fd.nevents = fd._data.shape[1]
                fd._meta_analysis = self._meta_analysis
                return fd
            else:
                raise AttributeError("Dimension Mismatch")
        else:
            raise AttributeError("Only accepts numpy.ndarrays") 

    
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
        t = self._make_gate(len(self._fd)-1)
        t.title = self._fd[-1].filename
    
    def append(self, item):
        self._fd.append(item)
        t = self._make_gate(len(self._fd)-1)
        t.title = 'Appended item {}'.format(len(self._fd)-1)
        return t
    def _make_gate(self, index):
        """
            Add a new gate to the corresponding index
        """
        t = GateTree()
        t.active = True
        t.color = [0, 0, 0]
        t.gates.append(GateIndex(index))
        self.gate_tree.addChild(t)
        return t
           
 
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
        self.gates = []
        self.title = ''

    def gate(self, flow_data):
        """ Apply gates to the provided data sets.

        """
        # We need to start from the top and work downwards towards the current gate

        for gt in self.pathFromRoot():
            for gate in gt.gates:
                flow_data = gate.apply(flow_data)
        return flow_data

    def __str__(self):
        root = self.getRoot()
        if not root == self:
            s = root.__str__()
            print self.getRoot()
            return s
        else:
            def walk(t, depth) :
                s =  "---"*depth + t.title + '\n'
                for g in t.gates:
                    s += "   "*depth + '|->Gate: ' + g.__str__() + '\n'
                for c in t.children:
                    s += walk(c, depth+1) 
                return s  
            return walk(self, 0)


class GateVirtual:
    def apply(self):
        raise NotImplementedError

    def __str__(self):
        return ' '

class GateIndex(GateVirtual):
    """
        A gate based on index of FlowData sets loaded into 
        a vector of FlowDatas
    """
    def __init__(self, index):
        self.index = index
    
    def apply(self, flow_data):
        return flow_data[self.index] 

    def __str__(self):
        return 'Index = {}'.format(self.index)


class GateBound(GateVirtual):
    def __init__(self, channel, inequality, bound):
        self.channel = channel
        if not inequality in ['=', '<=', '>=', '<', '>']:
            raise ValueError('inequality provided must be one of <, >, <=, >=, =; you gave {}'.format(inequality))
        self.inequality = inequality
        self.bound = bound

    def apply(self, flow_data):
        if flow_data.__class__ == [].__class__:
            # If we have a list of flow data, call on each element of list
            # append to the returned list
            flow_data_new = []
            for fd in flow_data:
                flow_data_new.append(self.apply(fd))
            return flow_data_new
        else:
            selected_data = flow_data.get(self.channel)
            index = {
                '=':  lambda x: x == self.bound,
                '<':  lambda x: x < self.bound,
                '>':  lambda x: x > self.bound,
                '<=': lambda x: x <= self.bound,
                '>=': lambda x: x >= self.bound
            }[self.inequality](selected_data)

            return flow_data[index]

    def __str__(self):
        return self.channel + ' ' + self.inequality + ' ' + '{}'.format(self.bound)

            
