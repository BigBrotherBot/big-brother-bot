#!/usr/bin/env python
"""
For all *.py files within the current directory
search for __version__
compute a md5 sum from file names and versions to 
make it easy to compare two branches/repositories
"""

import os
import re
import hashlib


fileList = []
rootdir = '.'
for root, subFolders, files in os.walk(rootdir):
    for file in files:
        if file.endswith('.py'):
            fileList.append(os.path.join(root,file))
fileList.sort()        
        
reVersion = re.compile(r'^\s*__version__\s*=\s*[\'"](?P<version>.+)[\'"].*$', re.MULTILINE)


resultsLines = []
for pythonfile in fileList:
    try:
        str = pythonfile + '\t'
        f = open(pythonfile)
        filecontent = f.read()
        
        m = reVersion.search(filecontent)
        if m:
            str += m.group('version')
        resultsLines.append(str)
    finally:
        f.close()
        
md5sum = hashlib.md5()
for line in resultsLines:
    md5sum.update(line)
print "project signature: %s" % md5sum.hexdigest()
 
for line in resultsLines:
    print line
        