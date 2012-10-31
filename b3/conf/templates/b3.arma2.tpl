<configuration>
	<settings name="b3">
		<set name="parser">arma2</set>
		<set name="database">mysql://b3:password@localhost/b3</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">(B3):</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CST</set>
		<set name="log_level">9</set>
		<set name="logfile">@conf\b3.log</set>
	</settings>
	<settings name="server">
		<set name="public_ip"></set>
		<set name="port">2302</set>
		<set name="rcon_ip">127.0.0.1</set>
		<set name="rcon_password"></set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
		<set name="destination">@conf\b3_doc.htm</set>
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
		<plugin name="censor" config="@conf/plugin_censor.xml" />
		<plugin name="spamcontrol" config="@conf/plugin_spamcontrol.xml" />
        <plugin name="admin" config="@conf/plugin_admin.xml" />
		<plugin name="stats" config="@conf/plugin_stats.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml" />
		<plugin name="status" config="@conf/plugin_status.xml" />
		<plugin name="welcome" config="@conf/plugin_welcome.xml" />
	</plugins>
    <extplugins>
        <plugin name="arma2admin" config="external_dir/conf/arma2admin.xml"
                dlocation="https://github.com/82ndab-Bravo17/b3-arma2plugins/zipball/master"/>
        <plugin name="arma2lobbykick" config="external_dir/conf/arma2lobbykick.xml"
                dlocation="https://github.com/82ndab-Bravo17/b3-arma2plugins/zipball/master"/>
        <plugin name="arma2restarts" config="external_dir/conf/arma2restarts.xml"
                dlocation="https://github.com/82ndab-Bravo17/b3-arma2plugins/zipball/master"/>
        <plugin name="xlrstats" config="external_dir/conf/xlrstats.xml"/>
    </extplugins>
</configuration>