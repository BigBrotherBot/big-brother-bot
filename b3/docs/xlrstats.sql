-- phpMyAdmin SQL Dump
-- version 2.6.1-rc2
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: May 04, 2005 at 12:10 PM
-- Server version: 4.0.23
-- PHP Version: 4.3.10-12
-- 
-- Database: `b3new`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `bodyparts`
-- 

CREATE TABLE `xlr_bodyparts` (
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
-- Table structure for table `mapstats`
-- 

CREATE TABLE `xlr_mapstats` (
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
-- Table structure for table `opponents`
-- 

CREATE TABLE `xlr_opponents` (
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
-- Table structure for table `playerbody`
-- 

CREATE TABLE `xlr_playerbody` (
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
-- Table structure for table `playermaps`
-- 

CREATE TABLE `xlr_playermaps` (
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
-- Table structure for table `playerstats`
-- 

CREATE TABLE `xlr_playerstats` (
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
-- Table structure for table `weaponstats`
-- 

CREATE TABLE `xlr_weaponstats` (
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
-- Table structure for table `weaponusage`
-- 

CREATE TABLE `xlr_weaponusage` (
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
