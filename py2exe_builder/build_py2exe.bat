@echo off

set PYTHON_BIN="c:\Python26\python.exe"

cd ..
rmdir dist_py2exe /Q /S
%PYTHON_BIN% setupPy2exe.py py2exe
rmdir build /Q /S
pause