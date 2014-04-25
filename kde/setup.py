from distutils.core import setup, Extension
import numpy.distutils.misc_util

#c_ext = Extension("_kde", ["_kde.c", "hat_linear.c"],libraries=['m','],library_dirs=['/usr/local/lib'])
c_ext = Extension("_kde", ["_kde.c", "hat_linear.c"],libraries = ['m'])

setup(
    ext_modules=[c_ext],
    include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs(),
)
