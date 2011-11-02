<configuration>
	<settings name="b3">
		<set name="parser">ro2</set>
		<set name="database">mysql://b3:password@localhost/b3</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">(b3):</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">EST</set>
		<set name="log_level">8</set>
		<set name="logfile">D:\82ndab_b3_current\ro2\logs\b3.log</set>
	</settings>
	<settings name="server">
		<set name="inifile">G:\TCAdmin_Game_Installs\82ndab\Gameservers\RO2_Public\rogame\config\ROgame.ini</set>
		<set name="rcon_password">********</set>
		<set name="ro2admin">Admin</set>
		<set name="port">7757</set>
		<set name="rcon_port">8080</set>
		<set name="public_ip">64.34.182.18</set>
		<set name="delay">0.33</set>
		<set name="lines_per_second">50</set>
		<set name="encoding">latin-1</set>
	</settings>
	<settings name="autodoc">
		<set name="type">html</set>
		<set name="maxlevel">100</set>
		<set name="destination">b3_doc.htm</set>
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
		<set name="external_dir">D:\82ndab_b3_current\ro2\extplugins</set>
	</settings>
	<plugins>
		<plugin name="admin" config="@conf/plugin_admin.xml" />
		<plugin name="censor" config="@conf/plugin_censor.xml" />
		<plugin name="spamcontrol" config="@conf/plugin_spamcontrol.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml" />
		<plugin name="status" config="@conf/plugin_status.xml" />
		<plugin name="welcome" config="@conf/plugin_welcome.xml" />
		<plugin name="login" config="@conf/plugin_login.xml"/>
	</plugins>
</configuration>