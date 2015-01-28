[b3]
parser: smg
database: mysql://b3:password@localhost/b3
bot_name: b3
bot_prefix: ^0[^2b3^0]^7:
time_format: %I:%M%p %Z %m/%d/%y
time_zone: CST
log_level: 9
logfile: @conf/b3.log
disabled_plugins:
external_plugins_dir: @b3/extplugins

[server]
rcon_password: password
port: 27960
game_log: games_mp.log
public_ip: 127.0.0.1
rcon_ip: 127.0.0.1
punkbuster: off
delay: 0.33
lines_per_second: 50

[autodoc]
type: html
maxlevel: 100
@conf/b3_doc.html

[update]
channel: stable

[messages]
kicked_by: $clientname^7 was kicked by $adminname^7 $reason
kicked: $clientname^7 was kicked $reason
banned_by: $clientname^7 was banned by $adminname^7 $reason
banned: $clientname^7 was banned $reason
temp_banned_by: $clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason
temp_banned: $clientname^7 was temp banned for $banduration^7 $reason
unbanned_by: $clientname^7 was un-banned by $adminname^7 $reason
unbanned: $clientname^7 was un-banned^7 $reason

[plugins]
admin: @conf/plugin_admin.ini
adv: @conf/plugin_adv.xml
censor: @conf/plugin_censor.xml
cmdmanager: @conf/plugin_cmdmanager.ini
pingwatch: @conf/plugin_pingwatch.ini
#punkbuster: @conf/plugin_punkbuster.ini
spamcontrol: @conf/plugin_spamcontrol.ini
stats: @conf/plugin_stats.ini
status: @conf/plugin_status.ini
tk: @conf/plugin_tk.ini
welcome: @conf/plugin_welcome.ini

# This is a non-standard plugin, and quite resource heavy. Please take a look in the B3 forums (look for
# XLR Extensions) for more information before enabling this. Extra database tables are necessary.
xlrstats: @b3/extplugins/conf/plugin_xlrstats.ini
