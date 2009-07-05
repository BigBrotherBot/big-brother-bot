-- phpMyAdmin SQL Dump
-- version 2.6.2-Debian-3sarge3
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Jan 24, 2007 at 11:52 AM
-- Server version: 4.0.24
-- PHP Version: 4.3.10-18
-- 
-- Database: `b3-uo`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_bodyparts`
-- 

DROP TABLE IF EXISTS `xlr_bodyparts`;
CREATE TABLE IF NOT EXISTS `xlr_bodyparts` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_mapstats`
-- 

DROP TABLE IF EXISTS `xlr_mapstats`;
CREATE TABLE IF NOT EXISTS `xlr_mapstats` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `name` varchar(25) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_opponents`
-- 

DROP TABLE IF EXISTS `xlr_opponents`;
CREATE TABLE IF NOT EXISTS `xlr_opponents` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `target_id` smallint(5) unsigned NOT NULL default '0',
  `killer_id` smallint(5) unsigned NOT NULL default '0',
  `kills` smallint(5) unsigned NOT NULL default '0',
  `retals` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `target_id` (`target_id`),
  KEY `killer_id` (`killer_id`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_playerbody`
-- 

DROP TABLE IF EXISTS `xlr_playerbody`;
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
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_playermaps`
-- 

DROP TABLE IF EXISTS `xlr_playermaps`;
CREATE TABLE IF NOT EXISTS `xlr_playermaps` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `map_id` tinyint(3) unsigned NOT NULL default '0',
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
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_playerstats`
-- 

DROP TABLE IF EXISTS `xlr_playerstats`;
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
  `curstreak` smallint(6) NOT NULL default '0',
  `winstreak` smallint(6) NOT NULL default '0',
  `losestreak` smallint(6) NOT NULL default '0',
  `rounds` smallint(5) unsigned NOT NULL default '0',
  `hide` tinyint(4) NOT NULL default '0',
  `fixed_name` varchar(32) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `client_id` (`client_id`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_weaponstats`
-- 

DROP TABLE IF EXISTS `xlr_weaponstats`;
CREATE TABLE IF NOT EXISTS `xlr_weaponstats` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `name` varchar(32) NOT NULL default '',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `xlr_weaponusage`
-- 

DROP TABLE IF EXISTS `xlr_weaponusage`;
CREATE TABLE IF NOT EXISTS `xlr_weaponusage` (
  `id` mediumint(8) unsigned NOT NULL auto_increment,
  `weapon_id` tinyint(3) unsigned NOT NULL default '0',
  `player_id` smallint(5) unsigned NOT NULL default '0',
  `kills` mediumint(8) unsigned NOT NULL default '0',
  `deaths` mediumint(8) unsigned NOT NULL default '0',
  `teamkills` smallint(5) unsigned NOT NULL default '0',
  `teamdeaths` smallint(5) unsigned NOT NULL default '0',
  `suicides` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `weapon_id` (`weapon_id`),
  KEY `player_id` (`player_id`)
) TYPE=MyISAM;
        
