-- SQL code to update default B3 database tables to B3 version 1.9.0 --
-- --------------------------------------------------------

-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR( 10 ) NOT NULL DEFAULT '';