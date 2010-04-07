-- phpMyAdmin SQL Dump
-- version 2.6.0-pl2
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Apr 20, 2005 at 12:55 PM
-- Server version: 3.23.58
-- PHP Version: 4.3.2
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
) TYPE=MyISAM;

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
  login varchar(16) NOT NULL default '',
  password varchar(32) NOT NULL default '',
  time_add varchar(11) NOT NULL default '',
  time_edit int(11) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY guid (guid),
  KEY group_bits (group_bits),
  KEY name (name)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `groups`
-- 

CREATE TABLE IF NOT EXISTS groups (
  id int(10) unsigned NOT NULL auto_increment,
  name varchar(32) NOT NULL default '',
  keyword varchar(32) NOT NULL default '',
  level int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  time_add int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY keyword (keyword),
  KEY level (level)
) TYPE=MyISAM;

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
  time_add int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  time_expire int(11) NOT NULL default '0',
  PRIMARY KEY  (id),
  KEY keyword (keyword),
  KEY type (type),
  KEY time_expire (time_expire),
  KEY time_add (time_add),
  KEY admin_id (admin_id),
  KEY inactive (inactive),
  KEY client_id (client_id)
) TYPE=MyISAM;
        