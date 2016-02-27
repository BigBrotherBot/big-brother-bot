#!/bin/bash

set -ev

export DISPLAY=:99.0
sh -e /etc/init.d/xvfb start

# Qt5
sudo add-apt-repository --yes ppa:ubuntu-sdk-team/ppa
sudo apt-get update -qq
sudo apt-get install qtbase5-dev qtdeclarative5-dev libqt5webkit5-dev libsqlite3-dev
sudo apt-get install qt5-default qttools5-dev-tools

# CREATE DOWNLOADS DIRECTORY
sudo mkdir -p downloads && sudo chmod a+rw downloads && cd downloads

# SIP
wget http://downloads.sourceforge.net/project/pyqt/sip/sip-4.16.7/sip-4.16.7.tar.gz
tar xzf sip-4.16.7.tar.gz --keep-newer-files && cd sip-4.16.7
python configure.py
make -j5
sudo make install
cd ..

# PyQt5
wget http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.3/PyQt-gpl-5.3.tar.gz
tar xzf PyQt-gpl-5.3.tar.gz --keep-newer-files && cd PyQt-gpl-5.3
python configure.py -c --confirm-license --no-designer-plugin -e QtCore -e QtGui -e QtWidgets
make -j5
sudo make install
cd ..

# REMOVE DOWNLOADS DIRECTORY
cd .. && sudo rm -R downloads

# PIP PACKAGES
pip install --upgrade pip
pip install -r requirements.txt
pip install -r build-requirements.txt
pip install -r optional-requirements.txt
pip install -r test-requirements.txt