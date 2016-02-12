import os
import setuptools


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name="astrotools",
    version="0.0.1",
    maintainer="Benjamin Kimock",
    maintainer_email="kimockb@gmail.com",
    description=("Supplemental Astronomy Tools for Python"),
    license="MIT",
    long_description=read('README.rst'),
    package_data={'': ['README.rst', 'LICENSE.rts']},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7, Python :: 3.4",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    url="https://github.com/saethlin/astrotools",
    platforms=['any'],
    packages=['astrotools'],
        requires=["numpy", "scipy", "PIL"]
)

