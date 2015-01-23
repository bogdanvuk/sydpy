from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sydpy',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/development.html#single-sourcing-the-version
    version='0.1.0a1',

    description='System Design in Python',
    long_description=long_description,

    # The project's main homepage.
    url='http://sydpy.readthedocs.org/en/latest/',

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

    keywords='HDL ASIC FPGA verification TLM',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=['greenlet'],

)