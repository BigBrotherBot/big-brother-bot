CREATE TABLE IF NOT EXISTS `aliases` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `num_used` INTEGER(10) NOT NULL DEFAULT '0',
  `alias` VARCHAR(32) NOT NULL DEFAULT '',
  `client_id` INTEGER NOT NULL DEFAULT '0',
  `time_add` INTEGER(10) NOT NULL DEFAULT '0',
  `time_edit` INTEGER(10) NOT NULL DEFAULT '0',
  CONSTRAINT `alias` UNIQUE (`alias`,`client_id`)
);

CREATE TABLE IF NOT EXISTS `ipaliases` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `num_used` INTEGER(10) NOT NULL DEFAULT '0',
  `ip` VARCHAR(16) NOT NULL,
  `client_id` INTEGER NOT NULL DEFAULT '0',
  `time_add` INTEGER(10) NOT NULL DEFAULT '0',
  `time_edit` INTEGER(10) NOT NULL DEFAULT '0',
  CONSTRAINT `ipalias` UNIQUE (`ip`,`client_id`)
);

CREATE TABLE IF NOT EXISTS `clients` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `ip` VARCHAR(16) NOT NULL DEFAULT '',
  `connections` INTEGER(11) NOT NULL DEFAULT '0',
  `guid` VARCHAR(36) NOT NULL DEFAULT '',
  `pbid` VARCHAR(32) NOT NULL DEFAULT '',
  `name` VARCHAR(32) NOT NULL DEFAULT '',
  `auto_login` TINYINT(1) NOT NULL DEFAULT '0',
  `mask_level` TINYINT(1) NOT NULL DEFAULT '0',
  `group_bits` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `greeting` VARCHAR(128) NOT NULL DEFAULT '',
  `time_add` INTEGER(11) NOT NULL DEFAULT '0',
  `time_edit` INTEGER(11) NOT NULL DEFAULT '0',
  `password` VARCHAR(32) DEFAULT NULL,
  `login` VARCHAR(16) DEFAULT NULL,
  CONSTRAINT `guid` UNIQUE (`guid`)
);

CREATE TABLE IF NOT EXISTS `groups` (
  `id` INTEGER PRIMARY KEY,
  `name` VARCHAR(32) NOT NULL DEFAULT '',
  `keyword` VARCHAR(32) NOT NULL DEFAULT '',
  `level` INTEGER(10) NOT NULL DEFAULT '0',
  `time_edit` INTEGER(10) NOT NULL DEFAULT (strftime('%s','now')),
  `time_add` INTEGER(10) NOT NULL DEFAULT (strftime('%s','now')),
  CONSTRAINT `keyword` UNIQUE (`keyword`)
);

INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (128, 0, 'Super Admin', 'superadmin', 100);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (64, 0, 'Senior Admin', 'senioradmin', 80);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (32, 0, 'Full Admin', 'fulladmin', 60);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (16, 0, 'Admin', 'admin', 40);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (8, 0, 'Moderator', 'mod', 20);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (2, 0, 'Regular', 'reg', 2);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (1, 0, 'User', 'user', 1);
INSERT OR IGNORE INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `level`) VALUES (0, 0, 'Guest', 'guest', 0);

CREATE TABLE IF NOT EXISTS `penalties` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` VARCHAR(16) NOT NULL DEFAULT 'Ban' CHECK (`type` in ('Ban','TempBan','Kick','Warning','Notice', '')),
  `client_id` INTEGER NOT NULL DEFAULT '0',
  `admin_id` INTEGER NOT NULL DEFAULT '0',
  `duration` INTEGER(10) NOT NULL DEFAULT '0',
  `inactive` TINYINT(1) NOT NULL DEFAULT '0',
  `keyword` VARCHAR(16) NOT NULL DEFAULT '',
  `reason` VARCHAR(255) NOT NULL DEFAULT '',
  `data` VARCHAR(255) NOT NULL DEFAULT '',
  `time_add` INTEGER(11) NOT NULL DEFAULT '0',
  `time_edit` INTEGER(11) NOT NULL DEFAULT '0',
  `time_expire` INTEGER(11) NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS `data` (
  `data_key` VARCHAR(255) NOT NULL PRIMARY KEY,
  `data_value` VARCHAR(255) NOT NULL
);