#!/bin/sh

export DISPLAY=:99.0
sh -e /etc/init.d/xvfb start
# downloads
sudo mkdir -p /downloads
sudo chmod a+rw /downloads
if [ ! -f /downloads/sip.tar.gz ]; then curl -L -o /downloads/sip.tar.gz http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.7/sip-4.16.7.tar.gz; fi
if [ ! -f /downloads/pyqt5.tar.gz ]; then curl -L -o /downloads/pyqt5.tar.gz http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.3/PyQt-gpl-5.3.tar.gz; fi
# Qt5
sudo add-apt-repository --yes ppa:ubuntu-sdk-team/ppa
sudo apt-get update -qq
sudo apt-get install qtbase5-dev qtdeclarative5-dev libqt5webkit5-dev libsqlite3-dev
sudo apt-get install qt5-default qttools5-dev-tools
# builds
sudo mkdir -p /builds
sudo chmod a+rw /builds
pushd /builds
# SIP
tar xzf /downloads/sip.tar.gz --keep-newer-files
pushd sip-4.16.7
python configure.py
make -j5
sudo make install
popd
# PyQt5
tar xzf /downloads/pyqt5.tar.gz --keep-newer-files
pushd PyQt-gpl-5.3
python configure.py -c --confirm-license --no-designer-plugin -e QtCore -e QtGui -e QtWidgets
make -j5
sudo make install
popd
# builds complete
popd
