-- SQL code to update default B3 database tables to B3 version 1.10.0 --
-- --------------------------------------------------------

-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';

-- Better scalability of the xlrstats tables.
ALTER TABLE `xlr_playerstats` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE `xlr_history_monthly` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE `xlr_history_weekly` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;

-- Update time_expire column value for Kick penalties
UPDATE `penalties` SET `time_expire`=-1 WHERE `type` = 'Kick';

-- Create Cmdmanager related tables
CREATE TABLE IF NOT EXISTS cmdgrants (
   id int(11) NOT NULL,
   commands TEXT NOT NULL,
   PRIMARY KEY (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;