-- SQL code to update default B3 database tables to B3 version 1.9.0 --
-- --------------------------------------------------------

-- Alter the login field of the client table (email can be no longer than 254 characters)
ALTER TABLE `clients` CHANGE `login` `login` VARCHAR(255) NOT NULL DEFAULT '';

-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';