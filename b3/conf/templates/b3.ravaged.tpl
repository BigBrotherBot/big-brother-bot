[b3]
parser: ravaged
database: mysql://b3:password@localhost/b3
bot_name: b3
bot_prefix: <FONT COLOR='#F9D90F'> B³:
time_format: %I:%M%p %Z %m/%d/%y
time_zone: CST
log_level: 9
logfile: @conf/b3.log
disabled_plugins:
external_plugins_dir: @b3/extplugins

[server]
public_ip:
# port: Ravaged Query port
port: 27015
rcon_ip: 127.0.0.1
rcon_port: 13550
rcon_password: ravaged!

[autodoc]
type: html
maxlevel: 100
@conf/b3_doc.html

[update]
channel: stable

[messages]
kicked_by: $clientname was kicked by $adminname $reason
kicked: $clientname was kicked $reason
banned_by: $clientname was banned by $adminname $reason
banned: $clientname was banned $reason
temp_banned_by: $clientname was temp banned by $adminname for $banduration $reason
temp_banned: $clientname was temp banned for $banduration $reason
unbanned_by: $clientname was un-banned by $adminname $reason
unbanned: $clientname was un-banned $reason

[plugins]
admin: @conf/plugin_admin.ini
adv: @conf/plugin_adv.xml
censor: @conf/plugin_censor.xml
cmdmanager: @conf/plugin_cmdmanager.ini
pingwatch: @conf/plugin_pingwatch.ini
spamcontrol: @conf/plugin_spamcontrol.ini
stats: @conf/plugin_stats.ini
status: @conf/plugin_status.ini
welcome: @conf/plugin_welcome.ini

# This is a non-standard plugin, and quite resource heavy. Please take a look in the B3 forums (look for
# XLR Extensions) for more information before enabling this. Extra database tables are necessary.
xlrstats: @b3/extplugins/conf/plugin_xlrstats.ini

