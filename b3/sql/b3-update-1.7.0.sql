-- SQL code to update default B3 database tables to B3 version 1.7.0 --

-- add ipaliases table --
CREATE TABLE IF NOT EXISTS ipaliases (
  id int(10) unsigned NOT NULL auto_increment,
  num_used int(10) unsigned NOT NULL default '0',
  ip varchar(16) NOT NULL,
  client_id int(10) unsigned NOT NULL default '0',
  time_add int(10) unsigned NOT NULL default '0',
  time_edit int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (id),
  UNIQUE KEY ipalias (ip,client_id),
  KEY client_id (client_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
