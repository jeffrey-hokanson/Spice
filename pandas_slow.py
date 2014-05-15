#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from timeit import Timer
from flowdata import FlowData
import pandas as pd
import numpy as np


fd = FlowData('test.fcs')
print fd.tags
print fd.markers

print len(fd.CD45)

print fd.get('TIM-3')

data = fd._data
x = fd.get('TIM-3')
y = fd.get('CD45')

i = y > 10
print len(i)
print data[:,y>10]

numpy_select = Timer("""x = fd.get('TIM-3'); y = fd.get('CD45'); x[y>10]""",setup="""from flowdata import FlowData; fd = FlowData('test.fcs'); """)

it = 1000
print "Time per select (Numpy) {} ms".format(numpy_select.timeit(it)/it*1000)

df = pd.DataFrame({'TIM-3':x, 'CD45':y})
#print df

# Pandas seems unforgivably slow as compared to pure numpy.
#pandas_select = Timer("""pd.eval("df[df['CD45']>10]")""",setup="""
pandas_select = Timer("""pd.eval("df[df['CD45']>10]")""",setup="""
import pandas as pd
from flowdata import FlowData
fd = FlowData('test.fcs')
x = fd.get('TIM-3')
y = fd.get('CD45')
df = pd.DataFrame({'TIM-3':x,'CD45':y})""")
print "Time per select (Pandas) {} ms".format(pandas_select.timeit(it)/it*1000)
