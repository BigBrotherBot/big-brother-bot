#!/bin/bash

set -ev

nosetests --where=tests.plugins.admin --verbosity=3
#nosetests --where=tests.plugins.adv --verbosity=3
nosetests --where=tests.plugins.banlist --verbosity=3
#nosetests --where=tests.plugins.callvote --verbosity=3
nosetests --where=tests.plugins.censor --verbosity=3
nosetests --where=tests.plugins.censorurt --verbosity=3
nosetests --where=tests.plugins.chatlogger --verbosity=3
nosetests --where=tests.plugins.cmdmanager --verbosity=3
nosetests --where=tests.plugins.countryfilter --verbosity=3
nosetests --where=tests.plugins.customcommands --verbosity=3
nosetests --where=tests.plugins.duel --verbosity=3
nosetests --where=tests.plugins.firstkill --verbosity=3
nosetests --where=tests.plugins.ftpytail --verbosity=3
nosetests --where=tests.plugins.geolocation --verbosity=3
nosetests --where=tests.plugins.ipban --verbosity=3
#nosetests --where=tests.plugins.jumper --verbosity=3
nosetests --where=tests.plugins.location --verbosity=3
nosetests --where=tests.plugins.login --verbosity=3
nosetests --where=tests.plugins.admin --verbosity=3
nosetests --where=tests.plugins.nickreg --verbosity=3
#nosetests --where=tests.plugins.pluginmanager --verbosity=3
#nosetests --where=tests.plugins.poweradminbf3 --verbosity=3
#nosetests --where=tests.plugins.poweradminurt --verbosity=3
nosetests --where=tests.plugins.publist --verbosity=3
nosetests --where=tests.plugins.sftpytail --verbosity=3
nosetests --where=tests.plugins.spamcontrol --verbosity=3
nosetests --where=tests.plugins.spawnkill --verbosity=3
nosetests --where=tests.plugins.spree.test_commands --verbosity=3
nosetests --where=tests.plugins.spree.test_conf --verbosity=3
nosetests --where=tests.plugins.spree.test_events --verbosity=3
nosetests --where=tests.plugins.stats --verbosity=3
nosetests --where=tests.plugins.tk --verbosity=3
nosetests --where=tests.plugins.translator --verbosity=3
#nosetests --where=tests.plugins.urtserversidedemo --verbosity=3
nosetests --where=tests.plugins.welcome --verbosity=3
nosetests --where=tests.plugins.xlrstats --verbosity=3

py.test tests/plugins/makeroom
py.test tests/plugins/afk