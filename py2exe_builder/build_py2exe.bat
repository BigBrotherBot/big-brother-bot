@echo off

set PYTHON_BIN="e:\Windows7\python2.5\python.exe"

cd ..
rmdir dist_py2exe /Q /S
%PYTHON_BIN% setupPy2exe.py py2exe
rmdir build /Q /S 
pause
