
CREATE TABLE IF NOT EXISTS aliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  num_used int(10) 	 NOT NULL default '0',
  alias varchar(32) NOT NULL default '',
  client_id INTEGER 	 NOT NULL default '0',
  time_add int(10) 	 NOT NULL default '0',
  time_edit int(10) 	 NOT NULL default '0',
  CONSTRAINT alias UNIQUE (alias,client_id)
);


CREATE TABLE IF NOT EXISTS ipaliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  num_used int(10) 	 NOT NULL default '0',
  ip varchar(16) NOT NULL,
  client_id INTEGER 	 NOT NULL default '0',
  time_add int(10) 	 NOT NULL default '0',
  time_edit int(10) 	 NOT NULL default '0',
  CONSTRAINT ipalias UNIQUE (ip,client_id)
);


CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip varchar(16) NOT NULL default '',
  connections int(11) 	 NOT NULL default '0',
  guid varchar(36) NOT NULL default '',
  pbid varchar(32) NOT NULL default '',
  name varchar(32) NOT NULL default '',
  auto_login tinyint(1) 	 NOT NULL default '0',
  mask_level tinyint(1) 	 NOT NULL default '0',
  group_bits mediumint(8) 	 NOT NULL default '0',
  greeting varchar(128) NOT NULL default '',
  time_add int(11) 	 NOT NULL default '0',
  time_edit int(11) 	 NOT NULL default '0',
  password varchar(32) default NULL,
  login varchar(16) default NULL,
  CONSTRAINT guid UNIQUE (guid)
);


CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY,
  name varchar(32) NOT NULL default '',
  keyword varchar(32) NOT NULL default '',
  level int(10) 	 NOT NULL default '0',
  time_edit int(10) 	 NOT NULL default (strftime('%s','now')),
  time_add int(10) 	 NOT NULL default (strftime('%s','now')),
  CONSTRAINT keyword UNIQUE (keyword)
);


INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (128, 0, 'Super Admin', 'superadmin', 100);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (64, 0, 'Senior Admin', 'senioradmin', 80);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (32, 0, 'Full Admin', 'fulladmin', 60);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (16, 0, 'Admin', 'admin', 40);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (8, 0, 'Moderator', 'mod', 20);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (2, 0, 'Regular', 'reg', 2);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (1, 0, 'User', 'user', 1);
INSERT OR IGNORE INTO `groups` (id, time_edit, name, keyword, level) VALUES (0, 0, 'Guest', 'guest', 0);


CREATE TABLE IF NOT EXISTS penalties (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type varchar(16) NOT NULL default 'Ban' CHECK (type in ('Ban','TempBan','Kick','Warning','Notice', '')),
  client_id INTEGER 	 NOT NULL default '0',
  admin_id INTEGER 	 NOT NULL default '0',
  duration int(10) 	 NOT NULL default '0',
  inactive tinyint(1) 	 NOT NULL default '0',
  keyword varchar(16) NOT NULL default '',
  reason varchar(255) NOT NULL default '',
  data varchar(255) NOT NULL default '',
  time_add int(11) 	 NOT NULL default '0',
  time_edit int(11) 	 NOT NULL default '0',
  time_expire int(11) NOT NULL default '0'
);


CREATE TABLE IF NOT EXISTS `data` (
  `data_key` varchar(255) NOT NULL PRIMARY KEY,
  `data_value` varchar(255) NOT NULL
);



-- --------------------------------------------------------

--
-- Table structure for table `bodyparts`
--

CREATE TABLE IF NOT EXISTS `xlr_bodyparts` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  CONSTRAINT name UNIQUE (`name`)
);

-- --------------------------------------------------------

--
-- Table structure for table `mapstats`
--

CREATE TABLE IF NOT EXISTS `xlr_mapstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  `rounds` smallint(5) NOT NULL default '0',
  CONSTRAINT name UNIQUE (`name`)
);

-- --------------------------------------------------------

--
-- Table structure for table `opponents`
--

CREATE TABLE IF NOT EXISTS `xlr_opponents` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `target_id` smallint(5) NOT NULL default '0',
  `killer_id` smallint(5) NOT NULL default '0',
  `kills` smallint(5) NOT NULL default '0',
  `retals` smallint(5) NOT NULL default '0',
  FOREIGN KEY(`target_id`) REFERENCES clients(`id`),
  FOREIGN KEY(`killer_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `playerbody`
--

CREATE TABLE IF NOT EXISTS `xlr_playerbody` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `bodypart_id` tinyint(3) NOT NULL default '0',
  `player_id` smallint(5) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  FOREIGN KEY(`bodypart_id`) REFERENCES xlr_bodyparts(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `playermaps`
--

CREATE TABLE IF NOT EXISTS `xlr_playermaps` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `map_id` smallint(5) NOT NULL default '0',
  `player_id` smallint(5) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` mediumint(8) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  `rounds` smallint(5) NOT NULL default '0',
  FOREIGN KEY(`map_id`) REFERENCES xlr_mapstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `playerstats`
--

CREATE TABLE IF NOT EXISTS `xlr_playerstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` int(11) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `curstreak` smallint(6) NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) NOT NULL default '0',
  `hide` tinyint(4) NOT NULL default '0',
  `fixed_name` varchar(32) NOT NULL default '',
  `id_token` varchar(10) NOT NULL default '',
  FOREIGN KEY(`client_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `weaponstats`
--

CREATE TABLE IF NOT EXISTS `xlr_weaponstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` varchar(64) NOT NULL default '',
  `kills` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  CONSTRAINT name UNIQUE (`name`)
);

-- --------------------------------------------------------

--
-- Table structure for table `weaponusage`
--

CREATE TABLE IF NOT EXISTS `xlr_weaponusage` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `weapon_id` smallint(5) NOT NULL default '0',
  `player_id` smallint(5) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  FOREIGN KEY(`weapon_id`) REFERENCES xlr_weaponstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `xlr_actionstats`
--

CREATE TABLE IF NOT EXISTS `xlr_actionstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` varchar(25) NOT NULL default '',
  `count` mediumint(8) NOT NULL default '0',
  CONSTRAINT name UNIQUE (`name`)
);

-- --------------------------------------------------------

--
-- Table structure for table `xlr_playeractions`
--

CREATE TABLE IF NOT EXISTS `xlr_playeractions` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `action_id` tinyint(3) NOT NULL default '0',
  `player_id` smallint(5) NOT NULL default '0',
  `count` mediumint(8) NOT NULL default '0',
  FOREIGN KEY(`action_id`) REFERENCES xlr_actionstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

-- --------------------------------------------------------

--
-- Table structure for table `xlr_history_monthly`
--

CREATE TABLE IF NOT EXISTS `xlr_history_monthly` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` int(11) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) NOT NULL default '0',
  `year` int(4) NOT NULL,
  `month` int(2) NOT NULL,
  `week` int(2) NOT NULL,
  `day` int(2) NOT NULL
);

-- --------------------------------------------------------

--
-- Table structure for table `xlr_history_weekly`
--

CREATE TABLE IF NOT EXISTS `xlr_history_weekly` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` int(11) NOT NULL default '0',
  `kills` mediumint(8) NOT NULL default '0',
  `deaths` mediumint(8) NOT NULL default '0',
  `teamkills` smallint(5) NOT NULL default '0',
  `teamdeaths` smallint(5) NOT NULL default '0',
  `suicides` smallint(5) NOT NULL default '0',
  `ratio` float NOT NULL default '0',
  `skill` float NOT NULL default '0',
  `assists` mediumint(8) NOT NULL default '0',
  `assistskill` float NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) NOT NULL default '0',
  `year` int(4) NOT NULL,
  `month` int(2) NOT NULL,
  `week` int(2) NOT NULL,
  `day` int(2) NOT NULL
);

-- --------------------------------------------------------

--
-- Table structure for table `ctime`
--

CREATE TABLE IF NOT EXISTS `ctime` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `guid` varchar(36) NOT NULL,
  `came` varchar(11) default NULL,
  `gone` varchar(11) default NULL,
  `nick` varchar(32) NOT NULL
);