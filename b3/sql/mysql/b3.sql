CREATE TABLE IF NOT EXISTS `aliases` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `num_used` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `alias` VARCHAR(32) NOT NULL DEFAULT '',
  `client_id` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_add` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_edit` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (id),
  UNIQUE KEY `alias` (`alias`,`client_id`),
  KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `ipaliases` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `num_used` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `ip` VARCHAR(16) NOT NULL,
  `client_id` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_add` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_edit` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (id),
  UNIQUE KEY `ipalias` (`ip`,`client_id`),
  KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `clients` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `ip` VARCHAR(16) NOT NULL DEFAULT '',
  `connections` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `guid` VARCHAR(36) NOT NULL DEFAULT '',
  `pbid` VARCHAR(32) NOT NULL DEFAULT '',
  `name` VARCHAR(32) NOT NULL DEFAULT '',
  `auto_login` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  `mask_level` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  `group_bits` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `greeting` VARCHAR(128) NOT NULL DEFAULT '',
  `time_add` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `time_edit` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `password` VARCHAR(32) DEFAULT NULL,
  `login` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY `guid` (`guid`),
  KEY `group_bits` (`group_bits`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `cmdgrants` (
   `id` INT(11) NOT NULL,
   `commands` TEXT NOT NULL,
   PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `groups` (
  `id` INT(10) UNSIGNED NOT NULL,
  `name` VARCHAR(32) NOT NULL DEFAULT '',
  `keyword` VARCHAR(32) NOT NULL DEFAULT '',
  `level` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_edit` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `time_add` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `keyword` (`keyword`),
  KEY `level` (`level`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (128, 0, 'Super Admin', 'superadmin', UNIX_TIMESTAMP(), 100);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (64, 0, 'Senior Admin', 'senioradmin', UNIX_TIMESTAMP(), 80);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (32, 0, 'Full Admin', 'fulladmin', UNIX_TIMESTAMP(), 60);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (16, 0, 'Admin', 'admin', UNIX_TIMESTAMP(), 40);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (8, 0, 'Moderator', 'mod', UNIX_TIMESTAMP(), 20);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (2, 0, 'Regular', 'reg', UNIX_TIMESTAMP(), 2);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (1, 0, 'User', 'user', UNIX_TIMESTAMP(), 1);
INSERT INTO `groups` (`id`, `time_edit`, `name`, `keyword`, `time_add`, `level`) VALUES (0, 0, 'Guest', 'guest', UNIX_TIMESTAMP(), 0);

CREATE TABLE IF NOT EXISTS `penalties` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `type` ENUM('Ban','TempBan','Kick','Warning','Notice') NOT NULL DEFAULT 'Ban',
  `client_id` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `admin_id` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `duration` INT(10) UNSIGNED NOT NULL DEFAULT '0',
  `inactive` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  `keyword` VARCHAR(16) NOT NULL DEFAULT '',
  `reason` VARCHAR(255) NOT NULL DEFAULT '',
  `data` VARCHAR(255) NOT NULL DEFAULT '',
  `time_add` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `time_edit` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `time_expire` INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `keyword` (`keyword`),
  KEY `type` (`type`),
  KEY `time_expire` (`time_expire`),
  KEY `time_add` (`time_add`),
  KEY `admin_id` (`admin_id`),
  KEY `inactive` (`inactive`),
  KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `data` (
  `data_key` VARCHAR(255) NOT NULL,
  `data_value` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`data_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_bodyparts` (
  `id` TINYINT(3) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_mapstats` (
  `id` SMALLINT(5) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_opponents` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `target_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `killer_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `kills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `retals` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `target_id` (`target_id`),
  KEY `killer_id` (`killer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_playerbody` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `bodypart_id` TINYINT(3) UNSIGNED NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `bodypart_id` (`bodypart_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_playermaps` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `map_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `map_id` (`map_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_playerstats` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `client_id` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `curstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `hide` TINYINT(4) NOT NULL DEFAULT '0',
  `fixed_name` VARCHAR(32) NOT NULL DEFAULT '',  PRIMARY KEY (`id`),
  `id_token` VARCHAR(10) NOT NULL DEFAULT '',
  UNIQUE KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_weaponstats` (
  `id` SMALLINT(5) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL DEFAULT '',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_weaponusage` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `weapon_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `weapon_id` (`weapon_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_actionstats` (
  `id` TINYINT(3) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(25) NOT NULL DEFAULT '',
  `count` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_playeractions` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `action_id` TINYINT(3) UNSIGNED NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `count` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `action_id` (`action_id`),
  KEY `player_id` (`player_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_history_monthly` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `client_id` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `year` INT(4) NOT NULL,
  `month` INT(2) NOT NULL,
  `week` INT(2) NOT NULL,
  `day` INT(2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `xlr_history_weekly` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `client_id` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) UNSIGNED NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `ratio` FLOAT NOT NULL DEFAULT '0',
  `skill` FLOAT NOT NULL DEFAULT '0',
  `assists` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `assistskill` FLOAT NOT NULL DEFAULT '0',
  `winstreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `losestreak` SMALLINT(6) NOT NULL DEFAULT '0',
  `rounds` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `year` INT(4) NOT NULL,
  `month` INT(2) NOT NULL,
  `week` INT(2) NOT NULL,
  `day` INT(2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `ctime` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `guid` VARCHAR(36) NOT NULL,
  `came` VARCHAR(11) DEFAULT NULL,
  `gone` VARCHAR(11) DEFAULT NULL,
  `nick` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;