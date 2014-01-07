-- SQL code to update default B3 database tables to B3 version 1.10.0 --
-- --------------------------------------------------------

-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR( 10 ) NOT NULL DEFAULT '';

-- Better scalability of the xlrstats tables.
ALTER TABLE  `xlr_playerstats` CHANGE  `id`  `id` INT( 11 ) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE  `xlr_history_monthly` CHANGE  `id`  `id` INT( 11 ) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE  `xlr_history_weekly` CHANGE  `id`  `id` INT( 11 ) UNSIGNED NOT NULL AUTO_INCREMENT;

-- fix mask_level in clients table
ALTER TABLE `clients` CHANGE `mask_level` `mask_level` mediumint(8) unsigned NOT NULL DEFAULT '0';