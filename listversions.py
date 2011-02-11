#!/usr/bin/env python
# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# A tool to create a list of current file versions

"""
For all *.py files within the b3 directory
search for __version__
compute a md5 sum from file names and versions to 
make it easy to compare two branches/repositories
"""

import os
import re
import hashlib


fileList = []
rootdir = 'b3'
for root, subFolders, files in os.walk(rootdir):
    for file in files:
        if file.endswith('.py'):
            fileList.append(os.path.join(root,file))
fileList.sort()        
        
reVersion = re.compile(r'^\s*__version__\s*=\s*[\'"](?P<version>.+)[\'"].*$', re.MULTILINE)


filesAndVersions = []
linesToDisplay = []
md5sum_content = hashlib.md5()
for pythonfile in fileList:
    try:
        str = pythonfile
        f = open(pythonfile)
        filecontent = f.read()
        
        md5sum_content.update(filecontent)
        
        md5sum_tmp = hashlib.md5()
        md5sum_tmp.update(filecontent)
        
        version = None
        m = reVersion.search(filecontent)
        if m:
            version = m.group('version')
        filesAndVersions.append('%s %s' % (pythonfile, version))
        linesToDisplay.append('%s %s %s' % (pythonfile, md5sum_tmp.hexdigest(), version))
    finally:
        f.close()

md5sum_fnames_versions = hashlib.md5()
for line in filesAndVersions:
    md5sum_fnames_versions.update(line.replace('\\','/'))
print "project files/versions signature: %s" % md5sum_fnames_versions.hexdigest()
print "project files content signature: %s" % md5sum_content.hexdigest()
 
for line in linesToDisplay:
    print line

    