@echo off
echo *************CLEAN DIRECTORY*************
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q moethread.egg-info
echo *************BUILD WHEEL*************
python setup.py sdist bdist_wheel
echo *************UPLOAD TO PYPI*************
twine upload dist/*