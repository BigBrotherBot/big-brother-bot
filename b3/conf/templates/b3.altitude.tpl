<configuration>
	<settings name="b3">
		<set name="parser">altitude</set>
		<set name="database">mysql://user:pass@localhost/dbname</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">(b3):</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CST</set>
		<set name="log_level">9</set>
		<set name="logfile">@conf/b3.log</set>
	</settings>
	<settings name="server">
		<set name="public_ip"></set>
		<set name="port">27015</set>
        <set name="game_log">C:/Program Files (x86)/Altitude/servers/log.txt</set>
		<set name="command_file">C:/Program Files (x86)/Altitude/servers/command.txt</set>
        <set name="delay">0.05</set>
        <set name="lines_per_second">1000</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
        <set name="destination">b3_doc.htm</set>
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
		<plugin name="admin" config="@conf/plugin_admin.xml" />
	</plugins>
    <extplugins>
    </extplugins>
</configuration>