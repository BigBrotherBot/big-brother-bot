#!/bin/bash

set -ev

# NOTE: this is supposed to be run from Travis CI console, so the current directory is the one outside
python setup.py egg_info --tag-build .dev${TRAVIS_COMMIT:0:7} --tag-date sdist bdist_wheel
python setup.py build_exe