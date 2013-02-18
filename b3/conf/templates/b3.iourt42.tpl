<configuration>
	<settings name="b3">
		<set name="parser">iourt42</set>
		<set name="database">mysql://b3:password@localhost/b3</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">^0(^2b3^0)^7:</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CST</set>
		<set name="log_level">9</set>
		<set name="logfile">@conf/b3.log</set>
	</settings>
	<settings name="server">
		<set name="game_log">/home/.q3a/games_mp.log</set>
		<set name="public_ip"></set>
		<set name="port">27960</set>
		<set name="rcon_ip">127.0.0.1</set>
		<set name="rcon_password"></set>
        <!--
        Ban with Frozen Sand auth system
        Set below if you want to send bans to the urbanterror.info website.
        Accepted values are yes/no.

        NOTE: you need to have auth_enable set to 1 in your game server config file and you also need to have the
        auth_owners cvar set correctly.
        -->
        <set name="permban_with_frozensand">no</set>
        <set name="tempban_with_frozensand">no</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
		<set name="destination">@conf/b3_doc.htm</set>
	</settings>
    <settings name="update">
        <!-- B3 checks if a new version is available at startup. Choose here what channel you want to check against.
            Available channels are :
                stable : will only show stable releases of B3
                beta : will also check if a beta release is available
                dev : will also check if a development release is available
            If you don't know what channel to use, use 'stable'
        -->
        <set name="channel">stable</set>
    </settings>
	<settings name="messages">
		<set name="kicked_by">$clientname^7 was kicked by $adminname^7 $reason</set>
		<set name="kicked">$clientname^7 was kicked $reason</set>
		<set name="banned_by">$clientname^7 was banned by $adminname^7 $reason</set>
		<set name="banned">$clientname^7 was banned $reason</set>
		<set name="temp_banned_by">$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason</set>
		<set name="temp_banned">$clientname^7 was temp banned for $banduration^7 $reason</set>
		<set name="unbanned_by">$clientname^7 was un-banned by $adminname^7 $reason</set>
		<set name="unbanned">$clientname^7 was un-banned $reason</set>
	</settings>
	<settings name="plugins">
		<set name="external_dir">@b3/extplugins</set>
	</settings>
	<plugins>
		<plugin name="censor" config="@conf/plugin_censor.xml" />
		<plugin name="spamcontrol" config="@conf/plugin_spamcontrol.xml" />
        <plugin name="admin" config="@conf/plugin_admin.xml" />
		<plugin name="tk" config="@conf/plugin_tk.xml" />
		<plugin name="stats" config="@conf/plugin_stats.xml" />
		<plugin name="pingwatch" config="@conf/plugin_pingwatch.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml" />
		<plugin name="status" config="@conf/plugin_status.xml" />
		<plugin name="welcome" config="@conf/plugin_welcome.xml" />
		<plugin name="punkbuster" config="@conf/plugin_punkbuster.xml" />
	</plugins>
    <extplugins>
        <plugin name="poweradminurt" config="external_dir/conf/poweradminurt.ini"
                dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=1"/>
        <plugin name="chatlogger" config="external_dir/conf/plugin_chatlogger.xml"
                dlocation="http://forum.bigbrotherbot.net/downloads/?sa=downfile&amp;id=7" sql="chatlogger.sql"/>
        <plugin name="xlrstats" config="external_dir/conf/xlrstats.xml"/>
    </extplugins>
</configuration>