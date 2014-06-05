#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# (c) Jeffrey M. Hokanson 
# Started 29 May 2014
"""
imd.py

A library for accessing IMD files produced by the CyTOF.
For more information about the CyTOF, see:

http://www.dvssciences.com/


The format is undocumented, but seems to be as follows:

1) An xml style text block at the end of the file.  This text block is embedded
   in 16bit ints, so between every character, there is \x00 int.  Hence, 
   every other character is selected to form the text block.
   
   The start of this text block is beginning of the xml-style file:
   "<ExperimentSchema" 

"""

#import xml.etree.ElementTree as ET
# Switching to lxml for better namespace support
from lxml import etree
import numpy as np
import struct
from functools32 import lru_cache
import scipy.sparse as sp

from clint.textui import progress

# This follows the example on Stack Overflow
# http://stackoverflow.com/questions/2745329/how-to-make-scipy-interpolate-give-an-extrapolated-result-beyond-the-input-range
from scipy.interpolate import interp1d
from scipy import array


# 
from scipy.lib.six import iteritems

def dok_gt(self, other):
    """
    Element-wise greater than
    """
    # First, store all the non-trivial elements
    ret = sp.dok_matrix(self, dtype = bool, copy = True)
    for (key, val) in iteritems(self):
        ret[key] = val > other
    
    # TODO: dok_matrix by default returns 0.0 for unknown keys
    # this should be replaced by either False for bool arrays 
    # OR, better, a default setting, either True or False
    return ret

def dok_lt(self, other):
    """
    Element-wise greater than
    """
    # First, store all the non-trivial elements
    ret = sp.dok_matrix(self, dtype = bool, copy = True)
    for (key, val) in iteritems(self):
        ret[key] = val < other
    
    # TODO: dok_matrix by default returns 0.0 for unknown keys
    # this should be replaced by either False for bool arrays 
    # OR, better, a default setting, either True or False
    return ret

#sp.dok_matrix.__gt__ = dok_gt 
#sp.dok_matrix.__lt__ = dok_lt


def extrap1d(interpolator):
    """
    Takes an interpolation routine and extends via linear extrapolation to
    points outside of the range.
    """
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:
            return ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
        elif x > xs[-1]:
            return ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return array(map(pointwise, array(xs)))

    return ufunclike

# From https://gist.github.com/endolith/114336

def gcd(*numbers):
    """Return the greatest common divisor of the given integers"""
    from fractions import gcd
    return reduce(gcd, numbers)

def lcm(*numbers):
    """Return lowest common multiple."""    
    def lcm(a, b):
        return (a * b) // gcd(a, b)
    return reduce(lcm, numbers, 1)



class read():
    """
    An interface for reading IMD files.

    This class keeps the data on disk unless called for by accessing using [] syntax;
    e.g.,
        x = imd.read('test.imd')
        x[0:50]
    will return the 50 rows of the datafile.
    Other properties are also accessible.
    """
 
    readible_xsd = 'http://www.dvssciences.com/xsd/Cytof/Experiment_1_0.xsd'
    dual_start_count = 1
    round_dual = True

    def __init__(self, filename):

        self.filename = filename
        self.xml_str = self.read_xml()
        root = self.root = etree.fromstring(self.xml_str)

        if not root.nsmap[None] in self.readible_xsd:
            raise ValueError('Cannot read the schema: {}'.format(root.nsmap[None]))
        
        # Save the value of the namespace in which we are working        
        ns = self.ns = "{" + root.nsmap[None] + "}"

        # Count number of columns
        ncol = self.ncol
        self.nrows = self.end_of_data/4/self.ncol
      
        # Open the file containing the data
        self.f = open(filename, 'rb') 

        # We make a tiny class so that we can access the pulse data using
        # self.pulse[5:10]
        class PulseArray():
            """ 
            Return the high precision, low dynamic range measurement
            """
            def __getitem__(s, index):
                return self._pulse(index)
        self.pulse = PulseArray()

        # Same for intensity
        class IntensityArray():
            """
            Return the low precision, high dynamic range measurement
            """
            def __getitem(s, index):
                return self._intensity(index)
        self.intensity = IntensityArray()


        class BothIterate():
            """
            Iterate over rows of both the pulse and intensity matrices.
            """
            # TODO: provide multiple rows of a desired width around target row

            def __init__(s, nrows = 1, read_blocksize = 1000):
                """
                nrows = how many rows to return at a time
                read_blocksize = number of rows to load at a time
                """
                s.start_block = 0
                s.row = 0           # row inside the block we are looking at
                s.read_blocksize = max(read_blocksize, nrows)
                s.data = self
                s.nrows = nrows
                s.read_blocksize = lcm(nrows, read_blocksize)

            def __iter__(s):
                return s

            def next(s):
                if s.row == s.read_blocksize:
                    s.row = 0
                    s.start_block += s.read_blocksize
                # load next block
                if s.row == 0:
                    (s.block_intensity, s.block_pulse) = s.data._read_binary(slice(s.start_block,s.start_block+s.read_blocksize,1))
                s.row += s.nrows
                if s.row + s.start_block > self.nrows:
                    raise StopIteration
                
                return (s.block_intensity[s.row-s.nrows:s.row,:], s.block_pulse[s.row-s.nrows:s.row,:])


            def __len__(s):
                return self.nrows/s.nrows

        self.both_iter = BothIterate


    def __del__(self):
        # Close open file
        self.f.close()
    
    def read_xml(self):
        """
        Find and return the string containing the xml segment of the imd file.
        """
        filename = self.filename
        f = open(filename,'rb')

        step = 1024
        xml_str = ''
        end_of_data = 0
        # While we don't have the header in the string we've read
        while xml_str.find('<ExperimentSchema') == -1:
            end_of_data += step
            # the 2 denotes: read relative to tail of file
            f.seek(-end_of_data,2) 
            r = f.read(end_of_data)
            # Strip the \x00 between characters (16 bit encoding) 
            # and convert the remaining to a string.
            xml_str = str(r[0::2])

        # Strip leading non-string parts
        start = xml_str.index('<ExperimentSchema')
        xml_str = xml_str[start:]
        # multiply by two to account for halving the length of the string 
        end_of_data -= start*2

        from os import fstat
        end_of_data = fstat(f.fileno()).st_size - end_of_data


        self.end_of_data = end_of_data
        f.close()

        return xml_str


    def _read_binary(self, index):
        """
        Reads data from disk, or from a cached sparse version if avalible;
        returns a (intensity, pulse) channels (ints)
        """
        # Attempt to read from sparse versions in memory
        try: 
            return (self.sparse_intensity[index], self.sparse_pulse[index])
        except AttributeError:
            # If this fails, perform the rest of the code
            pass

        if isinstance(index, slice):
            start = index.start
            stop = index.stop
            step = index.step

        elif isinstance(index, int):
            start = index
            stop = index+1
            step = 1
        else:
            raise ValueError("Not a recognized index type") 
        # Usigned int (uint16) (two bytes = 16 bits) 
        stride = 2 
        # how many rows
        nrows = self.end_of_data/stride/2/self.ncol
        # range check, not allowing beyond the end of file

        if stop > nrows and isinstance(index, int):
            raise ValueError("Index out of range")

        # TODO: Handle negative indices
        if start > stop:
            raise NotImplementedError()

        if stop > nrows and start > nrows:
            return ([], [])

        start = min(nrows, start)
        stop = min(nrows, stop)
 
        # Now load in the data
        f = self.f  
        #print "Length of stride {}".format(stride
        f.seek(start*stride*self.ncol*2)

        d = f.read((stop-start)*stride*self.ncol*2)
        array = np.fromstring(d, dtype = np.uint16, count = stride*(stop-start)*self.ncol)
        intensity = array[0::2].reshape([(stop-start), self.ncol])
        pulse = array[1::2].reshape([(stop-start), self.ncol])
        return (intensity, pulse)

    def _intensity(self, index):
        (intensity, pulse) = self._read_binary(index)
        return intensity

    def _pulse(self, index):
        (intensity, pulse) = self._read_binary(index)
        return pulse

    def __getitem__(self, index):
        """
        Return the dual compensated measurements
        """
        (intensity, pulse) = self._read_binary(index)
        slope = self.slopes
        dual_start_count = self.dual_start_count
        # From advice from Rachel Finck who reverse engineered the DVS algorithm:
        # IF slope*intensity>=pulse OR pulse>dual_start_count
        # dual=slope*intensity
        # ELSE
        # dual=pulse
        # The default dual_start_count is 1 on our software; on older software it was 3. 

        # Python apparently automatically broadcasts vector/ matrix multiplication as entrywise
        slope_intensity = np.multiply(slope,intensity)

        # Evaluate the logic entry wise
        case = (slope_intensity > pulse) | (pulse > dual_start_count)
        
        # Apply the formula; unary minus flips True/False
        dual = (slope_intensity*case) + (-case)*pulse 

        if self.round_dual:
            dual = dual.astype(np.int32)    

        return dual 
   
    @property
    @lru_cache(None)
    def ncol(self):
        ncol = 0
        for child in self.root.iter(self.ns +'AcquisitionMarkers'):
            ncol += 1
        return ncol


    @property
    @lru_cache(None)
    def tags(self): 
        """
            List of tags (e.g., CD45, TIM-3)
        """        
        tags = [None] * self.ncol 
        for child in self.root.iter(self.ns + 'AcquisitionMarkers'):
            # Find properties of the particular marker we are looking at 
            short_name = child.findtext(self.ns + 'ShortName')
            mass = child.findtext(self.ns + 'Mass')
            mass_symbol = child.findtext(self.ns + 'MassSymbol')        
            
            # Find corresponding order
            for marker in self.root.iter(self.ns + 'AcquisitionAnalytes'):
                if marker.findtext(self.ns + 'Mass') == mass and marker.findtext(self.ns + 'Symbol') == mass_symbol:
                    order = int(marker.findtext(self.ns + 'OrderNumber'))
                    break

            # Their ordering is one indexed
            tags[order - 1] = short_name
        return tags
    
    @property
    @lru_cache(None)
    def _analytes(self): 
        """
        Extract information about the heavy metal tags

        """        
        symbols = [None] * self.ncol 
        mass = [None] * self.ncol 
        # Find corresponding order
        for marker in self.root.iter(self.ns + 'AcquisitionAnalytes'):
            order = int(marker.findtext(self.ns + 'OrderNumber'))
            mass[order - 1] = float(marker.findtext(self.ns + "Mass"))
            symbols[order - 1] = marker.findtext(self.ns + "Symbol")
        
        return (symbols, mass) 
 
    @property
    @lru_cache(None)
    def markers(self): 
        """
            List of markers (e.g., Ir191)
        """
        makers = [None] * self.ncol   
        symbols, mass = self._analytes

        def name(symbol, m):
            return symbol + str(int(round(m)))

        markers = map(name, symbols, mass)

        return markers
    
    @property
    @lru_cache(None)
    def symbols(self):
        """
        Atomic symbols: e.g., Ir, Gd  
        """    
        symbols, mass = self._analytes
        return symbols


    @property
    @lru_cache(None)
    def masses(self):
        """
        Return the atomic masses of the heavy metal tags used
        """
        symbols, mass = self._analytes
        return mass


    @property
    @lru_cache(None)
    def _acquistion_markers(self):
        """
        Extract data from the AcquisitionMarkers tag
        """
        names = [None] * self.ncol
        descriptions = [None] * self.ncol


        for child in self.root.iter(self.ns + 'AcquisitionMarkers'):
            mass = float(child.findtext(self.ns + "Mass"))
            symbol = child.findtext(self.ns + "MassSymbol")
            # determine which entry this corresponds with in the list of masses
            index = self.masses.index(mass)
            if not symbol == self.symbols[index]:
                raise ValueError("Element information does not match")
            
            names[index] = child.findtext(self.ns + "ShortName")
            descriptions[index] = child.findtext(self.ns + "Description")
        
        return (names, descriptions)

    @property
    @lru_cache(None)
    def tags(self):
        """
        List of tags (e.g., CD10)
        """
        names, descriptions = self._acquistion_markers
        return names

    @property
    @lru_cache(None)
    def descriptions(self):
        """
        List of descriptions (e.g., CD10).  These generally are copies of
        the ShortName field in the xml file.
        """
        names, descriptions = self._acquistion_markers
        return descriptions

    @property
    @lru_cache(None)
    def slope_parameters(self):
        """ 
            Return the vector (mass, intercept, slope)
        """
        mass = []
        intercept = []
        slope = []
        for child in self.root.iter(self.ns + 'DualAnalytesSnapshot'):
            mass.append(float(child.findtext(self.ns + "Mass")))
            intercept.append(float(child.findtext(self.ns + "DualIntercept")))
            slope.append(float(child.findtext(self.ns + "DualSlope")))
        mass = np.array(mass)
        intercept = np.array(intercept)
        slope = np.array(slope)
        return (mass, intercept, slope)


    @property
    @lru_cache(None)
    def slopes(self):
        """
        Return a vector of slopes used for converting readings to Dual Counts.
        """
        # TODO: Improve the interpolation/extrapolation approach.  Currently 
        # use linear interpolation, but should we other varieties instead?
        mass, intercept, slope = self.slope_parameters   
        fi = interp1d(mass, slope)
        # Extrapolate to masses outside the desired range
        fx = extrap1d(fi)
        return fx(self.masses) 


    def plot_slope(self):
        """
        Show the interpolation curve and the measured points in MatPlotLib
        """
        import matplotlib.pyplot as plt
        
        mass, intercept, slope = self.slope_parameters
        plt.plot(mass, slope, 'ro')
        plt.plot(self.masses, self.slopes, 'b.')
        plt.xlabel('Mass')
        plt.ylabel('Slope')
        plt.title('Dual Slope Values')
        plt.show()
    

    def sparse(self, step = 100): 
        """
        Store sparse versions of the desired matrix
        """
        start = 0
        sparse_pulse = sp.dok_matrix( (self.nrows, self.ncol), dtype = np.int16)
        sparse_intensity = sp.dok_matrix( (self.nrows, self.ncol), dtype = np.int16)

        x = 0
        start = 0
        for (row_intensity, row_pulse) in progress.bar(self.both_iter(step)):
            i = row_intensity.nonzero()
            sparse_intensity[i[0]+start,i[1]] = row_intensity[i]

            i = row_pulse.nonzero()
            sparse_pulse[i[0]+start,i[1]] = row_pulse[i]
           
            start += step
            if start > 10000:
                break 
   
        return (sparse_intensity, sparse_pulse) 

    def cache(self):
        """
        Load a sparse representation of the data into memory, enabling
        faster queries
        """
        (self.sparse_intensity, self.sparse_pulse) = self.sparse()

def main():
    """
    Private testing code
    """

    data = read('test.imd')
   
    #print xml_str 
    #print data.tags
    #print data.markers
    print data.masses
    print data.markers
    print data.tags
    print data.descriptions
    (mass, intercept, slope) = data.slope_parameters
    
    np.set_printoptions(threshold = np.nan, linewidth = 150)

    #print data.end_of_data/data.ncol/2/2
    #start = data.end_of_data/data.ncol/4 - 100 
    #print data[start:start+10]
    #print data[start:start+100]
    if True:
        (intensity, pulse) = data.sparse()
        print intensity.getnnz()
        print intensity[0:1000]

        x = intensity > 1
        print x[0,0]
        print x

    print data[0:1000]

    if True:
        data.cache()
        print data[0:1000]
    #data.plot_slope()
 
if __name__ == "__main__":
    main()
