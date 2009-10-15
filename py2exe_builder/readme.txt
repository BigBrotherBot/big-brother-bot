This folder holds the tools and scripts to build a .exe release of B3
and an installer.

REQUIREMENTS:
    Environment :
        * a Windows OS
        * with python2.5
        * with elementtree (if required)
        * with mysqldb
    Tools:
        * py2exe2.5
        * Innosetup
        * ISTools (optional)
    
HOW TO BUILD THE .EXE RELEASE:
    * edit build_py2exe.bat with your python path
    * run it
    * check that there is no error
    * build is ready to test in the "dist_py2exe" folder
    
HOW TO BUILD THE INSTALLER:
    * open b3-installer-project.iss with InnoSetup or ISTools
    * compile it
    * test it
    