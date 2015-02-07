-- phpMyAdmin SQL Dump
-- version 2.9.1.1-Debian-10
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Jun 27, 2009 at 03:16 PM
-- Server version: 5.0.32
-- PHP Version: 5.2.0-8+etch13
-- 
-- Database: `b3`
-- 

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
  `name` varchar(26) NOT NULL default '',
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
) TYPE=MyISAM DEFAULT CHARSET=utf8;