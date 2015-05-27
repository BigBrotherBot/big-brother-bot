# Netblocker plugin for B3

This plugin is an ip (range) blocker. Do not mistake this plugin with a firewall, because it does not provide that kind
of security. If you need to secure your system you should use a proper firewall.

This plugin can be used to prevent clients from playing on your B3 enabled server. It checks the IP address against
your list of blocked IP's when the client is authorized by B3. If the address is prohibited from connecting the client
will be kicked consequently.

The plugin can handle only IPv4 type IP addresses and relies on the game/parser on providing that IP address to the plugin.

## Ranges

The plugin can handle IP addresses or ranges in the following formats:

- single IP address: 127.0.0.1
- IP range: 127.0.0.1-127.0.0.100
- CIDR notation: 192.168.100.0/24
- combination of the above seperated by a comma (,)

### Example
    
    netblock: 127.0.0.1, 127.0.0.1-127.0.10.225, 168.0.0.0/8, 127.0/8

## Credits

_This plugin makes use of the netblock module for python created by 'siebenmann' (https://github.com/siebenmann/python-netblock)_

  