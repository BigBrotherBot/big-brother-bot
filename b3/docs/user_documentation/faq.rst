Frequently Asked Questions
==========================

.. index:: faq

.. contents::
   :local:
   :depth: 1


How do I become superadmin?
---------------------------

Be the first one to type :command:`!iamgod` in the game chat.


Someone typed !iamgod before me ! what to do?
---------------------------------------------

Once the :command:`!iamgod` has been successfully used, it is not available anymore.

Chances are that you just installed B3 not long ago and can afford to delete the B3 database altogether and recreate it. Then:
 - make sure nobody is on your game server
 - restart B3
 - be the first one to type :command:`!iamgod`

If you don't want to delete your B3 database, you can remove the user from the superadmin group by editing the database.
For that you will need a tool to connect to your database and be able to alter it (see :ref:`mysql-tools`).

Once you are connected to the B3 database, open up the `clients` table. This table lists all players seen by B3 on your
game server.

To find who is in the superadmin group, sort the `clients` table on the `group_bits` column. A value of `128` indicates
that a player is in the superadmin group. Simply change the value `128` to `0` to remove the player from the superadmin
group.

Now that no one is superadmin anymore, you can restart B3 and make sure to be the first one to type :command:`!iamgod` in
the game chat.


Can B3 run remotely?
--------------------

For games B3 reads the game log file, refer to :ref:`remote-game-log-file`.

For other games, B3 just work from the RCON system alone.


Why does B3 not respond to my commands?
---------------------------------------

If B3 seems to be ignoring your commands there can be different reasons. To determine what is going wrong follow the
procedure:

  - restart B3
  - join your game server
  - type :command:`!help` in the game chat
  - open the B3 log file (often named :file:`b3.log`)
  - search your log file for the word `CONSOLE` (in upper case)

If you cannot find any line with `CONSOLE` in them
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

B3 has difficulties getting notified of what is happening on your game server. As a consequence, B3 is not even aware that
you typed a command in the game chat.

Depending on the game, B3 can be reading the game server log file. If this is the case, make sure the setting `game_log`
of your :file:`b3.xml` config file is correct. Also make sure you can find a line in that game log file that shows you
typing the `!help` command.

If B3 is not supposed to read any game server log file, then check your rcon settings in :file:`b3.xml`.

Make sure no line as `ERROR` in it in :file:`b3.log` file.


If you find lines with `CONSOLE` in them
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If none of them contains `!help` (the command you typed earlier), then check that the correct game log file is set for
`game_log` in your :file:`b3.xml` config file. Or check your rcon settings.
For CoD games, if you are running a game mod, then you should have different game log files in the mod folder. Make sure
B3 reads the one that is being written to by your game server.

If you can find the `CONSOLE` line that shows you typing the `!help` command your typed earlier, then examine the lines
that follow and look for any error that could give you hints about the issue.
Most likely, B3 was not able to send the response to the game server through rcon. If that is the case, tripple check
your rcon settings in :file:`b3.xml`.


B3 lags and is slow to respond to my commands
---------------------------------------------

If B3 is reading the game server log file, then your game log file might not be updated in real-time by the game server.

Check your game settings as instructed at :ref:`game-configuration`.


.. _remote-game-log-file:

Does B3 have to be installed on the game server for quake based games?
----------------------------------------------------------------------

No. B3 can read your game log file over different remote protocols such as FTP, SFTP, HTTP, HTTPS. In your :file:`b3.xml`
file, just set the `url` of your game log file for setting `game_log`.

.. note:: The `url` can contain the login and password if any. Example: ``ftp://my_login:my_password@my-hosting-provider.com/game.log``.

.. tip:: To verify your url is correct, paste it in your Internet browser and check the game log file content appears


Can I run B3 from a webhosting server?
--------------------------------------

No, B3 needs more than just a webserver. B3 depends also on Python and MySQL. Generally (some of) those
packages are not available on a webhosting environment.


I cant connect to my MySQL Database!!
-------------------------------------

First, make sure that the format of your MySQL info is correct in :file:`b3.xml` for setting `database`.

The syntax for the `database` setting is :

::

   mysql://<username>:<password>@<hostname>[:port]/<databasename>

.. option:: username

    the MySQL user that has privileges to access the B3 MySQL database

.. option:: password

    the MySQL password of the user that has privileges to access the B3 MySQL database

.. option:: hostname

    the hostname of the machine that runs the MySQL server. It can also be the IP address of that machine.

    .. tip:: if the hostname is `localhost` and you still have errors, try `127.0.0.1` instead of `localhost`

.. option:: port

    the port the MySQL server is listening on. Can be omitted if your MySQL server is listening on the default port : 3306

.. option:: databasename

    the name of the MySQL database B3 should use


Make sure all that info is correct by connecting to your MySQL database with a MySQL adminstration tool (see :ref:`mysql-tools`).


Can I run B3 on a LAN?
----------------------

Unfortunately not for all games.

For some games B3 uses Punkbuster (The Anti-Cheat tool) to authenticate players. Punkbuster doesn't authorize people on
LAN servers, so B3 will not run correctly.

Also the CoD series games will not provide you with a GUID, so on CoD B3 won't even work without PunkBuster on a LAN.


Can I run many different bots? Using the same sort of settings and database?
----------------------------------------------------------------------------

Yes you can run many bots on the same machine. You can also have many B3 bots sharing the same database, as long as its
the same game (eg. 2 x CoD2 Servers).

If you wish to do this then you need to make another B3 config file (eg. :file:`b3-2.xml`) with the details of your other
game server.

Then you need to tell your second B3 to start using the new config file :file:`b3-2.xml`. To do so, use the :option:`--config`
argument of the :command:`b3_run` program.

::

    b3_run.exe --config "C:\b3\conf\b3-2.xml"


I need a provider that sell game servers with B3 bot! Dedicated servers are far too expensive for our clan.
-----------------------------------------------------------------------------------------------------------

There are indeed a few providers that will allow you to buy game servers with B3 Bot installed! Also you can find
companies that will just host your B3 alone.

See list of `hosting providers`_


b3_run.exe fails to start
-------------------------

If the error message is:::

 This application has failed to start because the application configuration is incorrect. Reinstalling the application may fix this problem

then you most likely are missing a few dll. Install the `Microsoft Visual C++ 2008 Redistributable Package (x86)`_


The time is off by an hour
--------------------------

B3 does not automatically apply daylight saving time changes. To reflect summer/winter time change, you have to tell B3
explicitly in the :file:`b3.xml` main config file. see `available_timezones`_

B3 doesn't support python 2.4 and I'm on CentOS... now what?
------------------------------------------------------------

While B3 can work on python 2.6, it is advised to run in with python 2.7.

Python 2.6 is not at all in the Standard Repos of the RHEL / CentOS. Install Python 2.6 will work only, when you use the
epel Repository which can found here:

https://fedoraproject.org/wiki/EPEL

To install it use:

for 32bit systems

.. code-block:: none

    su -c 'rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-3.noarch.rpm'

for 64bit systems

.. code-block:: none

     su -c 'rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-3.noarch.rpm'

after that you can do:

.. code-block:: none

     yum install python26 mod_python26


Will B3 run with python on Windows 2k3 server 64-bit?
-----------------------------------------------------

B3 will run just fine under Server 2K3 64-bit. The trick is to use 100% 32-bit Python.

If you get the same error when trying to execute the 32-bit Python installers, get `Microsoft's 32-bit C++ runtime`_.


CRITICAL Error loading plugin: No module named ...
--------------------------------------------------

If you have an error in your :file:`b3.log` file complaining about a plugin that could be loaded:::

  091030 09:59:42   CRITICAL   Error loading plugin: No module named xlrstats
  Traceback (most recent call last):
    File "/usr/lib/python2.5/site-packages/b3-1.2.1-py2.5.egg/b3/parser.py", line 437, in loadPlugins
      pluginModule = self.pluginImport(p)
    File "/usr/lib/python2.5/site-packages/b3-1.2.1-py2.5.egg/b3/parser.py", line 500, in pluginImport
      fp, pathname, description = imp.find_module(name, [self.config.getpath('plugins', 'external_dir')])
  ImportError: No module named xlrstats


Then verify that the plugin file does exist in the `extplugins` folder of the B3 installation directory.

It the plugin `.py` exists in the right folder, then also check that file is not copied a second time in another folder
of your B3 installation directory.

Using B3 remote with sshfs
--------------------------

**Q:**
  I have been playing sshfs to monitor a remote server with b3. It works, but is kinda weird. If I mount with sshfs
  the remote game server dir in the box where b3 is running and then send a command from the game, for example !time,
  b3 will see the command like after two or three minutes. BUT, if I do a tail/cat/more of the game log file in the
  sshfs'ed mounted  directory then b3 will immediately see the command in the log and respond.
  If I leave a tail -f game.log running then b3 will work perfectly, and when stopped it then b3 will again start to react
  two or three minutes after.


**A:**
  The magic parameters are `direct_io` and `cache=no`. It works like a charm. You will mount it like this:::

      sshfs -odirect_io,cache=no urban@xxx.xxx.xxx.xxx:/home/urban/UrbanTerror servers/remote_server/


To avoid having to enter the remote user password each time you mount the remote dir you will have to generate a ssh
key pair with the ssh-keygen command and upload the public key to the game server :file:`.ssh/authorized_keys` file.
*(Thanks to Mazter)*


How to run B3 on Free BSD or MAC OS X
-------------------------------------

**Q:**
  On some Free BSD and Mac OS X, B3 does not read game log file content. As a result it does not respond to your in-game commands.

**A:**
  This topic on the forum as two solutions. One is to apply a patch on your Python installation while the other one is a patch to apply to B3



.. _`hosting providers`: http://www.bigbrotherbot.net/forums/general-discussion/gameserver-providers-that-support-b3/
.. _`Microsoft Visual C++ 2008 Redistributable Package (x86)`: http://www.microsoft.com/downloads/details.aspx?FamilyID=9b2da534-3e03-4391-8a4d-074b9f2bc1bf
.. _`available_timezones`: http://wiki.bigbrotherbot.net/usage:available_timezones
.. _`Microsoft's 32-bit C++ runtime`: http://www.microsoft.com/downloads/details.aspx?familyid=9b2da534-3e03-4391-8a4d-074b9f2bc1bf&displaylang=en