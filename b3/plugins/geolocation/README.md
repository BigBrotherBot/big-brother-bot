Geolocation Plugin for BigBrotherBot
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