#!/bin/bash

set -ev

# NOTE: this is supposed to be run from Travis CI console, so the current directory is the one outside
nosetests --where=tests.core --verbosity=3 --with-cov --cov b3 --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.core.clients --verbosity=3 --with-cov --cov b3.clients --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.core.parsers --verbosity=3 --with-cov --cov b3.parsers --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.core.storage --verbosity=3 --with-cov --cov b3.storage --cov-report term-missing --cov-config .coveragerc