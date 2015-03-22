Geolocation Plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
====================================

Description
-----------
A [BigBrotherBot][B3] plugin which introduces geolocation capabilities. This plugin is meant to be used as subplugin 
since it doesn't provide commands or visual reaction to B3 events. The plugin intercepts new clients connection and
retrieve geolocation data using multiple data sources:

* [IP api](http://ip-api.com/)
* [Telize](http://www.telize.com/)
* [Free GeoIP](https://freegeoip.net/)
* [MaxMind GeoIP](http://dev.maxmind.com/geoip/legacy/install/country/)

For plugin developers
---------------------
To notify other plugins of client geolocation being completed, two events are being fired:

* `EVT_CLIENT_GEOLOCATION_SUCCESS` : when the geolocation succeeds
* `EVT_CLIENT_GEOLOCATION_FAILURE` : when the geolocation fails

When the geolocation succeed a new attribute is added the the `b3.clients.Client` object: `location`. This attribute
will hold all the geolocation data the plugin could retrieve:
 
* `client.location.country` : the country name
* `client.location.region` : the region name
* `client.location.city` : the city name
* `client.location.cc` : the two letter country code
* `client.location.rc` : the two letter region code
* `client.location.isp` : the Internet Service Provider name
* `client.location.lat` : the latitude value
* `client.location.lon` : the longitude value
* `client.location.timezone` : the timezone string
* `client.location.zipcode` : the postal code

*NOTE #1* : when `EVT_CLIENT_GEOLOCATION_FAILURE` is fired `client.location` is set to `None`  
*NOTE #2* : when the plugin cannot retrieve a specific geolocation value, its attribute is set to `None`

Download
--------
Latest version available [here](https://github.com/danielepantaleone/b3-plugin-geolocation/archive/master.zip).

Requirements
------------
This plugin is meant to work only with B3 version **1.10dev** or higher. No **1.9.x** version will be released since 
the plugin makes use of some new B3 core features which have been added in version 1.10 development branch.

Installation
------------
Simply drop the `geolocation` directory into `b3/extplugins`. B3 will automatically load the plugin if needed. If you want you can load the plugin in b3 main configuration file but it's not mandatory.

Changelog
---------
### 1.3 - 2015/03/20 - Fenix
 - reworked external module imports
 - renamed Locator class (and all inherited ones) into Geolocator: updated module name
 - moved GeoIP.dat file into lib/geoip/db folder
 
### 1.2 - 2015/03/19 - Fenix
 - minor code changes to respect PEP8 constraints
 - import single locators classes instead of importing the whole module
 
### 1.1 - 2015/03/17 - Fenix
 - now plugin reacts also on EVT_CLIENT_UPDATE: see http://bit.ly/1LmHpIJ
 
### 1.0 - 2015/03/12 - Fenix
- initial release

Support
-------
If you have found a bug or have a suggestion for this plugin, please report it on the [B3 forums][Support].

[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"
[Support]: http://forum.bigbrotherbot.net/ "Support topic on the B3 forums"

[![Build Status](https://travis-ci.org/danielepantaleone/b3-plugin-geolocation.svg?branch=master)](https://travis-ci.org/danielepantaleone/b3-plugin-geolocation)
[![Code Health](https://landscape.io/github/danielepantaleone/b3-plugin-geolocation/master/landscape.svg?style=flat)](https://landscape.io/github/danielepantaleone/b3-plugin-geolocation/master)