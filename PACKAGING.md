BigBrotherBot (B3) packaging documentation
==========================================

B3 is distributed as different packages :

  - python sources package as a zip file
  - python egg package

as well as packages for the MS Windows plateform built with py2exe :

  - win32 zip package
  - win32 installer package (built with InnoSetup Installer)


# Requirements

To build the packages you need a computer running the MS Windows operating system with the following software installed :

  - python 2.7 32bit
  - all B3 python modules requirements B3 tests requirements (see requirements.txt and build-requirements.txt)
  - cx_freeze
    - Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)
    - [Microsoft Visual C++ Compiler for Python 2.7](http://aka.ms/vcpython27)
  - InnoSetup Installer with InnoSetup PreProcessor


# Environment setup

  - make sure python is in your PATH environment variable
  - update the installer/innosetup/build.yaml config file with the path to your InnoSetup Compiler


# Building packages

## Run the tests

We want to make sure there are no regressions or un-maintained test left behind. To quickly run all the tests, run `python setup.py test`.
If all tests pass, you are good to continue

## Update the version number

Open up setup.py and change the version string for the `b3version` variable at the top of the script, then run `python setup.py release`.
This command will build into the *dist* directory the different packages.


# Distribute the packages

Uupload the packages on a public place for users to download them?
