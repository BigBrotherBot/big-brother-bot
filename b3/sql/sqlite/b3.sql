
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
