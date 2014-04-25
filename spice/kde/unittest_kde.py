#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import kde
import _kde
import unittest
import numpy as np
from time import time

class TestCKDE(unittest.TestCase):
    def setUp(self):
        self.data = np.random.rand(1e4)
        self.xmin = 0
        self.xmax = 1
        self.npoints = 101
        self.bandwidth = 0.1

    def test_hat_linear(self):
        t0 = time()
        den = kde.hat_linear(self.data, bandwidth = self.bandwidth, 
                        xmin = self.xmin, xmax = self.xmax,
                        npoints = self.npoints, code = 'python')
        t1 = time()
        
        t2 = time()
        den2 = _kde.hat_linear(self.data, self.bandwidth, self.xmin, self.xmax,
                            self.npoints)
        t3 = time()

        t4 = time()
        den = kde.hat_linear(self.data, bandwidth = self.bandwidth, 
                        xmin = self.xmin, xmax = self.xmax,
                        npoints = self.npoints, code = 'C')
        t5 = time()
        

        print "Pure python      {:3.3g} seconds".format(t1-t0)
        print "C implementation {:3.3g} seconds".format(t3-t2)
        print "Speedup          {:3.0f} x".format((t1-t0)/(t3-t2))
        print "C from python    {:3.3g} seconds".format(t5-t4)
        self.assertTrue(np.linalg.norm(den - den2,np.inf)<1e-13)


if __name__ == '__main__':
    unittest.main()
