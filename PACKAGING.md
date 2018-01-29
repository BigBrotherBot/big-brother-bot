BigBrotherBot (B3) packaging documentation
==========================================

B3 is distributed as different packages:

  - Python sources package as a zip file
  - Python wheel package
  - Win32 zip package
  - Win32 installer package (built with InnoSetup Installer)

# Bumping the version number

You need the bumpversion tool for that task. See https://pypi.python.org/pypi/bumpversion/

Usage:

    bumpversion patch # will change "1.10.0" to "1.10.1"
    bumpversion minor # will change "1.10.0" to "1.11.0" 
    bumpversion major # will change "1.10.0" to "2.0.0"


# Packaging B3

To be able to build B3 distribution packages you need to have installed Python 2.7 32bit on your system.
You can check your python version by starting the python interpreter in a terminal window (or command 
prompt on win32 platform). Also you need to make sure to have `python` in your PATH environment variable.  
You also need to have installed [GIT](http://git-scm.com/) on your system and make sure that the `git` command
is in your PATH environment. Once the building process is completed you will find the built package(s) inside the 
*dist* directory.

## Source and wheel distribution

Open a terminal window (or command prompt if on win32 platform) and type the following commands:

 - clone big brother bot repository:
    - `git clone https://github.com/BigBrotherBot/big-brother-bot.git`
    - `cd big-brother-bot`
 - build source and wheel packages:
    - `python setup.py release`

## Windows

Install [Microsofts Visual C++ Compiler for Python2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266).  
Install [InnoSetup](http://www.jrsoftware.org/isinfo.php).  
Install [psycopg2](http://www.stickpeople.com/projects/python/win-psycopg/).  
Install [pycripto](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).  
Install [paramiko](http://blog.victorjabur.com/2011/06/08/modules-python-library-compiled-for-windows-32-and-64-unofficial-windows-binaries-for-python/).  
Install [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze/4.3.4).  
Make sure to have `pip` in your PATH environment.  
  
Open a command prompt window and type the following:

 - clone big brother bot repository:
    - `git clone https://github.com/BigBrotherBot/big-brother-bot.git`
    - `cd big-brother-bot`
 - install python requirements:
    - `pip install -r requirements.txt`
    - `pip install -r build-requirements.txt`
 - update `installer/innosetup/build.yaml` config file with the path to your InnoSetup compiler.
 - build the frozen application:
    - `python setup.py egg_info`
    - `python setup.py build_exe`