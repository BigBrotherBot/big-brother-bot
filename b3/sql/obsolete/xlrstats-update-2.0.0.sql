-- SQL code to update default xlrstats database tables to xlrstats plugin version 2.0.0 --

-- Add assist and assistskill fields to the playerstats table --
ALTER TABLE `xlr_playerstats` ADD `assists`  MEDIUMINT( 8 ) NOT NULL DEFAULT '0' AFTER `skill` ;
ALTER TABLE `xlr_playerstats` ADD `assistskill` FLOAT NOT NULL DEFAULT '0' AFTER `assists` ;
