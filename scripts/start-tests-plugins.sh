#!/bin/bash

set -ev

nosetests --where=tests.plugins.admin --verbosity=3 --with-cov --cov b3.plugins.admin --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.adv --verbosity=3 --with-cov --cov b3.plugins.adv --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.banlist --verbosity=3 --with-cov --cov b3.plugins.banlist --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.callvote --verbosity=3 --with-cov --cov b3.plugins.callvote --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.censor --verbosity=3 --with-cov --cov b3.plugins.censor --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.chatlogger --verbosity=3 --with-cov --cov b3.plugins.chatlogger --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.cmdmanager --verbosity=3 --with-cov --cov b3.plugins.cmdmanager --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.countryfilter --verbosity=3 --with-cov --cov b3.plugins.countryfilter --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.customcommands --verbosity=3 --with-cov --cov b3.plugins.customcommands --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.duel --verbosity=3 --with-cov --cov b3.plugins.duel --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.firstkill --verbosity=3 --with-cov --cov b3.plugins.firstkill --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.ftpytail --verbosity=3 --with-cov --cov b3.plugins.ftpytail --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.geolocation --verbosity=3 --with-cov --cov b3.plugins.geolocation --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.ipban --verbosity=3 --with-cov --cov b3.plugins.ipban --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.jumper --verbosity=3 --with-cov --cov b3.plugins.jumper --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.location --verbosity=3 --with-cov --cov b3.plugins.location --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.login --verbosity=3 --with-cov --cov b3.plugins.login --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.admin --verbosity=3 --with-cov --cov b3.plugins.admin --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.nickreg --verbosity=3 --with-cov --cov b3.plugins.nickreg --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.pluginmanager --verbosity=3 --with-cov --cov b3.plugins.pluginmanager --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.poweradminbf3 --verbosity=3 --with-cov --cov b3.plugins.poweradminbf3 --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.poweradminurt --verbosity=3 --with-cov --cov b3.plugins.poweradminurt --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.publist --verbosity=3 --with-cov --cov b3.plugins.publist --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.sftpytail --verbosity=3 --with-cov --cov b3.plugins.sftpytail --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.spamcontrol --verbosity=3 --with-cov --cov b3.plugins.spamcontrol --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.spawnkill --verbosity=3 --with-cov --cov b3.plugins.spawnkill --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.spree.test_commands --verbosity=3 --with-cov --cov b3.plugins.spree --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.spree.test_conf --verbosity=3 --with-cov --cov b3.plugins.spree --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.spree.test_events --verbosity=3 --with-cov --cov b3.plugins.spree --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.stats --verbosity=3 --with-cov --cov b3.plugins.status --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.tk --verbosity=3 --with-cov --cov b3.plugins.tk --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.translator --verbosity=3 --with-cov --cov b3.plugins.translator --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.urtserversidedemo --verbosity=3 --with-cov --cov b3.plugins.urtserversidedemo --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.welcome --verbosity=3 --with-cov --cov b3.plugins.welcome --cov-report term-missing --cov-config .coveragerc
nosetests --where=tests.plugins.xlrstats --verbosity=3 --with-cov --cov b3.plugins.xlrstats --cov-report term-missing --cov-config .coveragerc

py.test tests/plugins/makeroom
py.test tests/plugins/afk