import sys
import os
import glob
from distutils.core import setup 
import py2exe
from b3.pkg_handler import PkgResourcesStandIn

def listdirectory(path):
    return filter(os.path.isfile, glob.glob(path + os.sep + '*'))

def getVersion():
    pkg_handler = PkgResourcesStandIn()
    return pkg_handler.version("b3")
    
myDataFiles = [
        ('', ['README']),
        ('examples', listdirectory('examples/')),
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
    #zipfile = None, 
    data_files = myDataFiles,
    options = {
        "py2exe": {
            "dist_dir": "dist_py2exe",
            "optimize": 1,
            "includes": [
                "b3.plugins.*",
                "b3.parsers.*",
                "b3.extplugins.__init__",
            ],
        }
    },
) 