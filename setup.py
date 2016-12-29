from setuptools import setup, Extension
import numpy

ctools = Extension('ctools',
                   sources=['python_interface.cpp'],
                   extra_compile_args=['-std=c++11', '-Ofast'])

setup(name='ctools',
      version='0.0.1',
      description='A starspot modeling program',
      ext_modules=[ctools],
      include_dirs=[numpy.get_include()])
