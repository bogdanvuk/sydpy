from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sydpy',

    version='0.0.1',

    description='System Design in Python',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/bogdanvuk/sydpy',
    download_url = 'https://github.com/bogdanvuk/sydpy/tarball/0.0.1',

    # Author details
    author='Bogdan Vukobratovic',
    author_email='bogdan.vukobratovic@gmail.com',

    # Choose your license
    license='LGPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[

        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',

        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',

        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='System Design Python Simulator HDL ASIC FPGA verification TLM',
    packages=find_packages(exclude=['examples*', 'doc']),

    install_requires=['greenlet'],

)
