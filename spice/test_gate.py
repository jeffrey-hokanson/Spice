#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from timeit import Timer
from flowdata import *
import pandas as pd
import numpy as np


fd = FlowData('test.fcs')

fa = FlowAnalysis()
chan1 = fa.append(fd)

print fa.gate_tree

t = GateTree()
t.gates.append(GateBound('CD45','>',10))
t.title = 'CD45+'

chan1.addChild(t)

print fa.gate_tree

fd_new = t.gate([fd])

print fd._data.shape[1]
print fd.nevents
print fd_new._data.shape[1]
print fd_new.nevents
