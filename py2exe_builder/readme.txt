This folder holds the tools and scripts to build a .exe release of B3
and an installer.
This script will take the B3 version found in the b3.egg-info folder, so you need to have run the
setup.py tool before.

REQUIREMENTS:
    Environment :
        * a Windows OS
        * with python2.6+
        * with pymysql
    Tools:
        * py2exe2.6+
        * InnoSetup
        * InnoSetup preprocessor
        * ISTools (optional)
    
HOW TO BUILD THE .EXE RELEASE and distributions :
    * check the build.yaml config file
    * run python.exe build.py


----

# Quick walk-through to set up a Windows machine able to build the .exe B3 package

# install git
https://github.com/msysgit/msysgit/releases/download/Git-1.9.4-preview20140929/Git-1.9.4-preview20140929.exe

# open a PowerShell console and execute:
iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
choco install firefox jre8 DotNet3.5 console2

# install python 2.7 32bit and python modules
https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi
http://www.lfd.uci.edu/~gohlke/pythonlibs/wyxyx8e9/MySQL-python-1.2.5.win32-py2.7.exe
http://www.lfd.uci.edu/~gohlke/pythonlibs/wyxyx8e9/pysqlite-2.6.3.win32-py2.7.exe
http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe
http://freefr.dl.sourceforge.net/project/py2exe/py2exe/0.6.9/py2exe-0.6.9.win32-py2.7.exe

# add C:\Python27\;C:\Python27\Scripts\ to the PATH environment variable

# in a "Git Bash" console, run:
curl https://bootstrap.pypa.io/get-pip.py | python

# install more python modules with pip
pip install virtualenv

# install InnoSetup and InnoSetup PreProcessor
http://www.jrsoftware.org/download.php/ispack-unicode.exe?site=2


