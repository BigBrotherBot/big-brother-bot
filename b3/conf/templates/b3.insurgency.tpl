[b3]
parser: insurgency
database: mysql://b3:password@localhost/b3
bot_name: b3
bot_prefix: [b3]:
time_format: %I:%M%p %Z %m/%d/%y
time_zone: CST
log_level: 9
logfile: @conf/b3.log
disabled_plugins:
external_plugins_dir: @b3/extplugins

[server]
rcon_password: password
port: 27960
game_log: http://serverhost/path/to/games_mp.log
public_ip: 127.0.0.1
rcon_ip: 127.0.0.1
punkbuster: off
delay: 0.33
lines_per_second: 50

[autodoc]
type: html
maxlevel: 100
destination: @conf/b3_doc.html

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
tk: @conf/plugin_tk.ini
welcome: @conf/plugin_welcome.ini

# This is a non-standard plugin, and quite resource heavy. Please take a look in the B3 forums (look for
# XLR Extensions) for more information before enabling this. Extra database tables are necessary.
xlrstats: @b3/extplugins/conf/plugin_xlrstats.ini
