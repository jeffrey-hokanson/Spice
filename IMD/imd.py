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


def read_xml(filename):
    """
    Find and return the string containing the xml segment of the imd file.
    """
    try:
        f = open(filename,'rb')
    except:
        IOError('No such file or directory: {}'.format(filename))

    step_start = 1024
    start = 0
    xml_str = ''
    # While we don't have the header in the string we've read
    while xml_str.find('<ExperimentSchema') == -1:
        start += step_start
        # the 2 denotes: read relative to tail of file
        f.seek(-start,2) 
        r = f.read(start)
        # Strip the \x00 between characters (16 bit encoding) 
        # and convert the remaining to a string.
        xml_str = str(r[0::2])

    # Strip leading non-string parts
    start = xml_str.index('<ExperimentSchema')
    xml_str = xml_str[start:]  

    f.close()
    return xml_str



class Read():
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
    def __init__(self, filename):

        self.filename = filename
        self.xml_str = read_xml(filename)
        root = self.root = etree.fromstring(self.xml_str)

        if not root.nsmap[None] in self.readible_xsd:
            raise ValueError('Cannot read the schema: {}'.format(root.nsmap[None]))
        
        ns = self.ns = "{" + root.nsmap[None] + "}"
        print ns
        # Count number of columns
        ncol = 0
        for child in root.iter(ns +'AcquisitionMarkers'):
            ncol += 1

        self.ncol = ncol
        print "There are {} tags in use".format(ncol)
       


        # We make a tiny class so that we can access the pulse data using
        # self.pulse[5:10]
        class PulseArray():
            def __getitem__(s, index):
                return self._pulse(index)
        self.pulse = PulseArray()

        # Same for intensity
        class IntensityArray():
            def __getitem(s, index):
                return self._intensity(index)
        self.intensity = IntensityArray()


    def _read_binary(self, index):
        if isinstance(index, slice):
            print "slice"
            start = index.start
            stop = index.stop
            step = index.step
            print index.start
            print index.stop
            print index.step

        elif isinstance(index, int):
            print "int"
            start = index
            stop = index+1
            step = 1
        else:
            ValueError("Not a recognized type") 
        
        # Now load in the data
        f = open(self.filename,'rb')
    
        # Usigned int (uint16) (two bytes = 16 bits) 
        stride = 2 
        #print "Length of stride {}".format(stride)
        f.seek(start*stride*self.ncol)
        d = f.read((stop-start)*stride*self.ncol*2)
        array = np.fromstring(d, dtype = np.uint16, count = 2*(stop-start)*self.ncol)
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
        Currently an alias for the intensity channel
        Should eventually return dual compenstated value
        """
        return self._intensity(index) 

def main():
    xml_str = read_xml('test.imd')
    data = Read('test.imd')

    d = data[500:10000]
    np.set_printoptions(edgeitems = 4000, linewidth = 150)
    #print data.pulse[500:1000]
    
    print data.xml_str

if __name__ == "__main__":
    main()
