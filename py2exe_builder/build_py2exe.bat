@echo off

set PYTHON_BIN="c:\Python26\python.exe"

cd ..
rmdir ..\dist_py2exe /Q /S
%PYTHON_BIN% setupPy2exe.py py2exe
rmdir build /Q /S

copy py2exe_builder\readme-windows.txt ..\dist_py2exe\readme.txt
copy py2exe_builder\gpl-2.0.txt ..\dist_py2exe\license.txt
del ..\dist_py2exe\README /Q

xcopy ..\dist_py2exe\* py2exe_builder\Output\b3 /e /i

cd py2exe_builder/Output

ECHO ******************************************
SET /P M=Type version number, then press ENTER: 

7z.exe a -r -tzip b3-%M%-win32-noinstaller.zip b3
rmdir b3 /Q /S
cd ..
pause