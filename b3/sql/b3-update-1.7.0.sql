-- SQL code to update default B3 database tables to B3 version 1.7.0 --

-- add ipaliases table --
CREATE TABLE IF NOT EXISTS `ipaliases` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `num_used` int(10) unsigned NOT NULL DEFAULT '0',
  `ip` varchar(32) NOT NULL DEFAULT '',
  `client_id` int(10) unsigned NOT NULL DEFAULT '0',
  `time_add` int(10) unsigned NOT NULL DEFAULT '0',
  `time_edit` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`,`client_id`),
  KEY `client_id` (`client_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;