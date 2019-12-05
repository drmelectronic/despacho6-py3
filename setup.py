#*********************************************
#        Auto-Generated With py2Nsis
#*********************************************

import warnings 
#ignore the sets DeprecationWarning
warnings.simplefilter('ignore', DeprecationWarning) 
import py2exe
warnings.resetwarnings() 
from distutils.core import setup
		
target = {
'script' : "E:\\Documents and Settings\\Administrador\\Mis documentos\\Despacho6\\Principal.py",
'version' : "6.17",
'company_name' : "ECONAIN S.A.C.",
'copyright' : "",
'name' : "TCONTUR6", 
'dest_base' : "TCONTUR6", 
'icon_resources': [(1, "E:\\Documents and Settings\\Administrador\\Mis documentos\\Despacho6\\images\\icono.ico")]
}		



setup(

	data_files = [],
    
    zipfile = None,

	options = {"py2exe": {"compressed": 0, 
						  "optimize": 0,
						  "includes": ['atk', 'cairo', 'gio', 'gobject', 'pango', 'pangocairo', 'Cython', 'urllib3'],
						  "excludes": ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger', 'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl', 'Tkconstants', 'Tkinter', 'webkit'],
						  'dll_excludes': ['python32.dll',],
						  "packages": ['cefpython1', 'etc', 'reportlab', 'lib', 'urllib3', 'share', 'xlwt'],
						  "bundle_files": 3,
						  "dist_dir": "E:\\Documents and Settings\\Administrador\\Mis documentos\\Despacho6\\dist",
						  "xref": False,
						  "skip_archive": False,
						  "ascii": False,
						  "custom_boot_script": '',                          
						 }
			  },
	console = [],
	windows = [target],
	service = [],
	com_server = [],
	ctypes_com_server = []
)
		
