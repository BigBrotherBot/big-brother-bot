<configuration>
	<settings name="b3">
		<set name="parser">bf3</set>
		<set name="database">mysql://myuser:mypass@mydbhost/mydbname</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">(b3):</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CEST</set>
		<set name="log_level">9</set>
		<set name="logfile">@conf/b3.log</set>
	</settings>
	<settings name="bf3">
        <!-- max_say_line_length : when sending a message, lines will have at most this number of characters. -->
		<set name="max_say_line_length">128</set>
		<!-- message_delay : the delay (in second) to wait between two messages -->
        <set name="message_delay">0.8</set>
	</settings>
	<settings name="server">
		<set name="public_ip">11.22.33.44</set>
		<set name="port">19567</set>
		<set name="rcon_ip">11.22.33.44</set>
		<set name="rcon_port">48888</set>
		<set name="rcon_password">myrconpassword</set>
		<set name="timeout">3</set>
        <!-- ban_agent : choose how to ban players.
            Available agents are : 'server' or 'punkbuster'.
            Available options are :
             'server' : to save bans in the BF3 server banlist only
             'punkbuster' : to save bans in punkbuster only
             'both' : to save bans in both the BF3 server and punkbuster banlists
            Default value is 'server'
        -->
        <set name="ban_agent">server</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
        <set name="destination">@conf/b3_doc.htm</set>
	</settings>
	<settings name="messages">
		<set name="kicked_by">$clientname was kicked by $adminname ($reason)</set>
		<set name="kicked">$clientname was kicked ($reason)</set>
		<set name="banned_by">$clientname was banned by $adminname ($reason)</set>
		<set name="banned">$clientname was banned ($reason)</set>
		<set name="temp_banned_by">$clientname was temp banned by $adminname for $banduration ($reason)</set>
		<set name="temp_banned">$clientname was temp banned for $banduration ($reason)</set>
		<set name="unbanned_by">$clientname was un-banned by $adminname ($reason)</set>
		<set name="unbanned">$clientname was un-banned ($reason)</set>
	</settings>
	<settings name="plugins">
		<set name="external_dir">@b3/extplugins</set>
	</settings>
	<plugins>
		<plugin name="censor" config="@conf/plugin_censor.xml"/>
		<plugin name="spamcontrol" config="@b3/conf/plugin_spamcontrol.xml"/>
		<plugin name="admin" config="@conf/plugin_admin.xml"/>
		<!-- <plugin name="pingwatch" config="@conf/plugin_pingwatch.xml" /> NO PING INFO AVAILABLE FROM BF3 -->
		<plugin name="adv" config="@conf/plugin_adv.xml"/>
		<plugin name="status" config="@conf/plugin_status.xml"/>
		<plugin name="welcome" config="@conf/plugin_welcome.xml"/>
		<!-- <plugin name="punkbuster" config="@conf/plugin_punkbuster.xml"/> -->
	</plugins>
    <extplugins>
        <plugin name="poweradminbf3" config="external_dir/conf/plugin_poweradminbf3.xml"
                dlocation="http://forum.bigbrotherbot.net/index.php?action=downloads;sa=downfile&amp;id=172"/>
        <plugin name="chatlogger" config="external_dir/conf/plugin_chatlogger.xml"
                dlocation="http://github.com/courgette/b3-plugin-chatlogger/zipball/v1.0" sql="chatlogger.sql"/>
        <plugin name="xlrstats" config="external_dir/conf/xlrstats.xml" sql="xlrstats.sql"/>
        <plugin name="ctime" dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=146" sql="ctime.sql"/>
        <plugin name="makeroom" config="external_dir/conf/plugin_makeroom.xml" dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=148"/>
        <plugin name="metabans" config="external_dir/conf/plugin_metabans.xml" dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=153"/>
    </extplugins>
</configuration>