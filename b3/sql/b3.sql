-- phpMyAdmin SQL Dump
-- 
-- Database: `b3`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `aliases`
-- 

CREATE TABLE IF NOT EXISTS aliases (
  id int(10) unsigned NOT NULL auto_increment,
  num_used int(10) unsigned NOT NULL default '0',
  alias varchar(32) NOT NULL default '',
  client_id int(10) unsigned NOT NULL default '0',
  time_add int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY alias (alias,client_id),
  KEY client_id (client_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

-- 
-- Table structure for table `ipaliases`
-- 

CREATE TABLE IF NOT EXISTS ipaliases (
  id int(10) unsigned NOT NULL auto_increment,
  num_used int(10) unsigned NOT NULL default '0',
  ip varchar(16) NOT NULL,
  client_id int(10) unsigned NOT NULL default '0',
  time_add int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY ipalias (ip,client_id),
  KEY client_id (client_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

-- 
-- Table structure for table `clients`
-- 

CREATE TABLE IF NOT EXISTS clients (
  id int(11) unsigned NOT NULL auto_increment,
  ip varchar(16) NOT NULL default '',
  connections int(11) unsigned NOT NULL default '0',
  guid varchar(36) NOT NULL default '',
  pbid varchar(32) NOT NULL default '',
  name varchar(32) NOT NULL default '',
  auto_login tinyint(1) unsigned NOT NULL default '0',
  mask_level tinyint(1) unsigned NOT NULL default '0',
  group_bits mediumint(8) unsigned NOT NULL default '0',
  greeting varchar(128) NOT NULL default '',
  time_add int(11) unsigned NOT NULL default '0',
  time_edit int(11) unsigned NOT NULL default '0',
  password varchar(32) default NULL,
  login varchar(255) default NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY guid (guid),
  KEY group_bits (group_bits),
  KEY name (name)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

-- 
-- Table structure for table `groups`
-- 

CREATE TABLE IF NOT EXISTS groups (
  id int(10) unsigned NOT NULL,
  name varchar(32) NOT NULL default '',
  keyword varchar(32) NOT NULL default '',
  level int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  time_add int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY keyword (keyword),
  KEY level (level)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- 
-- Dumping data for table `groups`
-- 

INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (128, 0, 'Super Admin', 'superadmin', UNIX_TIMESTAMP(), 100);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (64, 0, 'Senior Admin', 'senioradmin', UNIX_TIMESTAMP(), 80);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (32, 0, 'Full Admin', 'fulladmin', UNIX_TIMESTAMP(), 60);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (16, 0, 'Admin', 'admin', UNIX_TIMESTAMP(), 40);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (8, 0, 'Moderator', 'mod', UNIX_TIMESTAMP(), 20);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (2, 0, 'Regular', 'reg', UNIX_TIMESTAMP(), 2);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (1, 0, 'User', 'user', UNIX_TIMESTAMP(), 1);
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (0, 0, 'Guest', 'guest', UNIX_TIMESTAMP(), 0);

-- --------------------------------------------------------

-- 
-- Table structure for table `penalties`
-- 

CREATE TABLE IF NOT EXISTS penalties (
  id int(10) unsigned NOT NULL auto_increment,
  type enum('Ban','TempBan','Kick','Warning','Notice') NOT NULL default 'Ban',
  client_id int(10) unsigned NOT NULL default '0',
  admin_id int(10) unsigned NOT NULL default '0',
  duration int(10) unsigned NOT NULL default '0',
  inactive tinyint(1) unsigned NOT NULL default '0',
  keyword varchar(16) NOT NULL default '',
  reason varchar(255) NOT NULL default '',
  data varchar(255) NOT NULL default '',
  time_add int(11) unsigned NOT NULL default '0',
  time_edit int(11) unsigned NOT NULL default '0',
  time_expire int(11) NOT NULL default '0',
  PRIMARY KEY  (id),
  KEY keyword (keyword),
  KEY type (type),
  KEY time_expire (time_expire),
  KEY time_add (time_add),
  KEY admin_id (admin_id),
  KEY inactive (inactive),
  KEY client_id (client_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `data`
--

CREATE TABLE IF NOT EXISTS `data` (
  `data_key` varchar(255) NOT NULL,
  `data_value` varchar(255) NOT NULL,
  PRIMARY KEY  (`data_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bodyparts`
--

CREATE TABLE IF NOT EXISTS `xlr_bodyparts` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `mapstats`
--

CREATE TABLE IF NOT EXISTS `xlr_mapstats` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `opponents`
--

CREATE TABLE IF NOT EXISTS `xlr_opponents` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `target_id` smallint(5) unsigned NOT NULL default '0',
  `killer_id` smallint(5) unsigned NOT NULL default '0',
  `kills` smallint(5) unsigned NOT NULL default '0',
  `retals` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `target_id` (`target_id`),
  KEY `killer_id` (`killer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `playerbody`
--

CREATE TABLE IF NOT EXISTS `xlr_playerbody` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `bodypart_id` tinyint(3) unsigned NOT NULL default '0',
  `player_id` smallint(5) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `bodypart_id` (`bodypart_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `playermaps`
--

CREATE TABLE IF NOT EXISTS `xlr_playermaps` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `map_id` smallint(5) unsigned NOT NULL default '0',
  `player_id` smallint(5) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` mediumint(8) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `map_id` (`map_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `playerstats`
--

CREATE TABLE IF NOT EXISTS `xlr_playerstats` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `client_id` int(11) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `curstreak` smallint(6) NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  `hide` tinyint(4) NOT NULL default '0',
  `fixed_name` varchar(32) NOT NULL default '',  PRIMARY KEY  (`id`),
  UNIQUE KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `weaponstats`
--

CREATE TABLE IF NOT EXISTS `xlr_weaponstats` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `name` varchar(64) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `weaponusage`
--

CREATE TABLE IF NOT EXISTS `xlr_weaponusage` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `weapon_id` smallint(5) unsigned NOT NULL default '0',
  `player_id` smallint(5) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `weapon_id` (`weapon_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `xlr_actionstats`
--

CREATE TABLE IF NOT EXISTS `xlr_actionstats` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `name` varchar(25) NOT NULL default '',
  `count` mediumint(8) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `xlr_playeractions`
--

CREATE TABLE IF NOT EXISTS `xlr_playeractions` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `action_id` tinyint(3) unsigned NOT NULL default '0',
  `player_id` smallint(5) unsigned NOT NULL default '0',
  `count` mediumint(8) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `action_id` (`action_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `xlr_history_monthly`
--

CREATE TABLE IF NOT EXISTS `xlr_history_monthly` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `client_id` int(11) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  `year` int(4) NOT NULL,
  `month` int(2) NOT NULL,
  `week` int(2) NOT NULL,
  `day` int(2) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `xlr_history_weekly`
--

CREATE TABLE IF NOT EXISTS `xlr_history_weekly` (
  `id` smallint(5) unsigned NOT NULL auto_increment,
  `client_id` int(11) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  `year` int(4) NOT NULL,
  `month` int(2) NOT NULL,
  `week` int(2) NOT NULL,
  `day` int(2) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ctime`
--

CREATE TABLE IF NOT EXISTS `ctime` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `guid` varchar(36) NOT NULL,
  `came` varchar(11) default NULL,
  `gone` varchar(11) default NULL,
  `nick` varchar(32) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;