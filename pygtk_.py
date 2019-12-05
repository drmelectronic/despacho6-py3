# An example of embedding CEF browser in PyGTK on Linux.

import ctypes, os, sys
libcef_so = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libcef.so')
if os.path.exists(libcef_so):
    # Import local module
    ctypes.CDLL(libcef_so, ctypes.RTLD_GLOBAL)
    if 0x02070000 <= sys.hexversion < 0x03000000:
        import cefpython_py27 as cefpython
        print 'cefpython27'
    else:
        raise Exception("Unsupported python version: %s" % sys.version)
else:
    # Import from package
    from cefpython1 import cefpython

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import re
