[b3]
parser: bf3
database: mysql://b3:password@localhost/b3
bot_name: b3
bot_prefix:
time_format: %I:%M%p %Z %m/%d/%y
time_zone: CST
log_level: 9
logfile: @conf/b3.log
disabled_plugins:
external_plugins_dir: @b3/extplugins

[bf3]
# message_delay : the delay (in second) to wait between two messages
message_delay: 0.8
# big_b3_private_responses - if on, then all private message sent by B3 will be displayed as a large on-screen message
big_b3_private_responses: on
# big_msg_repeat - B3 repeated big displayed messages in the chat.
# accepted values : all (repeat all) / pm (repeat private messages) / off (disabled)
big_msg_repeat: pm
# big_msg_duration : for how many seconds big messages are displayed
big_msg_duration: 6

[server]
public_ip: 11.22.33.44
port: 19567
rcon_ip: 11.22.33.44
rcon_port: 48888
rcon_password: myrconpassword
timeout: 3
# ban_agent : choose how to ban players
# available agents are : 'server' or 'punkbuster'
# available options are :
#   'server' : to save bans in the BF3 server banlist only
#   'punkbuster' : to save bans in punkbuster only
#   'both' : to save bans in both the BF3 server and punkbuster banlists
ban_agent: server

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
#punkbuster: @conf/plugin_punkbuster.ini
spamcontrol: @conf/plugin_spamcontrol.ini
stats: @conf/plugin_stats.ini
status: @conf/plugin_status.ini
welcome: @conf/plugin_welcome.ini

# This is a non-standard plugin, and quite resource heavy. Please take a look in the B3 forums (look for
# XLR Extensions) for more information before enabling this. Extra database tables are necessary.
xlrstats: @b3/extplugins/conf/plugin_xlrstats.ini
