#!/bin/bash

set -ev

pip install --upgrade pip
pip install -r requirements.txt
pip install -r build-requirements.txt
pip install -r optional-requirements.txt
pip install -r test-requirements.txt