###################################################################################
#
# Plugin for B3 (www.bigbrotherbot.com)
# Library and original code for Battlefield2 by Guwashi <guwashi[AT]fooos[DOT]com>
# Plugin (c) 2006-2014 www.xlr8or.com
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
# http://www.gnu.org/copyleft/gpl.html
#
# This product includes GeoIP data created by MaxMind, available
# from http://maxmind.com/
###################################################################################

Countryfilter (v1.x) for B3
###################################################################################
This plugin provides an allow/deny mechanism for connecting players based on their
Country-IP (GeoIP data). It announces connecting players in the server so you can
see where the player is connecting from. Even if you don't have anny countries
on the deny list, it's still nice to see where your playercrowd is connecting from!

- !cfcountry <player> will return the country the player is connecting from.


Requirements:
###################################################################################

- B3 version 1.2.2 or higher

Installation:
###################################################################################

1. Unzip the contents of this package into your B3 folder. It will
place the .py file in b3/extplugins and the config file .xml in
your b3/extplugins/conf folder. 

2. Open the .xml file with your favorit editor and modify the
settings if you want them different. Do not edit the settingnames
for they will not function under a different name.

3. Open your B3.xml file (in b3/conf) and add the next line in the
<plugins> section of the file:

<plugin name="countryfilter" config="@b3/extplugins/conf/countryfilter.xml"/>


Updating the Geo-data:
###################################################################################
Download GeoIP.dat from
http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
and extract it into extplugins/GeoIP/


Changelog
###################################################################################
v1.0.0         : Initial release
v1.1.0         : Added !cfcountry command for already connected players
v1.1.2         : Bugfix version
v1.1.6         : Updated to work properly with B3 win32 standalone realease. Requires B3 v1.2.2
v1.2.0         : Added support for BF:BC2 (PB enabled servers only!)
v1.2.1         : Added support for MOH (PB enabled servers only!)
v1.3           : Added support for BF3 (PB enabled servers only!)
v1.4           : Moved maxlevel setting to 'settings section'
                 Added ip blocking function and section in config file
                 Fixed and re-ordered config file.
###################################################################################
xlr8or - 2007/2014 - www.bigbrotherbot.net
