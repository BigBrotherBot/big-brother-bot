<configuration>
	<settings name="b3">
		<set name="parser">moh</set>
		<set name="database">mysql://myuser:mypass@mydbhost/mydbname</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">^0(^2b3^0)^7:</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CEST</set>
		<set name="log_level">9</set>
		<set name="logfile">b3.log</set>
	</settings>
	<settings name="moh">
		<set name="max_say_line_length">100</set>
	</settings>
	<settings name="server">
		<set name="public_ip">11.22.33.44</set>
		<set name="port">19567</set>
		<set name="rcon_ip">11.22.33.44</set>
		<set name="rcon_port">48888</set>
		<set name="rcon_password">myrconpassword</set>
		<set name="timeout">3</set>
		<set name="punkbuster">off</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
        <set name="destination">b3_doc.htm</set>
	</settings>
	<settings name="messages">
		<set name="kicked_by">$clientname was kicked by $adminname $reason</set>
		<set name="kicked">$clientname was kicked $reason</set>
		<set name="banned_by">$clientname was banned by $adminname $reason</set>
		<set name="banned">$clientname was banned $reason</set>
		<set name="temp_banned_by">$clientname was temp banned by $adminname for $banduration $reason</set>
		<set name="temp_banned">$clientname was temp banned for $banduration $reason</set>
		<set name="unbanned_by">$clientname was un-banned by $adminname $reason</set>
		<set name="unbanned">$clientname was un-banned $reason</set>
	</settings>
	<settings name="plugins">
		<set name="external_dir">@b3/extplugins</set>
	</settings>
	<plugins>
		<plugin name="censor" config="@conf/plugin_censor.xml"/>
		<plugin name="spamcontrol" config="@b3/conf/plugin_spamcontrol.xml"/>
		<plugin name="admin" config="@conf/plugin_admin.xml"/>
		<plugin name="pingwatch" config="@conf/plugin_pingwatch.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml"/>
		<plugin name="status" config="@conf/plugin_status.xml"/>
		<plugin name="welcome" config="@conf/plugin_welcome.xml"/>
		-->
	</plugins>
    <extplugins>
        <plugin name="poweradminmoh" config="external_dir/conf/plugin_poweradminmoh.xml"
                dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=127"/>
        <plugin name="banlist" config="external_dir/conf/banlist.xml"
                dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=6"/>
        <plugin name="chatlogger" config="external_dir/conf/plugin_chatlogger.xml"
                dlocation="http://github.com/courgette/b3-plugin-chatlogger/zipball/v1.0" sql="chatlogger.sql"/>
        <plugin name="xlrstats" config="external_dir/conf/xlrstats.xml" sql="xlrstats.sql"/>
        <plugin name="ctime" dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=146" sql="ctime.sql"/>
    </extplugins>
</configuration>