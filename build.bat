@echo off
echo *************CLEAN DIRECTORY*************
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q moevat.egg-info
echo *************BUILD WHEEL*************
python setup.py sdist bdist_wheel