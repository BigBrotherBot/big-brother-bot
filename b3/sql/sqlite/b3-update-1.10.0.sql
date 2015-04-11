-- SQL code to update default B3 database tables to B3 version 1.10.0 --
-- --------------------------------------------------------

-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';

-- Better scalability of the xlrstats tables.
-- REMOVED: was already declared as INTEGER (default to INTEGER(11) when not specified)

-- Update time_expire column value for Kick penalties
UPDATE `penalties` SET `time_expire`=-1 WHERE `type` = 'Kick';