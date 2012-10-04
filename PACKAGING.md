BigBrotherBot (B3) packaging documentation
==========================================

B3 is distributed as different packages :

  - python sources package
  - python egg package

as well as packages for the MS Windows plateform built with py2exe :

  - win32 zip package
  - win32 setup package (setup built with InnoSetup Installer)


# Requirements

To build the packages you need a computer running the MS Windows operating system with the following software installed :

  - python 2.7
  - all B3 python modules requirements B3 tests requirements (see pip-requires.txt)
  - py2exe
  - InnoSetup Installer with InnoSetup PreProcessor


# Environment setup

  - make sure python is in your PATH environment variable
  - update the py2exe_builder/build.yaml config file with the path to your InnoSetup Compiler


# Building packages

## Run the tests

We want to make sure there are no regressions or un-maintained test left behind. To quickly run all the tests, run `python setup.py test`.
If all tests pass, you are good to continue

## Update the version number

Open up setup.py and change the version string for the `b3version` variable at the top of the script, then run `python setup.py release`.
This command will build into the *releases* directory the python source, python egg packages and put into the *py2exe_builder/dist_py2exe* directory the project files 'compiled' for the win32 packages.
Then run the `python build.py` from the *py2exe_builder* directory to build the Windows packages that you will also find into the *releases* directory.


# Distribute the packages

Uupload the packages on a public place for users to download them?
