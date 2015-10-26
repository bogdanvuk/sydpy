from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [Extension("xsimintf_test", ["xsimintf_test.pyx"],
                        include_dirs = ["/home/bvukobratovic/projects/sydpy/intf/xsim/src",
                                        "/home/bvukobratovic/projects/sydpy/intf/xsim/test"])]

setup(
  name = 'xsimintf_test',
    ext_modules = cythonize(extensions),
)
