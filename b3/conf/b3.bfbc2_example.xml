<configuration>
	<!--
  This is B3 main config file for BattleField Bad Company 2 !!!
  (the one you specify when you run b3 with the command : b3_run -c b3.xml)

  For any change made in this config file, you have to restart the bot.

  Whenever you can specify a file/directory path, the following shortucts
  can be used :
   @b3 : the folder where B3 code is installed in
   @conf : the folder containing this config file
  -->
	<settings name="b3">
		<!-- parser defines the game: cod/cod2/cod4/cod5/cod6/cod7/iourt41/etpro/wop/smg/bfbc2 -->
		<set name="parser">bfbc2</set>
		<set name="database">mysql://myuser:mypass@mydbhost/mydbname</set>
		<set name="bot_name">b3</set>
		<set name="bot_prefix">^0(^2b3^0)^7:</set>
		<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
		<set name="time_zone">CEST</set>
		<!-- 9 = verbose, 10 = debug, 21 = bot, 22 = console -->
		<set name="log_level">9</set>
		<set name="logfile">b3.log</set>
	</settings>
	<settings name="bfbc2">
		<!-- BFBC2 specific settings
			* max_say_line_length : how long do you want the lines to be restricted to
			in the chat zone. (maximum length is 100)
		-->
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
		<!-- Autodoc will generate a user documentation for all B3 commands 
		 * type : can be one of : html, htmltable, xml
		 * maxlevel : if you want to exclude commands reserved for higher levels
		 * destination : can be a file or a ftp url
		 by default, a html documentation is created in your conf folder
		-->
		<set name="type">html</set>
		<set name="maxlevel">100</set>
		<!-- <set name="destination">C:\Users\b3\Desktop\test_doc.htm</set> -->
		<!-- <set name="destination">ftp://user:pass@somewhere.com/www/test_doc.htm</set> -->
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
		<!-- plugin order is important. Plugins that add new in-game commands all
			depend on the admin plugin. Make sure to have the admin plugin before
			them. -->
		<plugin name="censor" config="@conf/plugin_censor.xml"/>
		<plugin name="spamcontrol" config="@b3/conf/plugin_spamcontrol.xml"/>
		<plugin name="admin" config="@conf/plugin_admin.xml"/>
		<!-- !! not tested with BFBC2 !!  <plugin name="tk" config="@conf/plugin_tk.xml"/> -->
		<!-- !! not tested with BFBC2 !!  <plugin name="stats" config="@conf/plugin_stats.xml"/> -->
		<plugin name="pingwatch" config="@conf/plugin_pingwatch.xml" />
		<plugin name="adv" config="@conf/plugin_adv.xml"/>
		<plugin name="status" config="@conf/plugin_status.xml"/>
		<plugin name="welcome" config="@conf/plugin_welcome.xml"/>


		<!-- 
			This is a non-standard plugin, and quite resource heavy. Please take a look in the 
			B3 forums (look for XLR Extensions) for more information before enabling this.
			Extra database tables are necessary.
		<plugin name="xlrstats" config="@b3/extplugins/conf/xlrstats.xml"/>
		-->
	</plugins>
</configuration>