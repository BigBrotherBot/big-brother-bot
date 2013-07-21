<configuration>
	<settings name="b3">
		<set name="parser">ro2</set>
		<set name="database">mysql://b3:password@localhost/b3</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">^0(^2b3^0)^7:</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">EST</set>
		<set name="log_level">9</set>
		<set name="logfile">b3.log</set>
	</settings>
	<settings name="server">
		<set name="inifile">\rogame\config\ROgame.ini</set>
		<set name="rcon_password"></set>
		<set name="ro2admin">Admin</set>
		<set name="port">7757</set>
		<set name="rcon_port">8080</set>
		<set name="public_ip">127.0.0.1</set>
		<set name="punkbuster">off</set>
		<set name="delay">0.33</set>
		<set name="lines_per_second">50</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
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
		<plugin name="admin" config="@conf/plugin_admin.ini"/>
		<plugin name="censor" config="@conf/plugin_censor.xml"/>
		<plugin name="spamcontrol" config="@conf/plugin_spamcontrol.xml" />
		<plugin name="pingwatch" config="@conf/plugin_pingwatch.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml" />
		<plugin name="status" config="@conf/plugin_status.xml" />
		<plugin name="welcome" config="@conf/plugin_welcome.xml" />
	</plugins>
</configuration>