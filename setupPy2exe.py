import sys
import os
import glob
import re
from distutils.core import setup 
import py2exe
from b3.pkg_handler import PkgResourcesStandIn

if len(sys.argv)==1:
    sys.argv.append('py2exe')

def listdirectory(path):
    def istocopy(path):
        return (
                os.path.isfile(path)
                and not path.endswith('.pyc') 
                and not path.endswith('.pyo') 
                )
    return map(os.path.normpath, filter(istocopy, glob.glob(path + os.sep + '*')))

def getVersion():
    pkg_handler = PkgResourcesStandIn()
    reStrictVersion = re.compile('^\s*(?P<version>[0-9.]+).*$')
    m = reStrictVersion.match(pkg_handler.version("b3"))
    if m:
        return m.group('version')
    else:
        return None
    
myDataFiles = [
        ('', ['README']),
        ('', ['b3/PKG-INFO']),
        ('docs', listdirectory('b3/docs/')),
        ('conf', listdirectory('b3/conf/')),
        ('extplugins', ['b3/extplugins/xlrstats.py']),
        ('extplugins/conf', listdirectory('b3/extplugins/conf/')),
    ]
    
    
setup(
    name = "BigBrotherBot",
    version = getVersion(),
    url = "http://www.bigbrotherbot.com/",
    console = ["b3_run.py"],
    zipfile = None, 
    data_files = myDataFiles,
    options = {
        "py2exe": {
            "dist_dir": "../dist_py2exe",
            "bundle_files": 1,
            "optimize": 1,
            "includes": [
                "b3.lib.*",
                "b3.plugins.*",
                "b3.parsers.*",
                "b3.parsers.bfbc2.*",
                "b3.extplugins.__init__",
            ],
        }
    },
) 