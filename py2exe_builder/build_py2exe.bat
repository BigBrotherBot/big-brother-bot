@echo off

set PYTHON_BIN="c:\Python26\python.exe"

cd ..
rmdir dist_py2exe /Q /S
%PYTHON_BIN% setupPy2exe.py py2exe
rmdir build /Q /S

xcopy ..\dist_py2exe\* py2exe_builder\Output\b3 /e /i

cd py2exe_builder/Output

ECHO ******************************************
SET /P M=Type version number, then press ENTER: 

7z.exe a -r -tzip b3-%M%.zip b3
rmdir b3 /Q /S
pause