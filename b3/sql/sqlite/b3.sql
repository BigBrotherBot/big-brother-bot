CREATE TABLE IF NOT EXISTS aliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  num_used INTEGER(10) NOT NULL DEFAULT '0',
  alias VARCHAR(32) NOT NULL DEFAULT '',
  client_id INTEGER NOT NULL DEFAULT '0',
  time_add INTEGER(10) NOT NULL DEFAULT '0',
  time_edit INTEGER(10) NOT NULL DEFAULT '0',
  CONSTRAINT alias UNIQUE (alias,client_id)
);

CREATE TABLE IF NOT EXISTS ipaliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  num_used INTEGER(10) NOT NULL DEFAULT '0',
  ip VARCHAR(16) NOT NULL,
  client_id INTEGER NOT NULL DEFAULT '0',
  time_add INTEGER(10) NOT NULL DEFAULT '0',
  time_edit INTEGER(10) NOT NULL DEFAULT '0',
  CONSTRAINT ipalias UNIQUE (ip,client_id)
);

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip VARCHAR(16) NOT NULL DEFAULT '',
  connections INTEGER(11) NOT NULL DEFAULT '0',
  guid VARCHAR(36) NOT NULL DEFAULT '',
  pbid VARCHAR(32) NOT NULL DEFAULT '',
  name VARCHAR(32) NOT NULL DEFAULT '',
  auto_login TINYINT(1) NOT NULL DEFAULT '0',
  mask_level TINYINT(1) NOT NULL DEFAULT '0',
  group_bits MEDIUMINT(8) NOT NULL DEFAULT '0',
  greeting VARCHAR(128) NOT NULL DEFAULT '',
  time_add INTEGER(11) NOT NULL DEFAULT '0',
  time_edit INTEGER(11) NOT NULL DEFAULT '0',
  password VARCHAR(32) DEFAULT NULL,
  login VARCHAR(16) DEFAULT NULL,
  CONSTRAINT guid UNIQUE (guid)
);

CREATE TABLE IF NOT EXISTS cmdgrants (
  id INTEGER PRIMARY KEY,
  commands TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY,
  name VARCHAR(32) NOT NULL DEFAULT '',
  keyword VARCHAR(32) NOT NULL DEFAULT '',
  level INTEGER(10) NOT NULL DEFAULT '0',
  time_edit INTEGER(10) NOT NULL DEFAULT (strftime('%s','now')),
  time_add INTEGER(10) NOT NULL DEFAULT (strftime('%s','now')),
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
  type VARCHAR(16) NOT NULL DEFAULT 'Ban' CHECK (type in ('Ban','TempBan','Kick','Warning','Notice', '')),
  client_id INTEGER NOT NULL DEFAULT '0',
  admin_id INTEGER NOT NULL DEFAULT '0',
  duration INTEGER(10) NOT NULL DEFAULT '0',
  inactive TINYINT(1) NOT NULL DEFAULT '0',
  keyword VARCHAR(16) NOT NULL DEFAULT '',
  reason VARCHAR(255) NOT NULL DEFAULT '',
  data VARCHAR(255) NOT NULL DEFAULT '',
  time_add INTEGER(11) NOT NULL DEFAULT '0',
  time_edit INTEGER(11) NOT NULL DEFAULT '0',
  time_expire INTEGER(11) NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS `data` (
  `data_key` VARCHAR(255) NOT NULL PRIMARY KEY,
  `data_value` VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS `xlr_bodyparts` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  CONSTRAINT name UNIQUE (`name`)
);

CREATE TABLE IF NOT EXISTS `xlr_mapstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) NOT NULL DEFAULT '0',
  CONSTRAINT name UNIQUE (`name`)
);

CREATE TABLE IF NOT EXISTS `xlr_opponents` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `target_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `killer_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `kills` SMALLINT(5) NOT NULL DEFAULT '0',
  `retals` SMALLINT(5) NOT NULL DEFAULT '0',
  FOREIGN KEY(`target_id`) REFERENCES clients(`id`),
  FOREIGN KEY(`killer_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_playerbody` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `bodypart_id` TINYINT(3) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  FOREIGN KEY(`bodypart_id`) REFERENCES xlr_bodyparts(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_playermaps` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `map_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) NOT NULL DEFAULT '0',
  FOREIGN KEY(`map_id`) REFERENCES xlr_mapstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_playerstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` INTEGER(11) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `curstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) NOT NULL DEFAULT '0',
  `hide` TINYINT(4) NOT NULL DEFAULT '0',
  `fixed_name` VARCHAR(32) NOT NULL DEFAULT '',
  `id_token` VARCHAR(10) NOT NULL DEFAULT '',
  FOREIGN KEY(`client_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_weaponstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(64) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  CONSTRAINT name UNIQUE (`name`)
);

CREATE TABLE IF NOT EXISTS `xlr_weaponusage` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `weapon_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  FOREIGN KEY(`weapon_id`) REFERENCES xlr_weaponstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_actionstats` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `count` MEDIUMINT(8) NOT NULL DEFAULT '0',
  CONSTRAINT name UNIQUE (`name`)
);

CREATE TABLE IF NOT EXISTS `xlr_playeractions` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `action_id` TINYINT(3) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `count` MEDIUMINT(8) NOT NULL DEFAULT '0',
  FOREIGN KEY(`action_id`) REFERENCES xlr_actionstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);

CREATE TABLE IF NOT EXISTS `xlr_history_monthly` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` INTEGER(11) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) NOT NULL DEFAULT '0',
  `year` INTEGER(4) NOT NULL,
  `month` INTEGER(2) NOT NULL,
  `week` INTEGER(2) NOT NULL,
  `day` INTEGER(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS `xlr_history_weekly` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `client_id` INTEGER(11) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) NOT NULL DEFAULT '0',
  `year` INTEGER(4) NOT NULL,
  `month` INTEGER(2) NOT NULL,
  `week` INTEGER(2) NOT NULL,
  `day` INTEGER(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS `ctime` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `guid` VARCHAR(36) NOT NULL,
  `came` VARCHAR(11) DEFAULT NULL,
  `gone` VARCHAR(11) DEFAULT NULL,
  `nick` VARCHAR(32) NOT NULL
);