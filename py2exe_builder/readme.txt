This folder holds the tools and scripts to build a .exe release of B3
and an installer.
This script will take the B3 version found in the b3.egg-info folder, so you need to have run the
setup.py tool before.

REQUIREMENTS:
    Environment :
        * a Windows OS
        * with python2.6+
        * with mysqldb
    Tools:
        * py2exe2.6+
        * InnoSetup
        * InnoSetup preprocessor
        * ISTools (optional)
    
HOW TO BUILD THE .EXE RELEASE and distributions :
    * check the build.yaml config file
    * run python.exe build.py

    